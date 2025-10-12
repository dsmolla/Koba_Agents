# Quick Start Guide - Telegram Bot

Get your Google Agent Telegram bot running in 5 minutes!

## Prerequisites

- Python 3.8+
- Google account
- Telegram account

## Step 1: Get a Telegram Bot Token (2 minutes)

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Choose a name (e.g., "My Google Agent")
4. Choose a username (e.g., "my_google_agent_bot")
5. **Copy the token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Send `/setprivacy` to @BotFather, select your bot, choose "Disable"

## Step 2: Get Google Credentials (3 minutes)

### Get OAuth Credentials:
1. Go to https://console.cloud.google.com/
2. Create new project (or select existing)
3. Click "Enable APIs and Services"
4. Enable these APIs: Gmail, Calendar, Tasks, Drive
5. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
6. Choose "Desktop application"
7. Click "Create" (Desktop apps automatically get http://localhost)
8. Click "Download JSON" and save it

### Get API Key:
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

## Step 3: Install and Configure (2 minutes)

```bash
# Clone and setup
git clone https://github.com/dsmolla/google-agent.git
cd google-agent
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
```

Edit `.env`:
```env
CREDS_PATH=path/to/downloaded/credentials.json
GOOGLE_API_KEY=your_api_key_from_step_2
TELEGRAM_BOT_TOKEN=your_bot_token_from_step_1
```

## Step 4: Run! (1 minute)

```bash
python run_bot.py
```

You should see: `INFO - Starting Google Agent Bot...`

## Step 5: Use It!

1. Open Telegram
2. Search for your bot (the username from Step 1)
3. Send `/start`
4. Send `/login`
5. Click the Google link, authorize, and send the code back
6. Start chatting!

### Try These:

```
What emails did I receive today?
What's on my calendar this week?
Show me my tasks
Find all PDFs in my Drive
```

## Troubleshooting

**Bot doesn't respond?**
- Check the terminal for errors
- Make sure you disabled privacy mode in @BotFather

**Authentication fails?**
- Verify all APIs are enabled in Google Cloud Console
- Check that credentials.json path is correct
- Make sure you copied the full authorization code

**Need help?**
See the detailed guide: [TELEGRAM_BOT_README.md](TELEGRAM_BOT_README.md)

## What's Next?

- Read [TELEGRAM_BOT_README.md](TELEGRAM_BOT_README.md) for advanced features
- Explore cross-domain commands (emails + tasks + calendar)
- Deploy to a server to keep it running 24/7

Enjoy your Google Agent! 🚀
