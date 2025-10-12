"""
Main Telegram Bot implementation for Google Agent
"""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.constants import ChatAction, ParseMode
from langchain_core.messages import HumanMessage

from telegram_bot.config import Config
from telegram_bot.session_manager import SessionManager
from telegram_bot.auth import AuthManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class GoogleAgentBot:
    """Telegram bot for interacting with Google Agent"""

    def __init__(self):
        self.session_manager = SessionManager()
        self.auth_manager = AuthManager()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "there"

        welcome_message = f"""
👋 Hello {user_name}! Welcome to Google Agent Bot!

I'm your AI assistant for managing your Google Workspace - Gmail, Calendar, Tasks, and Drive.

🔐 **Getting Started:**
To use this bot, you need to authenticate with your Google account.
Use /login to begin the authentication process.

📝 **Available Commands:**
/start - Show this welcome message
/login - Authenticate with Google
/status - Check your authentication status
/clear - Clear conversation history
/help - Show help message

Once authenticated, just send me a message and I'll help you with your Google Workspace!

Examples:
• "Find all emails from Sarah about the project"
• "What meetings do I have tomorrow?"
• "Create a task to review the budget by Friday"
• "Find all my presentation files from last month"
"""
        await update.message.reply_text(welcome_message)

    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /login command"""
        user_id = update.effective_user.id

        # Check if already authenticated
        if self.auth_manager.is_user_authenticated(user_id):
            await update.message.reply_text(
                "✅ You're already authenticated! You can start using the bot right away."
            )
            return

        try:
            # Generate authentication URL
            auth_url, flow = self.auth_manager.generate_auth_url()
            self.session_manager.store_auth_flow(user_id, flow)

            # Send message without markdown to avoid URL parsing issues
            message = f"""🔐 Authentication Required

Please follow these steps:

1️⃣ Click or copy the link below to authorize the bot

2️⃣ Sign in with your Google account and grant the requested permissions

3️⃣ After authorizing, you'll be redirected to a page that won't load (this is normal)

4️⃣ Copy the ENTIRE URL from your browser's address bar
   It will look like: http://localhost/?code=4/0A...&scope=...

5️⃣ Send that full URL back to me in a message

💡 Tip: On mobile, long-press the address bar to select and copy the entire URL

⏰ This authorization link will expire in 10 minutes."""

            await update.message.reply_text(message)

            # Send the URL separately to ensure it's not modified
            await update.message.reply_text(f"🔗 Authorization URL:\n{auth_url}")

        except Exception as e:
            logger.error(f"Error generating auth URL for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error generating the authentication link. "
                "Please try again later."
            )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id

        is_authenticated = self.auth_manager.is_user_authenticated(user_id)

        if is_authenticated:
            session = self.session_manager.get_session(user_id)
            message_count = len(session.messages)

            status_message = f"""
✅ **Authentication Status: Authenticated**

📊 Session Info:
• Messages in history: {message_count}
• Session active: Yes

You can start chatting with the bot!
"""
        else:
            status_message = """
❌ **Authentication Status: Not Authenticated**

