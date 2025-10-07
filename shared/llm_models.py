from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI

MODELS = {
    "gemini": {
        "pro": "gemini-2.5-pro",
        "flash": "gemini-2.5-flash",
        "flash_lite": "gemini-2.5-flash-lite",
    },
    "anthropic": {
        "opus": "claude-opus-4-20250514",
        "sonnet": "claude-3-7-sonnet-20250219",
        "haiku": "claude-3-5-haiku-20241022",
    },
}


RATE_LIMITER = InMemoryRateLimiter(
    requests_per_second=0.16,  # 10 RPM
    check_every_n_seconds=0.1,
    max_bucket_size=10
)

LLM_FLASH = ChatGoogleGenerativeAI(
    model=MODELS['gemini']['flash'],
    rate_limiter=RATE_LIMITER,
)

LLM_PRO = ChatGoogleGenerativeAI(
    model=MODELS['gemini']['pro'],
    rate_limiter=RATE_LIMITER,
)

LLM_LITE = ChatGoogleGenerativeAI(
    model=MODELS['gemini']['flash_lite'],
    rate_limiter=RATE_LIMITER,
)

