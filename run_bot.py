import asyncio
import requests
import sys
from threading import Thread

from flask import Flask, request

from telegram_interface.bot import GoogleAgentBot
from telegram_interface.config import Config

Config.validate()


app = Flask(__name__)
bot = GoogleAgentBot('http://localhost:8080/callback')

@app.route('/callback')
def oauth2_callback():
    state = request.args.get('state')
    code = request.args.get('code')

    if not state or state not in bot.session_manager.auth_flows:
        return "Invalid state parameter", 400
    if not code:
        return "Missing code parameter", 400

    telegram_id = bot.session_manager.get_auth_flow(state)
    bot.session_manager.remove_auth_flow(state)

    if not telegram_id:
        return "Invalid state parameter", 400

    try:
        if token := bot.session_manager.auth_manager.complete_auth_flow(code, Config.OAUTH_SCOPES):
            asyncio.run(bot.session_manager.user_tokens_db.add_user(telegram_id, token))

            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": telegram_id,
                "text": "Authentication successful! You can now use the bot's features. Use /timezone to set your timezone.",
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            try:
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                return "Authentication successful! You can close this window."
            except requests.exceptions.RequestException:
                return "Authentication failed. Please try again.", 400
        else:
            return "Authentication failed. Please try again.", 400
    except Exception:
        return "Authentication failed. Please try again.", 500

def run_flask_app():
    app.run(port=8080, debug=False)


def main():
    try:
        # Initialize database tables
        asyncio.run(bot.session_manager.user_tokens_db._create_tables())

        flask_thread = Thread(target=run_flask_app, daemon=True)
        flask_thread.start()

        # Start Telegram bot (blocking)
        bot.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
