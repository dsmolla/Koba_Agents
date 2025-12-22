import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from logging import getLevelName
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update

from telegram_interface.bot import GoogleAgentBot
from telegram_interface.auth_instance import auth_manager
from config import Config
from logging_config import setup_logging

# Validate configuration
Config.validate()

# Setup logging
setup_logging(log_level=getLevelName(Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize bot instance
bot = GoogleAgentBot(Config.OAUTH_REDIRECT_URI)

# Graceful shutdown management
class GracefulShutdown:
    def __init__(self):
        self.is_shutting_down = False
        self.active_requests = 0
        self.shutdown_event = asyncio.Event()
        self.scheduler: Optional[AsyncIOScheduler] = None

    async def wait_for_completion(self, timeout: float = 30.0):
        """Wait for all active requests to complete."""
        if self.active_requests > 0:
            logger.info(f"Waiting for {self.active_requests} active requests to complete")
            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for requests, {self.active_requests} still active")
        logger.info("All requests completed or timeout reached")

    def mark_shutting_down(self):
        """Mark the server as shutting down."""
        self.is_shutting_down = True
        logger.info("Server marked as shutting down")


shutdown_manager = GracefulShutdown()


async def setup_background_jobs():
    """Setup periodic background jobs using APScheduler."""
    logger.info("Setting up background jobs with APScheduler")

    scheduler = AsyncIOScheduler()

    # Session cleanup every 5 minutes
    scheduler.add_job(
        bot._cleanup_sessions,
        'interval',
        seconds=300,
        id='cleanup_sessions',
        name='Session cleanup',
    )

    # File cleanup every hour
    scheduler.add_job(
        bot._cleanup_old_files,
        'interval',
        seconds=3600,
        id='cleanup_files',
        name='File cleanup'
    )

    # Auto-save sessions every 10 minutes
    scheduler.add_job(
        bot._auto_save_sessions,
        'interval',
        seconds=600,
        id='auto_save_sessions',
        name='Auto-save sessions'
    )

    scheduler.start()
    shutdown_manager.scheduler = scheduler
    logger.info("Background jobs scheduled successfully")

    return scheduler


async def process_pending_messages():
    """Process all pending message groups before shutdown."""
    logger.info(f"Processing {len(bot.pending_messages)} pending message groups")
    for telegram_id, timer_task in list(bot.timers.items()):
        timer_task.cancel()  # Cancel the timer
        if telegram_id in bot.pending_messages:
            message_data = bot.pending_messages[telegram_id]
            try:
                await bot.execute_message(message_data)
                logger.info(f"Processed pending messages for user {telegram_id}")
            except Exception as e:
                logger.error(f"Error processing pending message for {telegram_id}: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("Google Agent Bot (Telegram) - Webhook Mode")
    logger.info("=" * 60)

    try:
        # Initialize bot
        logger.info("Initializing bot and database")
        await bot.post_init(bot.application)

        # Register handlers
        bot.setup_handlers()

        # Setup background jobs
        await setup_background_jobs()

        # Start the Telegram application
        await bot.application.initialize()
        await bot.application.start()

        # Configure webhook
        webhook_url = f"{Config.WEBHOOK_URL}/webhook/{Config.WEBHOOK_SECRET_TOKEN}"
        logger.info(f"Setting webhook: {Config.WEBHOOK_URL}/webhook/***")

        await bot.application.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            max_connections=Config.WEBHOOK_MAX_CONNECTIONS,
            secret_token=Config.WEBHOOK_SECRET_TOKEN,
            drop_pending_updates=False
        )

        # Verify webhook
        webhook_info = await bot.application.bot.get_webhook_info()
        logger.info("Webhook configured successfully", extra={
            'url': webhook_info.url,
            'pending_update_count': webhook_info.pending_update_count,
            'max_connections': webhook_info.max_connections
        })

        logger.info(f"Webhook server ready on port {Config.WEBHOOK_PORT}")
        logger.info("Google Agent Bot is now running in webhook mode")

        yield

        # Shutdown
        logger.info("Shutting down Google Agent Bot")
        shutdown_manager.mark_shutting_down()

        # Process pending messages
        await process_pending_messages()

        # Wait for active requests
        await shutdown_manager.wait_for_completion(timeout=30.0)

        # Shutdown scheduler
        if shutdown_manager.scheduler:
            logger.info("Shutting down background job scheduler")
            shutdown_manager.scheduler.shutdown(wait=False)

        # Delete webhook
        logger.info("Removing webhook")
        await bot.application.bot.delete_webhook(drop_pending_updates=False)

        # Stop application
        logger.info("Stopping Telegram application")
        await bot.application.stop()
        await bot.application.shutdown()

        # Close database connections
        logger.info("Closing database connections")
        await auth_manager.user_tokens_db.close()
        await bot.session_manager.close()

        logger.info("Shutdown complete")

    except Exception as e:
        logger.critical("Error during startup/shutdown", extra={'error': str(e)}, exc_info=True)
        raise


# Create FastAPI app with lifespan
app = FastAPI(
    title="Google Agent Telegram Bot",
    version="1.0.0",
    lifespan=lifespan
)


# Middleware to track active requests
@app.middleware("http")
async def track_active_requests(request: Request, call_next):
    """Track active requests and reject new ones during shutdown."""
    if shutdown_manager.is_shutting_down:
        logger.warning("Rejecting request during shutdown", extra={
            'path': request.url.path,
            'method': request.method
        })
        return JSONResponse(
            {"error": "Server is shutting down"},
            status_code=503
        )

    shutdown_manager.active_requests += 1
    try:
        response = await call_next(request)
        return response
    finally:
        shutdown_manager.active_requests -= 1
        if shutdown_manager.active_requests == 0 and shutdown_manager.is_shutting_down:
            shutdown_manager.shutdown_event.set()


# Telegram webhook endpoint
@app.post(f"/webhook/{Config.WEBHOOK_SECRET_TOKEN}")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None)
):
    """Handle incoming Telegram webhook updates."""
    # Verify secret token
    if x_telegram_bot_api_secret_token != Config.WEBHOOK_SECRET_TOKEN:
        logger.warning("Webhook request with invalid secret token")
        return Response(status_code=403)

    # Parse update
    try:
        update_data = await request.json()
        update = Update.de_json(update_data, bot.application.bot)

        if update:
            # Process update asynchronously
            await bot.application.update_queue.put(update)
            logger.debug("Webhook update queued", extra={'update_id': update.update_id})
        else:
            logger.warning("Received invalid update data")

        return Response(status_code=200)

    except Exception as e:
        logger.error("Error processing webhook update", extra={'error': str(e)}, exc_info=True)
        return Response(status_code=500)


# OAuth callback route
@app.get("/callback")
async def oauth2_callback(state: str = None, code: str = None):
    """Handle Google OAuth2 callback."""
    logger.info("OAuth callback received", extra={
        'has_state': bool(state),
        'has_code': bool(code),
    })

    if not state:
        logger.warning("OAuth callback with invalid state")
        return PlainTextResponse("Invalid state parameter", status_code=400)
    if not code:
        logger.warning("OAuth callback missing code parameter")
        return PlainTextResponse("Missing code parameter", status_code=400)

    # Get auth flow data
    auth_flow_data = auth_manager.get_auth_flow(state)
    auth_manager.remove_auth_flow(state)

    if not auth_flow_data:
        logger.error("OAuth callback with invalid or expired state")
        return PlainTextResponse("Invalid or expired state parameter", status_code=400)

    telegram_id, pkce_verifier = auth_flow_data

    try:
        # Complete OAuth flow
        if token := auth_manager.complete_auth_flow(code, Config.OAUTH_SCOPES):
            auth_manager.user_tokens_db.add_user_sync(telegram_id, token)
            logger.info("OAuth authentication successful", extra={'user_id': telegram_id})

            # Send notification to user via bot
            try:
                await bot.application.bot.send_message(
                    chat_id=telegram_id,
                    text="Authentication successful! You can now use the bot's features. Use /timezone to set your timezone.",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                return PlainTextResponse("Authentication successful! You can close this window.")
            except Exception as e:
                logger.error(f"Error sending Telegram notification: {e}", extra={'user_id': telegram_id})
                return PlainTextResponse("Authentication successful but notification failed. You can close this window.")
        else:
            logger.error("OAuth token exchange failed", extra={'user_id': telegram_id})
            return PlainTextResponse("Authentication failed. Please try again.", status_code=400)
    except Exception as e:
        logger.error("OAuth callback exception", extra={
            'user_id': telegram_id,
            'error': str(e)
        }, exc_info=True)
        return PlainTextResponse("Authentication failed. Please try again.", status_code=500)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        bot_username = bot.application.bot.username if bot.application.bot.username else "unknown"
        return {
            "status": "healthy",
            "bot_username": bot_username,
            "active_sessions": len(bot.session_manager.sessions),
            "webhook_configured": True,
            "is_shutting_down": shutdown_manager.is_shutting_down
        }
    except Exception as e:
        logger.error("Health check error", extra={'error': str(e)})
        return JSONResponse(
            {"status": "unhealthy", "error": str(e)},
            status_code=500
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Google Agent Telegram Bot",
        "mode": "webhook",
        "status": "running"
    }


def main():
    """Main entry point."""
    try:
        # Run the FastAPI app with Uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=Config.WEBHOOK_PORT,
            log_config=None,  # Use our custom logging
            access_log=False  # Disable Uvicorn access logs (we have our own)
        )
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.critical("Fatal error", extra={'error': str(e)}, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
