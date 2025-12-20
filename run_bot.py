from logging import getLevelName

import asyncio
import sys
import logging

from telegram_interface.bot import GoogleAgentBot
from config import Config
from logging_config import setup_logging
from telegram_interface.auth_instance import auth_manager

Config.validate()

setup_logging(log_level=getLevelName(Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

bot = GoogleAgentBot('http://localhost:8080/callback')


def main():
    logger.info("=" * 60)
    logger.info("Google Agent Bot (Telegram) starting up")
    logger.info("=" * 60)
    logger.info("Note: Run oauth_callback.py separately for OAuth functionality")

    try:
        # Start Telegram bot (blocking)
        logger.info("Starting Telegram bot polling")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
        # Close database connections gracefully
        asyncio.run(auth_manager.user_tokens_db.close())
        asyncio.run(bot.session_manager.close())
        sys.exit(0)
    except Exception as e:
        logger.critical("Fatal error in main", extra={'error': str(e)}, exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Google Agent Bot shut down complete")


if __name__ == "__main__":
    main()
