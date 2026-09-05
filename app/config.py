import os
import threading
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Qwen API
        self.QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
        self.QWEN_API_URL: str = os.getenv(
            "QWEN_API_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        )
        self.QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-plus")

        # Tavily keys (round-robin)
        tavily_raw = os.getenv("TAVILY_KEYS", "")
        self.TAVILY_KEYS: list[str] = [
            k.strip() for k in tavily_raw.split(",") if k.strip()
        ]
        self._tavily_index: int = 0
        self._tavily_lock = threading.Lock()

        # Brave keys (round-robin)
        brave_raw = os.getenv("BRAVE_KEYS", "")
        self.BRAVE_KEYS: list[str] = [
            k.strip() for k in brave_raw.split(",") if k.strip()
        ]
        self._brave_index: int = 0
        self._brave_lock = threading.Lock()

        # JWT
        self.SECRET_KEY: str = os.getenv(
            "SECRET_KEY", "finance-suite-secret-key-change-in-production-2026"
        )
        self.ACCESS_TOKEN_EXPIRE_HOURS: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24")
        )

        # App
        self.APP_NAME: str = os.getenv("APP_NAME", "Finance Suite")
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    def get_tavily_key(self) -> str:
        """Get next Tavily API key using round-robin."""
        if not self.TAVILY_KEYS:
            return ""
        with self._tavily_lock:
            key = self.TAVILY_KEYS[self._tavily_index % len(self.TAVILY_KEYS)]
            self._tavily_index += 1
            return key

    def get_brave_key(self) -> str:
        """Get next Brave API key using round-robin."""
        if not self.BRAVE_KEYS:
            return ""
        with self._brave_lock:
            key = self.BRAVE_KEYS[self._brave_index % len(self.BRAVE_KEYS)]
            self._brave_index += 1
            return key


settings = Settings()
