"""Application settings for MediMind AI."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

from config.constants import (
    APP_TITLE,
    APP_VERSION,
    DATABASE_DRIVER_DEFAULT,
    DATABASE_MAX_OVERFLOW_DEFAULT,
    DATABASE_HOST_DEFAULT,
    DATABASE_PORT_DEFAULT,
    DATABASE_POOL_RECYCLE_DEFAULT,
    DATABASE_POOL_SIZE_DEFAULT,
    DATABASE_POOL_TIMEOUT_DEFAULT,
    ENVIRONMENT_DEVELOPMENT,
    JWT_ALGORITHM_DEFAULT,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES_DEFAULT,
    PINECONE_INDEX_NAME,
)
from app_logging.logger import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: Annotated[str, Field(alias="APP_NAME")] = APP_TITLE
    app_version: Annotated[str, Field(alias="APP_VERSION")] = APP_VERSION
    environment: Annotated[str, Field(alias="ENVIRONMENT")] = ENVIRONMENT_DEVELOPMENT
    debug: Annotated[bool, Field(alias="DEBUG")] = False
    google_api_key: Annotated[str | None, Field(default=None, alias="GOOGLE_API_KEY")]
    database_driver: Annotated[str, Field(alias="DB_DRIVER")] = DATABASE_DRIVER_DEFAULT
    database_host: Annotated[str, Field(alias="DB_HOST")] = DATABASE_HOST_DEFAULT
    database_port: Annotated[int, Field(alias="DB_PORT")] = DATABASE_PORT_DEFAULT
    database_name: Annotated[str | None, Field(default=None, alias="DB_NAME")]
    database_user: Annotated[str | None, Field(default=None, alias="DB_USER")]
    database_password: Annotated[str | None, Field(default=None, alias="DB_PASSWORD")]
    database_pool_size: Annotated[int, Field(alias="DB_POOL_SIZE")] = DATABASE_POOL_SIZE_DEFAULT
    database_max_overflow: Annotated[int, Field(alias="DB_MAX_OVERFLOW")] = DATABASE_MAX_OVERFLOW_DEFAULT
    database_pool_recycle: Annotated[int, Field(alias="DB_POOL_RECYCLE")] = DATABASE_POOL_RECYCLE_DEFAULT
    database_pool_timeout: Annotated[int, Field(alias="DB_POOL_TIMEOUT")] = DATABASE_POOL_TIMEOUT_DEFAULT
    pinecone_api_key: Annotated[str | None, Field(default=None, alias="PINECONE_API_KEY")]
    pinecone_index_name: Annotated[str, Field(alias="PINECONE_INDEX_NAME")] = PINECONE_INDEX_NAME
    jwt_secret_key: Annotated[str, Field(alias="JWT_SECRET_KEY")] = "change-me-in-production"
    jwt_algorithm: Annotated[str, Field(alias="JWT_ALGORITHM")] = JWT_ALGORITHM_DEFAULT
    access_token_expire_minutes: Annotated[
        int,
        Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    ] = JWT_ACCESS_TOKEN_EXPIRE_MINUTES_DEFAULT

    @property
    def database_connection_string(self) -> str | None:
        """Build the PostgreSQL connection string from the discrete database settings."""
        if not self.database_name:
            return None

        url = URL.create(
            drivername=self.database_driver,
            username=self.database_user,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )
        return url.render_as_string(hide_password=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton settings instance."""
    loaded_settings = Settings()
    logger.debug(
        "Application settings loaded",
        environment=loaded_settings.environment,
        debug=loaded_settings.debug,
    )
    return loaded_settings


settings = get_settings()
