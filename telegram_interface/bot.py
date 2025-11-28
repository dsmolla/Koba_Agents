import asyncio
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import telegramify_markdown
from langchain_core.messages import HumanMessage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram._files.audio import Audio
from telegram._files.document import Document
from telegram._files.photosize import PhotoSize
from telegram._files.video import Video
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


@dataclass
class MessageData:
    documents: list[Document | PhotoSize | Video | Audio] = field(default_factory=list)
    text: Optional[str] = None
    update: Optional[Update] = None


class GoogleAgentBot:
    def __init__(self, auth_redirect_uri: str):
        logger.info("Initializing GoogleAgentBot", extra={'auth_redirect_uri': auth_redirect_uri})
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).concurrent_updates(True).build()
        self.session_manager = SessionManager(auth_redirect_uri)
        self.auth_flows = {}

        self.pending_messages: dict[int, MessageData] = defaultdict(lambda: MessageData())
        self.timers: dict[int, asyncio.Task] = {}

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

        if await self.session_manager.is_user_authenticated(telegram_id):
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
        is_authenticated = await self.session_manager.is_user_authenticated(telegram_id)
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
        await self.session_manager.user_tokens_db.delete_token(telegram_id)
        self.session_manager.clear_session(telegram_id)
        logger.info("User logged out successfully", extra={'user_id': telegram_id})
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(LOGGED_OUT_MESSAGE))

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        logger.info("/clear command received", extra={'user_id': telegram_id})
        self.session_manager.clear_session(telegram_id)
        logger.info("User session cleared", extra={'user_id': telegram_id})
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(CLEARED_HISTORY_MESSAGE))

    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        logger.info("/help command received", extra={'user_id': telegram_id})
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(HELP_MESSAGE))

    async def timezone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        logger.info("/timezone command received", extra={'user_id': telegram_id})

        if not await self.session_manager.is_user_authenticated(telegram_id):
            logger.warning("Timezone command from unauthenticated user", extra={'user_id': telegram_id})
            await update.message.reply_markdown_v2(
                await format_markdown_for_telegram(TIMEZONE_NOT_AUTHENTICATED_MESSAGE))
            return

        current_tz = await self.session_manager.user_tokens_db.get_timezone(telegram_id)
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
            await self.session_manager.user_tokens_db.update_timezone(telegram_id, timezone)
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

    async def _process_group_after_timeout(self, telegram_id: int):
        await asyncio.sleep(1.5)

        if telegram_id in self.pending_messages:
            message_data = self.pending_messages[telegram_id]
            await self.execute_message(message_data)

            del self.pending_messages[telegram_id]
            if telegram_id in self.timers:
                del self.timers[telegram_id]

    @staticmethod
    async def download_files(documents: list[Document]) -> list[Path]:
        download_folder = Path(Config.USER_FILES_DIR)
        downloaded_files = []
        for document in documents:
            try:
                file = await document.get_file()
                try:
                    file_name = document.file_name
                except AttributeError:
                    file_name = document.file_unique_id
                    extension = file.file_path.split('.')[-1]
                    file_name = f"{file_name}.{extension}"
                path = await file.download_to_drive(download_folder / file_name)
                downloaded_files.append(path)
            except Exception:
                logger.error(f"Error downloading file: {document}",
                             extra={'file_id': document.file_id},
                             exc_info=True
                             )
        return downloaded_files

    async def execute_message(self, message_data: MessageData):
        start_time = time.time()
        telegram_id = message_data.update.effective_user.id
        update = message_data.update
        text = message_data.text or ""

        logger.info("User message received", extra={
            'user_id': telegram_id,
            'message_length': len(text),
            'message_preview': text[:100],
            'files': [document.file_unique_id for document in message_data.documents]
        })

        session = await self.session_manager.get_session(telegram_id)

        if session.agent is None:
            logger.info("Message from unauthenticated user", extra={'user_id': telegram_id})
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(NOT_LOGGED_IN_MESSAGE))
            return

        paths = []
        if message_data.documents:
            paths = await self.download_files(message_data.documents)
            text += "\nFile Paths: "
            text += ', '.join([str(path) for path in paths])

        async def typing_action():
            while True:
                await update.message.reply_chat_action(ChatAction.TYPING)
                await asyncio.sleep(4)

        typing_task = asyncio.create_task(typing_action())

        try:
            human_message = HumanMessage(content=text)
            session.add_message(human_message)
            response = await session.agent.aexecute([human_message])
            session.add_message(response.messages[-1])

            processing_time = time.time() - start_time
            response_text = response.messages[-1].content

            logger.info("Agent response generated successfully", extra={
                'user_id': telegram_id,
                'processing_time': f"{processing_time:.2f}s",
                'response_length': len(response_text),
                'response_preview': response_text[:100]
            })

            await update.message.reply_markdown_v2(await format_markdown_for_telegram(response_text))
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error("Error processing user message", extra={
                'user_id': telegram_id,
                'processing_time': f"{processing_time:.2f}s",
                'error': str(e),
                'message_preview': text[:100]
            }, exc_info=True)
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(ERROR_PROCESSING_MESSAGE))
        finally:
            typing_task.cancel()
            # Clean up downloaded files
            for path in paths:
                try:
                    if path.exists():
                        path.unlink()
                        logger.debug("File deleted successfully", extra={
                            'user_id': telegram_id,
                            'file_path': str(path)
                        })
                except Exception as e:
                    logger.warning("Failed to delete file", extra={
                        'user_id': telegram_id,
                        'file_path': str(path),
                        'error': str(e)
                    })

    async def handle_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        telegram_id = update.effective_user.id

        message_data = self.pending_messages[telegram_id]

        if message_data.update is None:
            message_data.update = update

        if message.document:
            message_data.documents.append(message.document)

        if message.photo:
            message_data.documents.append(message.photo[-1])

        if message.video:
            message_data.documents.append(message.video)

        if message.audio:
            message_data.documents.append(message.audio)

        if message.caption and message_data.text is None:
            message_data.text = message.caption

        if telegram_id in self.timers:
            self.timers[telegram_id].cancel()

        self.pending_messages[telegram_id] = message_data
        self.timers[telegram_id] = asyncio.create_task(self._process_group_after_timeout(telegram_id))

    async def handle_text_only(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        message_data = self.pending_messages[telegram_id]
        message_data.text = update.message.text
        message_data.update = update

        if telegram_id in self.timers:
            self.timers[telegram_id].cancel()

        self.pending_messages[telegram_id] = message_data
        self.timers[telegram_id] = asyncio.create_task(self._process_group_after_timeout(telegram_id))

    async def save_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        telegram_id = update.effective_user.id
        await self.session_manager.save_session_to_disk(telegram_id)
        logger.info("User session saved", extra={'user_id': telegram_id})

    async def load_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        await self.session_manager.load_session_from_disk(telegram_id)
        logger.info("User session loaded", extra={'user_id': telegram_id})

    @staticmethod
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        telegram_id = update.effective_user.id if update.effective_user else None
        error = context.error
        logger.error("Telegram bot error occurred", extra={
            'user_id': telegram_id,
            'error_type': type(error).__name__,
            'error': str(error)
        }, exc_info=error)
        if update and update.message:
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
        self.application.add_handler(CommandHandler("save", self.save_session))
        self.application.add_handler(CommandHandler("load", self.load_session))
        self.application.add_handler(CallbackQueryHandler(self.handle_timezone_selection, pattern="^"))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_only))
        self.application.add_handler(
            MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO, self.handle_files))

        self.application.add_error_handler(self.error_handler)

        logger.info("Scheduling session cleanup job (every 300 seconds)")
        self.application.job_queue.run_repeating(self._cleanup_sessions, interval=300, first=300)

        logger.info("Starting bot polling")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
