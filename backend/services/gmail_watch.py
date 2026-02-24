import asyncio
import logging

from google_client.services.gmail import AsyncGmailApiService

from config import Config
from core.auth import get_google_service
from core.db import database
from core.exceptions import ProviderNotConnectedError

logger = logging.getLogger(__name__)


async def get_user_email(gmail_service) -> str:
    """Fetch the authenticated user's Gmail address."""
    loop = asyncio.get_running_loop()
    profile = await loop.run_in_executor(
        None,
        lambda: gmail_service._service().users().getProfile(userId='me').execute()
    )
    return profile['emailAddress']


async def start_watch(user_id: str):
    """Start a Gmail Pub/Sub watch for a user. Upserts gmail_watch_state."""
    if not Config.PUBSUB_TOPIC:
        logger.warning("PUBSUB_TOPIC not configured, skipping watch start", extra={"user_id": user_id})
        return

    user_tz = await database.get_user_timezone(user_id)
    api_service = await get_google_service(user_id, user_tz)
    gmail = api_service.async_gmail

    result = await gmail.watch(
        topic_name=Config.PUBSUB_TOPIC,
        label_ids=["INBOX"],
        label_filter_action="include"
    )

    email = (await get_user_email(gmail)).lower()  # Store lowercase for consistent index lookups

    history_id = int(result["historyId"])
    expiration = int(result["expiration"])

    await database.execute(
        """
        INSERT INTO public.gmail_watch_state (user_id, email, history_id, watch_expiration, is_active)
        VALUES (%s, %s, %s, to_timestamp(%s / 1000.0), TRUE)
        ON CONFLICT (user_id) DO UPDATE SET
            email = EXCLUDED.email,
            history_id = EXCLUDED.history_id,
            watch_expiration = EXCLUDED.watch_expiration,
            is_active = TRUE,
            updated_at = NOW()
        """,
        (user_id, email, history_id, expiration)
    )

    logger.info("Gmail watch started", extra={"user_id": user_id, "email": email})


async def stop_watch(user_id: str):
    """Stop the Gmail Pub/Sub watch for a user and remove watch state."""
    try:
        user_tz = await database.get_user_timezone(user_id)
        api_service = await get_google_service(user_id, user_tz)
        gmail = api_service.async_gmail
        await gmail.stop_watch()
    except (ProviderNotConnectedError, Exception) as e:
        logger.warning(f"Could not stop Gmail watch: {e}", extra={"user_id": user_id})

    await database.execute(
        "UPDATE public.gmail_watch_state SET is_active = FALSE, updated_at = NOW() WHERE user_id = %s",
        (user_id,)
    )
    logger.info("Gmail watch stopped", extra={"user_id": user_id})


async def renew_all_watches():
    """Renew Gmail watches for all users with active watch state. Called by APScheduler."""
    rows = await database.fetch_all("SELECT user_id FROM public.gmail_watch_state WHERE is_active = TRUE")
    if not rows:
        return

    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent renewals to avoid Gmail API rate limits

    async def renew_one(user_id: str):
        async with semaphore:
            try:
                # Check if user still has enabled rules
                rule_count = await database.fetch_one(
                    "SELECT COUNT(*) as cnt FROM public.auto_reply_rules WHERE user_id = %s AND is_enabled = TRUE",
                    (user_id,)
                )
                if rule_count['cnt'] == 0:
                    await stop_watch(user_id)
                    return

                user_tz = await database.get_user_timezone(user_id)
                api_service = await get_google_service(user_id, user_tz)
                gmail = api_service.async_gmail

                result = await gmail.watch(
                    topic_name=Config.PUBSUB_TOPIC,
                    label_ids=["INBOX"],
                    label_filter_action="include"
                )

                expiration = int(result["expiration"])
                await database.execute(
                    """
                    UPDATE public.gmail_watch_state
                    SET watch_expiration = to_timestamp(%s / 1000.0), updated_at = NOW()
                    WHERE user_id = %s
                    """,
                    (expiration, user_id)
                )
                logger.info("Gmail watch renewed", extra={"user_id": user_id})

            except ProviderNotConnectedError:
                logger.warning("Skipping watch renewal: Google not connected", extra={"user_id": user_id})
            except Exception as e:
                logger.error(f"Failed to renew watch: {e}", extra={"user_id": user_id})

    await asyncio.gather(*[renew_one(row['user_id']) for row in rows], return_exceptions=True)


async def get_history_changes(gmail_service: AsyncGmailApiService, start_history_id: int) -> list[str]:
    """Fetch new INBOX message IDs since start_history_id using Gmail History API.

    Returns:
        Tuple of (new_message_ids, latest_history_id)
    """
    IGNORE_LABELS = {'SPAM', 'CATEGORY_PROMOTIONS', 'TRASH'}
    page_token = None
    message_ids = set()
    loop = asyncio.get_running_loop()
    while True:
        history_response = await loop.run_in_executor(
            None,
            lambda: gmail_service._service().users().history().list(
                userId='me',
                startHistoryId=str(start_history_id),
                historyTypes=['messageAdded'],
                labelId='INBOX',
                pageToken=page_token
            ).execute()
        )

        for record in history_response.get('history', []):
            for message_data in record.get('messagesAdded', []):
                message = message_data['message']
                message_id = message['id']
                message_labels = set(message.get('labelIds', []))
                if not IGNORE_LABELS.intersection(message_labels):
                    message_ids.add(message_id)

        page_token = history_response.get('nextPageToken', None)
        if not page_token:
            break

    return list(message_ids)
