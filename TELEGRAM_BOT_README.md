# Google Agent Telegram Bot

A Telegram bot interface for the Google Agent that allows users to interact with their Google Workspace (Gmail, Calendar, Tasks, and Drive) through Telegram messages.

## Features

- 🔐 **Secure OAuth Authentication** - Each user authenticates with their own Google account
- 💬 **Conversational Interface** - Natural language interaction through Telegram
- 📝 **Context-Aware** - Maintains conversation history for follow-up questions
- 🔄 **Multi-User Support** - Multiple users can use the bot simultaneously
- 💾 **Session Persistence** - Conversations are saved and restored
- 🚀 **Full Google Workspace Access** - All Google Agent capabilities available

## Setup

### Prerequisites

1. **Python 3.8 or higher**
2. **Google Cloud Project** with these APIs enabled:
   - Gmail API
   - Google Calendar API
   - Google Tasks API
   - Google Drive API
3. **Telegram Bot Token** from @BotFather
4. **Google API Key** for Gemini (from Google AI Studio)

### Step 1: Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts to choose a name and username for your bot
4. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. **Important:** Send `/setprivacy` to @BotFather, select your bot, and choose "Disable" to allow the bot to see all messages

### Step 2: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the required APIs (Gmail, Calendar, Tasks, Drive)
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Desktop application" as the application type
6. Click "Create" - Desktop apps automatically get `http://localhost` as a redirect URI
7. Download the credentials JSON file

**Note:** The `http://localhost` redirect URI should be automatically configured for Desktop applications.

### Step 3: Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the API key

### Step 4: Install Dependencies

```bash
# Clone the repository (if not already done)
git clone https://github.com/dsmolla/google-agent.git
cd google-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Environment

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in your credentials:
```env
# Path to your downloaded Google OAuth credentials
CREDS_PATH=path/to/your/credentials.json

# Google API Key from AI Studio
GOOGLE_API_KEY=your_google_api_key_here

# Telegram Bot Token from BotFather
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Optional: Enable debug mode
PRINT_STEPS=false
```

### Step 6: Run the Bot

```bash
python run_bot.py
```

You should see:
```
INFO - Starting Google Agent Bot...
```

The bot is now running! Keep this terminal open.

## Usage

### First Time Setup (For Each User)

1. **Start the bot** - Open Telegram and search for your bot (using the username you chose)
2. **Send `/start`** - This shows the welcome message
3. **Send `/login`** - This starts the authentication process
4. **Authenticate:**
   - Click the Google OAuth link provided by the bot
   - Sign in with your Google account
   - Grant the requested permissions
   - Copy the authorization code
   - Send the code back to the bot
5. **You're ready!** - Start chatting with your Google Agent

### Commands

- `/start` - Show welcome message
- `/login` - Authenticate with Google
- `/status` - Check authentication and session status
- `/clear` - Clear conversation history (start fresh)
- `/logout` - Revoke authentication and delete credentials
- `/help` - Show help message

### Example Conversations

**Gmail:**
```
You: Find all unread emails from today
Bot: I found 5 unread emails from today...

You: Summarize the most important ones
Bot: Here are the most important emails...
```

**Calendar:**
```
You: What meetings do I have tomorrow?
Bot: Tomorrow you have 3 meetings:
1. Team standup at 9:00 AM...

You: Cancel the 2pm meeting
Bot: I've canceled the meeting at 2:00 PM...
```

**Tasks:**
```
You: Show me my overdue tasks
Bot: You have 3 overdue tasks...

You: Create a task to review the budget by Friday
Bot: I've created a task "Review the budget" with due date...
```

**Drive:**
```
You: Find all my spreadsheets from last month
Bot: I found 8 spreadsheets from last month...

You: Create a folder called Q4 Reports
Bot: I've created a folder called "Q4 Reports"...
```

**Cross-Domain:**
```
You: Find emails about the project deadline and create a task
Bot: I found emails about the project. The deadline is March 15th.
I've created a task to track this...

You: Block time on my calendar to work on it
Bot: I've added a 2-hour block on your calendar...
```

## Architecture

```
telegram_bot/
├── __init__.py           # Package initialization
├── config.py             # Configuration and settings
├── auth.py               # Google OAuth authentication
├── session_manager.py    # User session management
└── bot.py               # Main bot logic and handlers

