#!/usr/bin/env python3
"""
Entry point for running the Telegram bot

Usage:
    python run_bot.py
"""

import sys
import logging
from telegram_bot.bot import GoogleAgentBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    try:
        bot = GoogleAgentBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
