import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.supervisor import SupervisorAgent
from config import Config
from core.db import database
from core.rate_limit import RateLimitMiddleware
from logging_config import setup_logging
from routes.auth import router as auth_router
from routes.auto_reply import router as auto_reply_router
from routes.chat import router as chat_router
from routes.health import router as health_router
from routes.integrations import router as integrations_router
from routes.models import router as models_router
from routes.settings import router as settings_router
from routes.internal import router as internal_router
from routes.webhooks import router as webhooks_router
from services.gmail_watch import renew_all_watches

load_dotenv()
Config.validate()
setup_logging(Config.LOG_LEVEL)

logger = logging.getLogger(__name__)


async def _renew_watches_job():
    logger.info("Gmail watch renewal job starting")
    try:
        await renew_all_watches()
        logger.info("Gmail watch renewal job completed")
    except Exception as e:
        logger.error(f"Gmail watch renewal job failed: {e}", exc_info=True)


def get_agent(app, model_name: str) -> SupervisorAgent:
    """Get or lazily create a SupervisorAgent for the given model."""
    if model_name not in Config.ALLOWED_MODELS:
        model_name = Config.DEFAULT_MODEL
    if model_name not in app.state.agents:
        llm = ChatGoogleGenerativeAI(model=model_name)
        app.state.agents[model_name] = SupervisorAgent(model=llm, checkpointer=app.state.checkpointer)
        logger.info(f"Created agent for model: {model_name}")
    return app.state.agents[model_name]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    checkpointer = await database.get_checkpointer()
    app.state.checkpointer = checkpointer
    default_llm = ChatGoogleGenerativeAI(model=Config.DEFAULT_MODEL)
    app.state.agents = {Config.DEFAULT_MODEL: SupervisorAgent(model=default_llm, checkpointer=checkpointer)}

    # Start APScheduler for auto-reply background jobs
    scheduler = AsyncIOScheduler()
    if Config.PUBSUB_TOPIC:
        scheduler.add_job(_renew_watches_job, 'interval', hours=6, id='renew_gmail_watches')
    scheduler.start()
    app.state.scheduler = scheduler

    yield

    app.state.scheduler.shutdown()
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router)
app.include_router(auto_reply_router)
app.include_router(health_router)
app.include_router(integrations_router)
app.include_router(models_router)
app.include_router(settings_router)
app.include_router(internal_router)
app.include_router(webhooks_router)
app.include_router(chat_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
