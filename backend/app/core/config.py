import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./personal_agent_cloud.db")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "development-only-change-me")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))
    require_email_verification: bool = os.getenv(
        "REQUIRE_EMAIL_VERIFICATION", "false"
    ).lower() == "true"
    secure_cookies: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    max_agents_per_user: int = int(os.getenv("MAX_AGENTS_PER_USER", "10"))
    groq_builder_model: str = os.getenv("GROQ_BUILDER_MODEL", "openai/gpt-oss-120b")


settings = Settings()
