import os

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        # Refuse to start instead of failing on the first question.
        raise RuntimeError(f"Missing required setting: {name}")
    return value


class Settings:
    _provider = os.getenv("AI_PROVIDER", "gemini").lower()
    APP_NAME = "ScreenGuide AI Layer"
    # "gemini" (free tier) or "claude". Change this one setting to switch.
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
    # Check ai.google.dev for the current free model name and limits.
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    GEMINI_API_KEY = _required("GEMINI_API_KEY") if _provider == "gemini" else os.getenv("GEMINI_API_KEY")
    ANTHROPIC_API_KEY = _required("ANTHROPIC_API_KEY") if _provider == "claude" else os.getenv("ANTHROPIC_API_KEY")
    APP_TOKEN = _required("APP_TOKEN")
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "500"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "350"))
    PER_INSTALL_PER_MINUTE = int(os.getenv("PER_INSTALL_PER_MINUTE", "5"))
    PER_INSTALL_PER_DAY = int(os.getenv("PER_INSTALL_PER_DAY", "40"))
    GLOBAL_PER_DAY = int(os.getenv("GLOBAL_PER_DAY", "800"))


settings = Settings()
