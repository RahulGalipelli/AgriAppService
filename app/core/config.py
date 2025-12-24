from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AgriCure Backend"
    ENV: str = "local"
    DEBUG: bool = True

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    @property
    def database_url(self) -> str:
        # ASYNC (FastAPI runtime)
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def database_url_sync(self) -> str:
        # SYNC (Alembic only)
        return self.database_url.replace("+asyncpg", "+psycopg2")

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    # Twilio
    TWILIO_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE: str
    TWILIO_VERIFY_SERVICE_SID: str

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
