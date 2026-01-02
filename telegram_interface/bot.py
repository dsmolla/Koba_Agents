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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument
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
from telegram.request import HTTPXRequest
from telegram.error import TimedOut, NetworkError

from config import Config
from telegram_interface.messages import *
from telegram_interface.session_manager import SessionManager
from telegram_interface.auth_instance import auth_manager
from telegram_interface.security import RateLimiter, FileSecurityValidator, FileCleanupManager
from agents.common.exceptions import AgentException, ToolException

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

        # Create custom request handler with configured timeouts
        request = HTTPXRequest(
            connection_pool_size=Config.TELEGRAM_POOL_SIZE,
            connect_timeout=Config.TELEGRAM_CONNECT_TIMEOUT,
            read_timeout=Config.TELEGRAM_READ_TIMEOUT,
            write_timeout=Config.TELEGRAM_WRITE_TIMEOUT,
            media_write_timeout=Config.TELEGRAM_MEDIA_WRITE_TIMEOUT
        )

        self.application = Application.builder() \
            .token(Config.TELEGRAM_BOT_TOKEN) \
            .concurrent_updates(True) \
            .request(request) \
            .post_init(self.post_init) \
            .build()

        # Use shared auth_manager instance
        self.auth_manager = auth_manager
        self.session_manager = SessionManager(auth_manager)
        self.auth_flows = {}

        self.pending_messages: dict[int, MessageData] = defaultdict(lambda: MessageData())
        self.timers: dict[int, asyncio.Task] = {}
        self._pending_message_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

        # Security components
        self.rate_limiter = RateLimiter()
        self.file_validator = FileSecurityValidator()

        logger.info("GoogleAgentBot initialized successfully")

    async def post_init(self, application: Application):
        """Initialize async components within the bot's event loop."""
        logger.info("Running post_init initialization")

        # Initialize database tables
        logger.info("Initializing database tables")
        await self.auth_manager.user_tokens_db._create_tables()
        
        # Initialize session manager (checkpointer)
        logger.info("Initializing checkpointer for conversation persistence")
        await self.session_manager.initialize()
        
        # Load saved sessions
        await self.load_saved_sessions()
        
        logger.info("Post_init initialization complete")

    async def load_saved_sessions(self):
        """Load saved sessions from disk."""
        logger.info("Loading saved sessions from disk")
        loaded_count = 0
        from pathlib import Path
        session_dir = Path(Config.USER_SESSIONS_DIR)
        if session_dir.exists():
            for session_file in session_dir.glob("*_session.json"):
                try:
                    telegram_id = int(session_file.stem.split('_')[0])
                    if await self.session_manager.load_session_from_disk(telegram_id):
                        loaded_count += 1
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse session filename: {session_file}", extra={'error': str(e)})
                except Exception as e:
                    logger.error(f"Failed to load session from {session_file}", extra={'error': str(e)}, exc_info=True)

        logger.info(f"Loaded {loaded_count} saved sessions from disk")

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

        if await self.auth_manager.is_user_authenticated(telegram_id):
            logger.info("User already authenticated", extra={'user_id': telegram_id})
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(ALREADY_AUTHENTICATED_MESSAGE))
            return

        try:
            state = os.urandom(16).hex()
            await self.auth_manager.store_auth_flow(state, telegram_id)
            auth_url = self.auth_manager.generate_auth_url(Config.OAUTH_SCOPES, state)
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
        is_authenticated = await self.auth_manager.is_user_authenticated(telegram_id)
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
        await self.auth_manager.delete_user_token(telegram_id)
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

        if not await self.auth_manager.is_user_authenticated(telegram_id):
            logger.warning("Timezone command from unauthenticated user", extra={'user_id': telegram_id})
            await update.message.reply_markdown_v2(
                await format_markdown_for_telegram(TIMEZONE_NOT_AUTHENTICATED_MESSAGE))
            return

        current_tz = await self.auth_manager.user_tokens_db.get_timezone(telegram_id)
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
            await self.auth_manager.user_tokens_db.update_timezone(telegram_id, timezone)
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

    async def download_files(self, documents: list[Document], telegram_id: int) -> tuple[list[Path], list[str]]:
        """
        Download files with security validation.
        Returns: (list of downloaded paths, list of error messages)
        """
        download_folder = Path(Config.USER_FILES_DIR) / str(telegram_id)
        download_folder.mkdir(parents=True, exist_ok=True)
        downloaded_files = []
        errors = []

        # Check user storage quota
        quota_ok, quota_error = await FileSecurityValidator.check_user_storage_quota(telegram_id)
        if not quota_ok:
            errors.append(quota_error)
            return downloaded_files, errors

        for document in documents:
            try:
                # Get file info
                file = await document.get_file()

                # Get filename
                try:
                    file_name = document.file_name
                except AttributeError:
                    file_name = document.file_unique_id
                    extension = file.file_path.split('.')[-1]
                    file_name = f"{file_name}.{extension}"

                # Sanitize filename
                safe_filename = FileSecurityValidator.sanitize_filename(file_name)

                # Validate file extension
                ext_ok, ext_error = FileSecurityValidator.validate_file_extension(safe_filename)
                if not ext_ok:
                    errors.append(f"{file_name}: {ext_error}")
                    continue

                # Validate file size
                file_size = file.file_size if hasattr(file, 'file_size') else 0
                size_ok, size_error = FileSecurityValidator.validate_file_size(file_size)
                if not size_ok:
                    errors.append(f"{file_name}: {size_error}")
                    continue

                # Download file
                path = await file.download_to_drive(download_folder / safe_filename)
                downloaded_files.append(path)

                logger.info("File downloaded successfully", extra={
                    'user_id': telegram_id,
                    'file_name': safe_filename,
                    'file_size': file_size
                })

            except Exception as e:
                error_msg = f"Error downloading {file_name if 'file_name' in locals() else 'file'}: {str(e)}"
                errors.append(error_msg)
                logger.error("Error downloading file", extra={
                    'file_id': document.file_id,
                    'user_id': telegram_id,
                    'error': str(e)
                }, exc_info=True)

        return downloaded_files, errors

    async def execute_message(self, message_data: MessageData):
        start_time = time.time()
        telegram_id = message_data.update.effective_user.id
        update = message_data.update
        text = message_data.text or ""

        # Rate limit check
        is_allowed, wait_time = await self.rate_limiter.check_rate_limit(telegram_id)
        if not is_allowed:
            await update.message.reply_text(
                f"⚠️ Rate limit exceeded. Please wait {wait_time} seconds before sending more messages."
            )
            return

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

        if message_data.documents:
            paths, download_errors = await self.download_files(message_data.documents, telegram_id)

            if download_errors:
                error_text = "⚠️ File download errors:\n" + "\n".join(download_errors)
                await update.message.reply_text(error_text)

                # If no files were successfully downloaded, return early
                if not paths:
                    return

            if paths:
                text += "\nFile Paths: "
                text += ', '.join([str(path) for path in paths])

        async def typing_action():
            while True:
                await update.message.reply_chat_action(ChatAction.TYPING)
                await asyncio.sleep(4)

        typing_task = asyncio.create_task(typing_action())
        media_group = []

        try:
            human_message = HumanMessage(content=text)
            session.add_message(human_message)
            response = await session.agent.aexecute([human_message])
            session.add_message(response.messages[-1])

            processing_time = time.time() - start_time
            response_text = response.structured_responses[-1].text
            response_files = response.structured_responses[-1].requested_files

            logger.info("Agent response generated successfully", extra={
                'user_id': telegram_id,
                'processing_time': f"{processing_time:.2f}s",
                'response_length': len(response_text),
                'response_preview': response_text[:100]
            })

            # Use context managers for file handling
            if response_files:
                for file_path in response_files:
                    with open(file_path, 'rb') as file_handle:
                        # Read file content and create InputMediaDocument
                        media_group.append(InputMediaDocument(media=file_handle.read(), filename=Path(file_path).name))

            if media_group:
                await update.message.reply_media_group(media=media_group,)

            max_message_len = Config.MAX_MESSAGE_LENGTH
            formatted_message = await format_markdown_for_telegram(response_text)
            for i in range(0, len(response_text), max_message_len):
                await update.message.reply_markdown_v2(formatted_message[i: i + max_message_len])

        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            logger.error("Request timed out", extra={
                'user_id': telegram_id,
                'processing_time': f"{processing_time:.2f}s",
                'message_preview': text[:100]
            })
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(ERROR_TIMEOUT_MESSAGE))

        except ToolException as e:
            processing_time = time.time() - start_time
            logger.error("Tool execution error", extra={
                'user_id': telegram_id,
                'tool_name': e.tool_name,
                'error': str(e),
                'processing_time': f"{processing_time:.2f}s"
            }, exc_info=True)
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(
                ERROR_TOOL_EXECUTION_MESSAGE.format(tool_name=e.tool_name, details=e.message)
            ))

        except AgentException as e:
            processing_time = time.time() - start_time
            logger.error("Agent execution error", extra={
                'user_id': telegram_id,
                'agent_name': e.agent_name,
                'error': str(e),
                'processing_time': f"{processing_time:.2f}s"
            }, exc_info=True)
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(
                f"❌ Error in {e.agent_name}: {e.message}"
            ))

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

    async def handle_files(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        telegram_id = update.effective_user.id

        async with self._pending_message_locks[telegram_id]:
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

        async with self._pending_message_locks[telegram_id]:
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
            if isinstance(error, TimedOut):
                await update.message.reply_markdown_v2(await format_markdown_for_telegram(ERROR_TIMEOUT_MESSAGE))
            elif isinstance(error, NetworkError):
                await update.message.reply_markdown_v2(await format_markdown_for_telegram("⚠️ Network connection error. Please try again."))
            else:
                await update.message.reply_markdown_v2(await format_markdown_for_telegram(ERROR_PROCESSING_MESSAGE))

    async def _cleanup_sessions(self):
        logger.debug("Running session cleanup task")
        cleaned_count = self.session_manager.cleanup_expired_sessions()
        logger.info("Session cleanup completed", extra={'sessions_cleaned': cleaned_count})

    async def _cleanup_old_files(self):
        """Periodic job to clean up old files."""
        logger.debug("Running file cleanup task")
        deleted_count = await FileCleanupManager.cleanup_old_files()
        if deleted_count > 0:
            logger.info("File cleanup completed", extra={'files_deleted': deleted_count})

    async def _auto_save_sessions(self):
        """Periodic job to automatically save all active sessions."""
        logger.debug("Running auto-save sessions task")
        saved_count = 0
        for telegram_id in list(self.session_manager.sessions.keys()):
            try:
                if await self.session_manager.save_session_to_disk(telegram_id):
                    saved_count += 1
            except Exception as e:
                logger.error("Error auto-saving session", extra={
                    'user_id': telegram_id,
                    'error': str(e)
                }, exc_info=True)

        if saved_count > 0:
            logger.info("Auto-save sessions completed", extra={'sessions_saved': saved_count})

    async def send_message(self, telegram_id: int, message: str):
        logger.info("Sending message to user", extra={
            'user_id': telegram_id,
            'message_length': len(message)
        })
        await self.application.bot.send_message(chat_id=telegram_id, text=message)

    def setup_handlers(self):
        """Register all bot handlers."""
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
        logger.info("Bot handlers registered successfully")

    def get_application(self) -> Application:
        """Get the Telegram Application instance for webhook setup."""
        return self.application

    def run(self):
        """Run the bot in polling mode (deprecated - use webhook mode instead)."""
        self.setup_handlers()

        logger.info("Scheduling periodic maintenance jobs")
        # Session cleanup every 300 seconds (5 minutes)
        self.application.job_queue.run_repeating(self._cleanup_sessions, interval=300, first=300)
        # File cleanup every 3600 seconds (1 hour)
        self.application.job_queue.run_repeating(self._cleanup_old_files, interval=3600, first=3600)
        # Auto-save sessions every 600 seconds (10 minutes)
        self.application.job_queue.run_repeating(self._auto_save_sessions, interval=600, first=600)

        logger.info("Starting bot polling")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
