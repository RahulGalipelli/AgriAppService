from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AgriCure Backend"
    ENV: str = "local"
    DEBUG: bool = True

    # Database - Support both DATABASE_URL (cloud) and individual vars (local)
    DATABASE_URL: Optional[str] = None  # Cloud providers use this
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None

    @property
    def database_url(self) -> str:
        # If DATABASE_URL is provided (cloud), use it directly
        if self.DATABASE_URL:
            # Convert to asyncpg format if needed
            if "postgresql://" in self.DATABASE_URL and "+asyncpg" not in self.DATABASE_URL:
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            return self.DATABASE_URL
        
        # Otherwise, build from individual vars (local development)
        if not all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DB]):
            raise ValueError("Either DATABASE_URL or all POSTGRES_* variables must be set")
        
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        # SYNC (Alembic only) - convert asyncpg to psycopg2
        url = self.database_url
        if "+asyncpg" in url:
            return url.replace("+asyncpg", "+psycopg2")
        elif "postgresql://" in url and "+" not in url:
            return url.replace("postgresql://", "postgresql+psycopg2://")
        return url

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    # Twilio
    TWILIO_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE: str
    TWILIO_VERIFY_SERVICE_SID: str

    #Security
    SECRET_KEY: str

    # OpenAI
    OPENAI_API_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