run_bot.py                # Bot entry point
```

### How It Works

1. **User sends a message** → Telegram forwards to your bot
2. **Bot checks authentication** → Ensures user has valid Google credentials
3. **Session management** → Retrieves or creates user's conversation session
4. **Agent execution** → Forwards message to Google Agent with context
5. **Response handling** → Sends agent's response back to user
6. **Session persistence** → Saves conversation for future context

### Security Features

- **Per-user authentication** - Each user uses their own Google account
- **Secure token storage** - Credentials stored separately per user
- **Session timeout** - Inactive sessions expire after 1 hour
- **OAuth refresh** - Tokens automatically refreshed when needed
- **Privacy** - No sharing of data between users

## Troubleshooting

### Bot doesn't respond to messages

1. Check if the bot is running (terminal should show logs)
2. Make sure you've disabled privacy mode with @BotFather
3. Verify your TELEGRAM_BOT_TOKEN is correct
4. Check logs for error messages

### Authentication fails

1. Ensure your credentials.json file exists and is valid
2. Check that all required Google APIs are enabled
3. Try using `/logout` then `/login` again
4. Make sure you're copying the full authorization code

### "Could not initialize agent" error

1. Check that GOOGLE_API_KEY is set correctly
2. Verify credentials.json is accessible
3. Look at the logs for specific error messages
4. Try `/logout` and `/login` again

### Messages are cut off

- Responses longer than 4096 characters are automatically split into multiple messages
- If splitting doesn't work well, try asking for more concise responses

### Bot is slow

- The first request after authentication may be slow (initializing Google client)
- Complex multi-step operations naturally take longer
- Enable `PRINT_STEPS=true` to see what the agent is doing

## Advanced Configuration

### Custom Storage Paths

In your `.env` file:
```env
USER_TOKENS_DIR=custom/path/to/tokens
USER_SESSIONS_DIR=custom/path/to/sessions
```

### Debug Mode

Enable detailed logging:
```env
PRINT_STEPS=true
```

This will show agent reasoning steps in the bot logs.

### Session Timeout

Edit `telegram_bot/config.py`:
```python
SESSION_TIMEOUT = 7200  # 2 hours in seconds
```

## Deployment

### Running in Background (Linux/macOS)

Use `screen` or `tmux`:
```bash
screen -S telegram-bot
python run_bot.py
# Press Ctrl+A then D to detach
```

Or use `nohup`:
```bash
nohup python run_bot.py > bot.log 2>&1 &
```

### Running as a Service (Linux)

Create `/etc/systemd/system/google-agent-bot.service`:
```ini
[Unit]
Description=Google Agent Telegram Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/google-agent
Environment="PATH=/path/to/google-agent/.venv/bin"
ExecStart=/path/to/google-agent/.venv/bin/python run_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable google-agent-bot
sudo systemctl start google-agent-bot
sudo systemctl status google-agent-bot
```

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "run_bot.py"]
```

Build and run:
```bash
docker build -t google-agent-bot .
docker run -d --name google-agent-bot \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/user_tokens:/app/user_tokens \
  -v $(pwd)/user_sessions:/app/user_sessions \
  google-agent-bot
```

## Maintenance

### View Logs

```bash
# If running in foreground, logs appear in terminal

# If using systemd:
sudo journalctl -u google-agent-bot -f

# If using Docker:
docker logs -f google-agent-bot
```

### Backup User Data

```bash
# Backup tokens and sessions
tar -czf backup-$(date +%Y%m%d).tar.gz user_tokens/ user_sessions/
```

### Clear All User Data

```bash
# Warning: This will log out all users
rm -rf user_tokens/*
rm -rf user_sessions/*
```

## Security Best Practices

1. **Keep `.env` secure** - Never commit it to version control
2. **Protect token directories** - Set appropriate file permissions:
   ```bash
   chmod 700 user_tokens user_sessions
   ```
3. **Regular backups** - Backup user tokens and sessions
4. **Monitor logs** - Watch for suspicious activity
5. **Update dependencies** - Keep libraries up to date:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## Support

- For Google Agent issues, see the main [README.md](README.md)
- For Telegram bot issues, check the logs in your terminal
- For authentication issues, refer to [Google OAuth documentation](https://developers.google.com/identity/protocols/oauth2)

## License

Same as the main Google Agent project.
