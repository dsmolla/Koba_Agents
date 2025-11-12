import os
import logging
import time

import telegramify_markdown
from langchain_core.messages import HumanMessage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

from telegram_interface.config import Config
from telegram_interface.messages import *
from telegram_interface.session_manager import SessionManager

logger = logging.getLogger(__name__)


async def format_markdown_for_telegram(text: str) -> str:
    formatted_text = await telegramify_markdown.telegramify(text)
    if len(formatted_text) > 0:
        return formatted_text[0].content
    return ""


class GoogleAgentBot:
    def __init__(self, auth_redirect_uri: str):
        logger.info("Initializing GoogleAgentBot", extra={'auth_redirect_uri': auth_redirect_uri})
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self.session_manager = SessionManager(auth_redirect_uri)
        self.auth_flows = {}
        logger.info("GoogleAgentBot initialized successfully")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        username = update.effective_user.username
        user_name = update.effective_user.first_name or 'there'
        logger.info("/start command received", extra={
            'user_id': telegram_id,
            'username': username,
            'user_name': user_name
        })
        await update.message.reply_markdown_v2(
            await format_markdown_for_telegram(WELCOME_MESSAGE.format(name=user_name)))

    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        username = update.effective_user.username
        logger.info("/login command received", extra={'user_id': telegram_id, 'username': username})

        if self.session_manager.is_user_authenticated(telegram_id):
            logger.info("User already authenticated", extra={'user_id': telegram_id})
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(ALREADY_AUTHENTICATED_MESSAGE))
            return

        try:
            state = os.urandom(16).hex()
            self.session_manager.store_auth_flow(state, telegram_id)
            auth_url = self.session_manager.auth_manager.generate_auth_url(Config.OAUTH_SCOPES, state)
            logger.info("OAuth flow initiated", extra={
                'user_id': telegram_id,
                'scopes': Config.OAUTH_SCOPES
            })
            await update.message.reply_markdown_v2(
                await format_markdown_for_telegram(LOGIN_MESSAGE.format(link=auth_url)))
        except Exception as e:
            logger.error("OAuth flow initiation failed", extra={
                'user_id': telegram_id,
                'error': str(e)
            }, exc_info=True)
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(AUTH_FLOW_ERROR_MESSAGE))

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        is_authenticated = self.session_manager.is_user_authenticated(telegram_id)
        logger.info("/status command received", extra={
            'user_id': telegram_id,
            'is_authenticated': is_authenticated
        })
        if is_authenticated:
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(STATUS_AUTHENTICATED_MESSAGE))
        else:
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(STATUS_NOT_AUTHENTICATED_MESSAGE))

    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        logger.info("/logout command received", extra={'user_id': telegram_id})
        self.session_manager.user_tokens_db.delete_token(telegram_id)
        self.session_manager.clear_session(telegram_id)
        logger.info("User logged out successfully", extra={'user_id': telegram_id})
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(LOGGED_OUT_MESSAGE))

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        logger.info("/clear command received", extra={'user_id': telegram_id})
        self.session_manager.clear_session(telegram_id)
        logger.info("User session cleared", extra={'user_id': telegram_id})
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(CLEARED_HISTORY_MESSAGE))

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        logger.info("/help command received", extra={'user_id': telegram_id})
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(HELP_MESSAGE))

    async def timezone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        logger.info("/timezone command received", extra={'user_id': telegram_id})

        if not self.session_manager.is_user_authenticated(telegram_id):
            logger.warning("Timezone command from unauthenticated user", extra={'user_id': telegram_id})
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(TIMEZONE_NOT_AUTHENTICATED_MESSAGE))
            return

        current_tz = self.session_manager.user_tokens_db.get_timezone(telegram_id)
        if not current_tz:
            current_tz = "Not set"
        logger.debug("Current timezone retrieved", extra={'user_id': telegram_id, 'current_timezone': current_tz})

        # Define common timezones with inline keyboard
        keyboard = [
            [InlineKeyboardButton("🇺🇸 America/New_York (EST/EDT)", callback_data="America/New_York")],
            [InlineKeyboardButton("🇺🇸 America/Chicago (CST/CDT)", callback_data="America/Chicago")],
            [InlineKeyboardButton("🇺🇸 America/Denver (MST/MDT)", callback_data="America/Denver")],
            [InlineKeyboardButton("🇺🇸 America/Los_Angeles (PST/PDT)", callback_data="America/Los_Angeles")],
            [InlineKeyboardButton("🇬🇧 Europe/London (GMT/BST)", callback_data="Europe/London")],
            [InlineKeyboardButton("🇫🇷 Europe/Paris (CET/CEST)", callback_data="Europe/Paris")],
            [InlineKeyboardButton("🇩🇪 Europe/Berlin (CET/CEST)", callback_data="Europe/Berlin")],
            [InlineKeyboardButton("🇯🇵 Asia/Tokyo (JST)", callback_data="Asia/Tokyo")],
            [InlineKeyboardButton("🇨🇳 Asia/Shanghai (CST)", callback_data="Asia/Shanghai")],
            [InlineKeyboardButton("🇮🇳 Asia/Kolkata (IST)", callback_data="Asia/Kolkata")],
            [InlineKeyboardButton("🇦🇺 Australia/Sydney (AEDT/AEST)", callback_data="Australia/Sydney")],
            [InlineKeyboardButton("🌍 UTC", callback_data="UTC")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_markdown_v2(
            await format_markdown_for_telegram(TIMEZONE_PROMPT_MESSAGE.format(current_timezone=current_tz)),
            reply_markup=reply_markup
        )

    async def handle_timezone_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        telegram_id = update.effective_user.id
        timezone = query.data
        logger.info("Timezone selection received", extra={'user_id': telegram_id, 'timezone': timezone})

        try:
            self.session_manager.user_tokens_db.update_timezone(telegram_id, timezone)
            logger.info("Timezone updated successfully", extra={'user_id': telegram_id, 'timezone': timezone})
            await query.edit_message_text(
                await format_markdown_for_telegram(TIMEZONE_UPDATED_MESSAGE.format(timezone=timezone)),
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            logger.error("Failed to update timezone", extra={
                'user_id': telegram_id,
                'timezone': timezone,
                'error': str(e)
            }, exc_info=True)
            await query.edit_message_text(
                await format_markdown_for_telegram(TIMEZONE_ERROR_MESSAGE),
                parse_mode='MarkdownV2'
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        username = update.effective_user.username
        user_message = update.message.text
        start_time = time.time()

        logger.info("User message received", extra={
            'user_id': telegram_id,
            'username': username,
            'message_length': len(user_message),
            'message_preview': user_message[:100]  # First 100 chars
        })

        session = self.session_manager.get_session(telegram_id)

        if session.agent is None:
            logger.warning("Message from unauthenticated user", extra={'user_id': telegram_id})
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(NOT_LOGGED_IN_MESSAGE))
            return

        session.add_messages([HumanMessage(content=user_message)])
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        try:
            logger.debug("Sending message to agent", extra={'user_id': telegram_id})
            response = await session.agent.aexecute(session.messages)
            session.add_messages(response.messages)

            processing_time = time.time() - start_time
            response_text = response.messages[-1].content

            logger.info("Agent response generated successfully", extra={
                'user_id': telegram_id,
                'processing_time': f"{processing_time:.2f}s",
                'response_length': len(response_text),
                'response_preview': response_text[:100]  # First 100 chars
            })

            await update.message.reply_markdown_v2(await format_markdown_for_telegram(response_text))
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error("Error processing user message", extra={
                'user_id': telegram_id,
                'processing_time': f"{processing_time:.2f}s",
                'error': str(e),
                'message_preview': user_message[:100]
            }, exc_info=True)
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(ERROR_PROCESSING_MESSAGE))

    @staticmethod
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        telegram_id = update.effective_user.id if update.effective_user else None
        error = context.error
        logger.error("Telegram bot error occurred", extra={
            'user_id': telegram_id,
            'error_type': type(error).__name__,
            'error': str(error)
        }, exc_info=error)
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(ERROR_PROCESSING_MESSAGE))

    async def _cleanup_sessions(self, context: ContextTypes.DEFAULT_TYPE):
        logger.debug("Running session cleanup task")
        cleaned_count = self.session_manager.cleanup_expired_sessions()
        logger.info("Session cleanup completed", extra={'sessions_cleaned': cleaned_count})

    async def send_message(self, telegram_id: int, message: str):
        logger.info("Sending message to user", extra={
            'user_id': telegram_id,
            'message_length': len(message)
        })
        await self.application.bot.send_message(chat_id=telegram_id, text=message)

    def run(self):
        logger.info("Registering bot handlers")
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("login", self.login))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("logout", self.logout))
        self.application.add_handler(CommandHandler("clear", self.clear))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("timezone", self.timezone))
        self.application.add_handler(CallbackQueryHandler(self.handle_timezone_selection, pattern="^"))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        self.application.add_error_handler(self.error_handler)

        logger.info("Scheduling session cleanup job (every 300 seconds)")
        self.application.job_queue.run_repeating(self._cleanup_sessions, interval=300, first=300)

        logger.info("Starting bot polling")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
