import logging
from logging import getLevelName

import requests
from flask import Flask, request
import waitress

from telegram_interface.bot import GoogleAgentBot
from config import Config
from logging_config import setup_logging
from telegram_interface.auth_instance import auth_manager

Config.validate()

setup_logging(log_level=getLevelName(Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Create bot instance just for sending notifications
notification_bot = GoogleAgentBot(Config.OAUTH_REDIRECT_URI)


@app.route('/callback')
def oauth2_callback():
    state = request.args.get('state')
    code = request.args.get('code')

    logger.info("OAuth callback received", extra={
        'has_state': bool(state),
        'has_code': bool(code),
        'remote_addr': request.remote_addr
    })

    if not state:
        logger.warning("OAuth callback with invalid state")
        return "Invalid state parameter", 400
    if not code:
        logger.warning("OAuth callback missing code parameter")
        return "Missing code parameter", 400

    # Use auth_manager directly (no session_manager)
    auth_flow_data = auth_manager.get_auth_flow(state)
    auth_manager.remove_auth_flow(state)

    if not auth_flow_data:
        logger.error("OAuth callback with invalid or expired state")
        return "Invalid or expired state parameter", 400

    telegram_id, pkce_verifier = auth_flow_data

    try:
        if token := auth_manager.complete_auth_flow(code, Config.OAUTH_SCOPES):
            auth_manager.user_tokens_db.add_user_sync(telegram_id, token)
            logger.info("OAuth authentication successful", extra={'user_id': telegram_id})

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
            except requests.exceptions.RequestException as e:
                logger.error(f"Error sending Telegram notification: {e}")
                return "Authentication failed. Please try again.", 400
        else:
            logger.error("OAuth token exchange failed", extra={'user_id': telegram_id})
            return "Authentication failed. Please try again.", 400
    except Exception as e:
        logger.error("OAuth callback exception", extra={
            'user_id': telegram_id,
            'error': str(e)
        }, exc_info=True)
        return "Authentication failed. Please try again.", 500


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Google Agent OAuth Callback Server starting up")
    logger.info("=" * 60)
    logger.info("Starting Flask OAuth server with Waitress on port 8080")

    # Disable Flask's default logger output to avoid duplicate logs
    import logging as flask_logging
    werkzeug_logger = flask_logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(flask_logging.WARNING)
    waitress_logger = flask_logging.getLogger('waitress')
    waitress_logger.setLevel(flask_logging.WARNING)

    try:
        waitress.serve(app, host='0.0.0.0', port=8080, _quiet=True)
    except KeyboardInterrupt:
        logger.info("OAuth server shutting down")
    except Exception as e:
        logger.critical("Fatal error in OAuth server", extra={'error': str(e)}, exc_info=True)
    finally:
        logger.info("OAuth server shut down complete")
