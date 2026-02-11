import logging
from contextlib import asynccontextmanager

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
from routes.chat import router as chat_router
from routes.health import router as health_router
from routes.integrations import router as integrations_router

load_dotenv()
Config.validate()
setup_logging(Config.LOG_LEVEL)

logger = logging.getLogger(__name__)

LLM = ChatGoogleGenerativeAI(model=Config.GEMINI_MODEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    checkpointer = await database.get_checkpointer()
    app.state.supervisor_agent = SupervisorAgent(model=LLM, checkpointer=checkpointer)
    yield
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
app.include_router(health_router)
app.include_router(integrations_router)
app.include_router(chat_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )
