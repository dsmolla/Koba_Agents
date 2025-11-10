import sys

import logging
from telegram_interface.bot import GoogleAgentBot
from threading import Thread
from flask import Flask, request

from telegram_interface.config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


app = Flask(__name__)
bot = GoogleAgentBot('http://localhost:8080/callback')

@app.route('/callback')
async def oauth2_callback():
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

    if token := bot.session_manager.auth_manager.complete_auth_flow(code, Config.OAUTH_SCOPES):
        bot.session_manager.user_tokens_db.add_user(telegram_id, token)
        await bot.send_message(telegram_id, "Authentication successful! You can now use the bot's features. Use /timezone to set your timezone.")
        return "Authentication successful! You can close this window."
    else:
        return "Authentication failed. Please try again.", 400

def run_flask_app():
    app.run(port=8080)


def main():
    """Main entry point"""
    try:
        flask_thread = Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        bot.run()
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        bot.session_manager.user_tokens_db.close()


if __name__ == "__main__":
    main()
