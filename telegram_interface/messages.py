WELCOME_MESSAGE = """
👋 Hello {name}! Welcome to Google Agent Bot!

I'm your AI assistant for managing your Google Workspace - Gmail, Calendar, Tasks, and Drive.

🔐 **Getting Started:**
To use this bot, you need to authenticate with your Google account.
Use /login to begin the authentication process.

📝 **Available Commands:**
/start - Show this welcome message
/login - Authenticate with Google
/timezone - Set your timezone
/status - Check your authentication status
/clear - Clear conversation history
/logout - Remove Google Authentication
/help - Show help message

Once authenticated, just send me a message and I'll help you with your Google Workspace!

Examples:
• "Find all emails from Sarah about the project"
• "What meetings do I have tomorrow?"
• "Create a task to review the budget by Friday"
• "Find all my presentation files from last month"

"""

ALREADY_AUTHENTICATED_MESSAGE = "✅ You're already authenticated! You can start using the bot right away."

LOGIN_MESSAGE = """
🔐 Authentication Required

Please follow these steps:

1️⃣ Click or copy the link below to authorize the bot

2️⃣ Sign in with your Google account and grant the requested permissions

3️⃣ After authorizing, return to this bot

⏰ This authorization [link]({link}) will expire in 10 minutes.
"""

AUTH_FLOW_ERROR_MESSAGE = "❌ Sorry, there was an error generating the authentication link. Please try again later."

STATUS_AUTHENTICATED_MESSAGE = "✅ You are authenticated with Google. You can start using the bot!"
STATUS_NOT_AUTHENTICATED_MESSAGE = "❌ You are not authenticated. Please use /login to authenticate with your Google account."

NOT_LOGGED_IN_MESSAGE = "❌ You need to authenticate first. Use /login to authenticate with your Google account."

LOGGED_OUT_MESSAGE = "✅ You have been logged out and your session cleared."

CLEARED_HISTORY_MESSAGE = "🗑️ Your conversation history has been cleared."

HELP_MESSAGE = """
📚 **Google Agent Bot Help**

**Commands:**
/start - Show welcome message
/login - Authenticate with Google
/timezone - Set your timezone
/status - Check authentication status
/clear - Clear conversation history
/logout - Remove Google Authentication
/help - Show this help message

I'm here to assist you with managing your Google Workspace - Gmail, Calendar, Tasks, and Drive.
Here are some tips to get the most out of our interactions:
• Be specific: The more details you provide, the better I can assist you. For example, instead of saying "Find emails", say "Find emails from John about the project".
• Use natural language: You can ask questions or give commands in a conversational way. For example, "What meetings do I have tomorrow?" or "Create a task to review the budget by Friday".
• You can combine requests: Feel free to ask for multiple things in one message, like "Find emails from Sarah and create a task to follow up".
• You can ask follow-up questions - I maintain context within a session.
• Explore features: I can help with a variety of tasks including searching emails, managing calendar events, creating tasks, and finding files in Google Drive.
• Privacy: I respect your privacy and only access the information necessary to assist you. Your data is not stored or shared.
• Use /clear to start a new conversation and clear history.

If you have any questions or need further assistance, just ask!
"""

ERROR_PROCESSING_MESSAGE = "❌ Sorry, I encountered an error processing your request. Please try again or use /clear to start a fresh conversation."

TIMEZONE_PROMPT_MESSAGE = """
🌍 **Set Your Timezone**

Please select your timezone from the options below. This helps me display calendar events and schedule tasks at the correct time for you.

Your current timezone: {current_timezone}
"""

TIMEZONE_UPDATED_MESSAGE = "✅ Your timezone has been updated to **{timezone}**."

TIMEZONE_ERROR_MESSAGE = "❌ There was an error updating your timezone. Please try again."

TIMEZONE_NOT_AUTHENTICATED_MESSAGE = "❌ You need to authenticate first. Use /login to authenticate with your Google account."