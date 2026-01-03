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

custom_profile = {"structured_output": True}
LLM_FLASH = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])


