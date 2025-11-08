import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.constants import ChatAction
from langchain_core.messages import HumanMessage
import telegramify_markdown

from telegram_interface.config import Config
from telegram_interface.session_manager import SessionManager
from telegram_interface.messages import *


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
        await update.message.reply_markdown_v2(await format_markdown_for_telegram(WELCOME_MESSAGE.format(name=user_name)))

    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        if self.session_manager.is_user_authenticated(telegram_id):
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(ALREADY_AUTHENTICATED_MESSAGE))
            return

        try:
            state = os.urandom(16).hex()
            self.session_manager.store_auth_flow(state, telegram_id)
            auth_url = self.session_manager.auth_manager.generate_auth_url(Config.OAUTH_SCOPES, state)
            await update.message.reply_markdown_v2(await format_markdown_for_telegram(LOGIN_MESSAGE.format(link=auth_url)))
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
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # self.application.add_error_handler(self.error_handler)

        self.application.job_queue.run_repeating(self._cleanup_sessions, interval=300, first=300)

        self.application.run_polling(allowed_updates=Update.ALL_TYPES)