You need to authenticate with Google to use this bot.
Use /login to begin the authentication process.
"""

        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command"""
        user_id = update.effective_user.id

        self.session_manager.clear_session(user_id)

        await update.message.reply_text(
            "🗑️ Conversation history cleared! Starting fresh."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📚 **Google Agent Bot Help**

**Commands:**
/start - Show welcome message
/login - Authenticate with Google
/status - Check authentication status
/clear - Clear conversation history
/help - Show this help message

**How to use:**
Once authenticated, simply send me a message describing what you want to do with your Google Workspace.

**Example requests:**

**Gmail:**
• "Find all unread emails from today"
• "Summarize emails about the project launch"
• "Delete all my user-created labels"

**Calendar:**
• "What meetings do I have tomorrow?"
• "Schedule a team standup every Monday at 9am"
• "Check my availability this Friday"

**Tasks:**
• "Show me all overdue tasks"
• "Create a task to review the budget by Friday"
• "List all high-priority tasks"

**Drive:**
• "Find all PDFs from last month"
• "Create a folder called Project Alpha"
• "Organize my documents into folders by month"

**Cross-domain:**
• "Find emails from Sarah about the presentation and create a task"
• "What's on my schedule today and what tasks are due?"
• "Save all email attachments from this week to Drive"

💡 **Tips:**
• Be specific in your requests
• You can ask follow-up questions - I maintain conversation context
• Use /clear to start a fresh conversation
• I'll show you when I'm processing your request

Need more help? Just ask!
"""
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)

    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /logout command"""
        user_id = update.effective_user.id

        if self.auth_manager.revoke_authentication(user_id):
            self.session_manager.clear_session(user_id)
            await update.message.reply_text(
                "👋 You've been logged out successfully. Your credentials have been removed.\n"
                "Use /login to authenticate again."
            )
        else:
            await update.message.reply_text(
                "You're not currently authenticated."
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        user_id = update.effective_user.id
        user_message = update.message.text

        # Check if user has pending auth flow (waiting for auth code)
        auth_flow = self.session_manager.get_auth_flow(user_id)
        if auth_flow is not None:
            await self._handle_auth_code(update, context, user_message, auth_flow)
            return

        # Check if authenticated
        if not self.auth_manager.is_user_authenticated(user_id):
            await update.message.reply_text(
                "❌ You need to authenticate first. Use /login to get started."
            )
            return

        # Process message with Google Agent
        await self._process_agent_message(update, context, user_message)

    async def _handle_auth_code(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        auth_input: str,
        flow
    ):
        """Handle authentication code or URL from user"""
        user_id = update.effective_user.id

        # Show processing message
        processing_msg = await update.message.reply_text(
            "🔄 Processing authentication..."
        )

        try:
            # Extract code from URL if user sent the full redirect URL
            auth_code = auth_input.strip()

            # Check if it's a URL with the code parameter
            if 'code=' in auth_code:
                # Extract the code from the URL
                import urllib.parse
                if auth_code.startswith('http'):
                    parsed = urllib.parse.urlparse(auth_code)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'code' in params:
                        auth_code = params['code'][0]
                        logger.info(f"Extracted code from URL for user {user_id}")

            # Complete authentication
            success = self.auth_manager.complete_authentication(
                user_id,
                auth_code,
                flow
            )

            if success:
                self.session_manager.remove_auth_flow(user_id)
                await processing_msg.edit_text(
                    "✅ Authentication successful! You can now start using the bot.\n\n"
                    "Try asking me something like:\n"
                    "• What emails did I receive today?\n"
                    "• What's on my calendar this week?\n"
                    "• Show me my tasks"
                )
            else:
                await processing_msg.edit_text(
                    "❌ Authentication failed. The code might be invalid or expired.\n"
                    "Please use /login to try again."
                )
                self.session_manager.remove_auth_flow(user_id)

        except Exception as e:
            logger.error(f"Error during authentication for user {user_id}: {e}")
            await processing_msg.edit_text(
                "❌ An error occurred during authentication. Please use /login to try again."
            )
            self.session_manager.remove_auth_flow(user_id)

    async def _process_agent_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_message: str
    ):
        """Process message with Google Agent"""
        user_id = update.effective_user.id

        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        try:
            # Get or create agent
            agent = self.session_manager.get_or_create_agent(user_id)
            if agent is None:
                await update.message.reply_text(
                    "❌ Error: Could not initialize the agent. Please try /logout and then /login again."
                )
                return

            # Get session and add user message
            session = self.session_manager.get_session(user_id)
            user_msg = HumanMessage(content=user_message)

            # Execute agent
            logger.info(f"Processing message for user {user_id}: {user_message[:50]}...")

            response = agent.execute(session.messages + [user_msg])

            # Update session with all messages
            session.messages.extend(response.messages)

            # Get the AI's response
            ai_response = response.messages[-1].content

            # Split response if too long (Telegram limit: 4096 chars)
            await self._send_long_message(update, ai_response)

            # Save session
            self.session_manager._save_session_to_disk(user_id)

        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Sorry, I encountered an error processing your request. "
                "Please try again or use /clear to start a fresh conversation."
            )

    async def _send_long_message(self, update: Update, message: str):
        """Split and send long messages with Markdown formatting"""
        max_length = Config.MAX_MESSAGE_LENGTH

        # Try to send with Markdown first
        if len(message) <= max_length:
            await self._send_with_markdown(update, message)
            return

        # Split message into chunks
        chunks = []
        current_chunk = ""

        for line in message.split('\n'):
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + '\n'

        if current_chunk:
            chunks.append(current_chunk)

        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == 0:
                await self._send_with_markdown(update, chunk)
            else:
                await self._send_with_markdown(update, f"(continued...)\n\n{chunk}")

    async def _send_with_markdown(self, update: Update, message: str):
        """
        Send message with Markdown formatting, fallback to plain text if it fails

        Telegram supports basic Markdown:
        - *bold* or **bold**
        - _italic_
        - `code`
        - ```code block```
        - [link](url)
        """
        try:
            # Try regular Markdown (more forgiving than MarkdownV2)
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.warning(f"Failed to send with Markdown: {e}")
            try:
                # If Markdown fails, try escaping special characters and retry
                escaped_message = self._fix_markdown_for_telegram(message)
                await update.message.reply_text(
                    escaped_message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e2:
                logger.warning(f"Failed to send with escaped Markdown: {e2}")
                # Final fallback to plain text
                await update.message.reply_text(message)

    def _fix_markdown_for_telegram(self, text: str) -> str:
        """
        Fix common markdown issues that cause Telegram to reject messages

        Common issues:
        - Unmatched * or _ characters
        - Invalid [] or () combinations
        """
        import re

        # Replace problematic characters that aren't part of valid markdown
        # This is a simple fix - escape standalone underscores not part of _italic_

        # Count asterisks and underscores - if odd number, there's an unmatched one
        # For now, just escape any that would cause issues

        # Simpler approach: escape [ and ] that aren't part of links
        # Escape any [ that isn't followed by ]( pattern
        text = re.sub(r'\[(?![^\]]*\]\()', r'\\[', text)

        return text

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)

        if update and update.message:
            await update.message.reply_text(
                "❌ An unexpected error occurred. Please try again later."
            )

    def run(self):
        """Run the bot"""
        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise

        # Create application with job queue enabled
        application = (
            Application.builder()
            .token(Config.TELEGRAM_BOT_TOKEN)
            .build()
        )

        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("login", self.login))
        application.add_handler(CommandHandler("status", self.status))
        application.add_handler(CommandHandler("clear", self.clear))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("logout", self.logout))

        # Message handler for regular messages
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Error handler
        application.add_error_handler(self.error_handler)

        # Start periodic cleanup of expired sessions (if job_queue is available)
        if application.job_queue:
            application.job_queue.run_repeating(
                self._cleanup_job,
                interval=300,  # Every 5 minutes
                first=300
            )
            logger.info("Session cleanup job scheduled")
        else:
            logger.warning("Job queue not available - session cleanup disabled")

        # Start bot
        logger.info("Starting Google Agent Bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def _cleanup_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Periodic job to cleanup expired sessions"""
        try:
            self.session_manager.cleanup_expired_sessions()
            self.session_manager.save_all_sessions()
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}")
