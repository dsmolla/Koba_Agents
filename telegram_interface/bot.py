import os

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


async def format_markdown_for_telegram(text: str) -> str:
    formatted_text = await telegramify_markdown.telegramify(text)
    if len(formatted_text) > 0:
        return formatted_text[0].content
    return ""


class GoogleAgentBot:
    def __init__(self, auth_redirect_uri: str):
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self.session_manager = SessionManager(auth_redirect_uri)
        self.auth_flows = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_name = update.effective_user.first_name or 'there'
        await update.message.reply_markdown_v2(
            await format_markdown_for_telegram(WELCOME_MESSAGE.format(name=user_name)))

    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        if self.session_manager.is_user_authenticated(telegram_id):
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(ALREADY_AUTHENTICATED_MESSAGE))
            return

        try:
            state = os.urandom(16).hex()
            self.session_manager.store_auth_flow(state, telegram_id)
            auth_url = self.session_manager.auth_manager.generate_auth_url(Config.OAUTH_SCOPES, state)
            await update.message.reply_markdown_v2(
                await format_markdown_for_telegram(LOGIN_MESSAGE.format(link=auth_url)))
        except Exception:
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(AUTH_FLOW_ERROR_MESSAGE))

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        if self.session_manager.is_user_authenticated(telegram_id):
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(STATUS_AUTHENTICATED_MESSAGE))
        else:
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(STATUS_NOT_AUTHENTICATED_MESSAGE))

    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        self.session_manager.user_tokens_db.delete_token(telegram_id)
        self.session_manager.clear_session(telegram_id)
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(LOGGED_OUT_MESSAGE))

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        self.session_manager.clear_session(telegram_id)
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(CLEARED_HISTORY_MESSAGE))

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(HELP_MESSAGE))

    async def timezone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id

        if not self.session_manager.is_user_authenticated(telegram_id):
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(TIMEZONE_NOT_AUTHENTICATED_MESSAGE))
            return

        current_tz = self.session_manager.user_tokens_db.get_timezone(telegram_id)
        if not current_tz:
            current_tz = "Not set"

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

        try:
            self.session_manager.user_tokens_db.update_timezone(telegram_id, timezone)
            await query.edit_message_text(
                await format_markdown_for_telegram(TIMEZONE_UPDATED_MESSAGE.format(timezone=timezone)),
                parse_mode='MarkdownV2'
            )
        except Exception:
            await query.edit_message_text(
                await format_markdown_for_telegram(TIMEZONE_ERROR_MESSAGE),
                parse_mode='MarkdownV2'
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        user_message = update.message.text
        session = self.session_manager.get_session(telegram_id)

        if session.agent is None:
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(NOT_LOGGED_IN_MESSAGE))
            return

        session.add_messages([HumanMessage(content=user_message)])
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        try:
            response = await session.agent.aexecute(session.messages)
            session.add_messages(response.messages)
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(response.messages[-1].content))
        except Exception:
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(ERROR_PROCESSING_MESSAGE))

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(ERROR_PROCESSING_MESSAGE))

    async def _cleanup_sessions(self, context: ContextTypes.DEFAULT_TYPE):
        self.session_manager.cleanup_expired_sessions()

    async def send_message(self, telegram_id: int, message: str):
        await self.application.bot.send_message(chat_id=telegram_id, text=message)

    def run(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("login", self.login))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("logout", self.logout))
        self.application.add_handler(CommandHandler("clear", self.clear))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("timezone", self.timezone))
        self.application.add_handler(CallbackQueryHandler(self.handle_timezone_selection, pattern="^"))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # self.application.add_error_handler(self.error_handler)

        self.application.job_queue.run_repeating(self._cleanup_sessions, interval=300, first=300)

        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
