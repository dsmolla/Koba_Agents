import asyncio
import logging

from google.auth.exceptions import RefreshError
from google_client.services.gmail import AsyncGmailApiService
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.gmail.auto_reply.agent import GmailAutoReplyAgent
from config import Config
from core.auth import get_google_service
from core.db import database
from core.exceptions import ProviderNotConnectedError
from core.redis_client import redis_client
from services.gmail_watch import get_history_changes, stop_watch

logger = logging.getLogger(__name__)

SKIP_SENDERS = ['noreply', 'no-reply', 'donotreply', 'do-not-reply', 'mailer-daemon', 'postmaster']
SKIP_LABELS = {'SENT', 'DRAFT', 'SPAM', 'TRASH', 'CATEGORY_PROMOTIONS'}


async def should_skip_email(gmail_service: AsyncGmailApiService, message_id: str) -> tuple[bool, str | None]:
    """Return (True, None) if this email should NOT get an auto-reply, else (False, subject)."""
    email = await gmail_service.get_email(message_id)
    subject = getattr(email, 'subject', None)

    if email.is_from('me'):
        logger.debug("Skipping: sent by self", extra={"message_id": message_id})
        return True, None
    if matched := SKIP_LABELS.intersection(set(email.labels)):
        logger.debug(f"Skipping: label {matched}", extra={"message_id": message_id})
        return True, None
    if email.sender:
        sender_lower = email.sender.email.lower()
        if any(skip in sender_lower for skip in SKIP_SENDERS):
            logger.debug("Skipping: noreply sender", extra={"message_id": message_id})
            return True, None

    # Check auto-generated email headers
    loop = asyncio.get_event_loop()

    try:
        raw_msg = await loop.run_in_executor(
            gmail_service._executor,
            lambda: gmail_service._service().users().messages().get(
                userId='me', id=message_id, format='metadata',
                metadataHeaders=['Auto-Submitted', 'X-Autoreply', 'X-Auto-Response-Suppress', 'Precedence']
            ).execute()
        )
    except Exception as e:
        logger.warning(f"Failed to fetch email headers for {message_id}: {e}",
                       extra={"message_id": message_id})
        return False, subject

    headers = {h['name'].lower(): h['value'].lower() for h in raw_msg.get('payload', {}).get('headers', [])}

    if headers.get('auto-submitted', '') not in ('', 'no'):
        logger.debug("Skipping: Auto-Submitted header", extra={"message_id": message_id})
        return True, None
    if 'x-autoreply' in headers:
        logger.debug("Skipping: X-Autoreply header", extra={"message_id": message_id})
        return True, None
    if 'x-auto-response-suppress' in headers:
        logger.debug("Skipping: X-Auto-Response-Suppress header", extra={"message_id": message_id})
        return True, None
    if headers.get('precedence', '') in ('bulk', 'junk', 'list'):
        logger.debug("Skipping: bulk/list precedence header", extra={"message_id": message_id})
        return True, None

    return False, subject


async def check_rate_limit(user_id: str) -> bool:
    """Return True if user is within their auto-reply rate limit."""
    is_allowed, _ = await redis_client.check_rate_limit(
        f"auto_reply:{user_id}",
        Config.AUTO_REPLY_HOURLY_LIMIT,
        3600
    )
    return is_allowed


async def log_auto_reply(user_id, message_id, reply_message_id=None, status='sent', error_message=None, llm_model=None, subject=None):
    """Log an auto-reply attempt. rule_id is optional (agent decides, not programmatic matching)."""
    try:
        await database.execute(
            """
            INSERT INTO public.auto_reply_log
                (user_id, message_id, reply_message_id, status, error_message, llm_model, subject)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, message_id) DO NOTHING
            """,
            (user_id, message_id, reply_message_id, status, error_message, llm_model, subject)
        )
        return True
    except Exception as e:
        logger.error(f"Failed to log auto-reply: {e}", extra={"user_id": user_id})
        return False


async def process_notification(user_id: str, notification_history_id: int):
    try:
        watch_state = await database.fetch_one(
            "SELECT history_id FROM public.gmail_watch_state WHERE user_id = %s",
            (user_id,)
        )
        if not watch_state:
            await stop_watch(user_id)
            return

        stored_history_id = watch_state['history_id']

        if notification_history_id <= stored_history_id:
            return

        rules = await database.fetch_all(
            "SELECT * FROM public.auto_reply_rules WHERE user_id = %s AND is_enabled = TRUE ORDER BY sort_order ASC",
            (user_id,)
        )
        if not rules:
            return

        user_tz = await database.get_user_timezone(user_id)
        api_service = await get_google_service(user_id, user_tz)
        gmail_service = api_service.async_gmail

        new_message_ids = await get_history_changes(gmail_service, stored_history_id)

        llm = ChatGoogleGenerativeAI(model=Config.DEFAULT_MODEL)
        auto_reply_agent = GmailAutoReplyAgent(llm, rules)

        for message_id in new_message_ids:
            if not await check_rate_limit(user_id):
                break

            already_processed = await database.fetch_one(
                "SELECT id FROM public.auto_reply_log WHERE user_id = %s AND message_id = %s",
                (user_id, message_id)
            )
            if already_processed:
                continue
            should_skip, subject = await should_skip_email(api_service.async_gmail, message_id)
            if should_skip:
                continue

            config = RunnableConfig(
                configurable={
                    "thread_id": f"gmail_auto_reply_{user_id}_{message_id}",
                    "timezone": user_tz,
                    "api_service": api_service,
                },
            )

            try:
                response = await auto_reply_agent.arun(message_id, config)
                result = response.content.strip()

                if result.upper() == "IGNORE":
                    continue

                await log_auto_reply(
                    user_id, message_id,
                    reply_message_id=result,
                    status='sent', llm_model=Config.DEFAULT_MODEL, subject=subject
                )
                logger.info(f"Auto-reply agent acted on {message_id}", extra={"user_id": user_id})

            except Exception as e:
                logger.error(f"Auto-reply agent failed for {message_id}: {e}", extra={"user_id": user_id})
                await log_auto_reply(
                    user_id, message_id,
                    status='failed', error_message=str(e)[:500],
                    llm_model=Config.DEFAULT_MODEL, subject=subject
                )

        await database.execute(
            "UPDATE public.gmail_watch_state SET history_id = %s, updated_at = NOW() WHERE user_id = %s",
            (notification_history_id, user_id)
        )

    except (ProviderNotConnectedError, RefreshError) as e:
        logger.warning(f"Auth error during auto-reply processing: {e}", extra={"user_id": user_id})
    except Exception as e:
        logger.error(f"Error processing notification: {e}", extra={"user_id": user_id}, exc_info=True)
