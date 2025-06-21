import secrets
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi_mail import ConnectionConfig
from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    RedisDsn,
    SecretStr,
    computed_field,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    API_PREFIX: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(nbytes=32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    PROJECT_NAME: str

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> PostgresDsn:  # noqa: N802
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )  # type: ignore[return-value]

    REDIS_SERVER: str
    REDIS_USERS_DB: int = 0
    REDIS_USERS_KEY_PREFIX: str = "fastapi_users_token:"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URI(self) -> RedisDsn:  # noqa: N802
        return MultiHostUrl.build(scheme="redis", host=self.REDIS_SERVER, port=6379)  # type: ignore[return-value]

    FRONTEND_HOST: HttpUrl = "http://localhost:8501"  # type: ignore[assignment]
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            str(self.FRONTEND_HOST)
        ]

    RATE_LIMITING_ENABLED: bool
    RATE_LIMITING_HEADERS_ENABLED: bool = False
    RATE_LIMITING_REDIS_DB: int = 1
    RATE_LIMITING_STRATEGY: Literal["sliding-window-counter", "fixed-window", "moving-window"] = (
        "fixed-window"
    )
    RATE_LIMIT_VALUE_PER_SECOND_AUTH: int = 2
    RATE_LIMIT_VALUE_PER_SECOND_LOGGEDIN: int = 10
    RATE_LIMIT_VALUE_PER_SECOND_PUBLIC: int = 5
    RATE_LIMIT_VALUE_PER_MINUTE_AUTH: int = 60
    RATE_LIMIT_VALUE_PER_MINUTE_LOGGEDIN: int = 300
    RATE_LIMIT_VALUE_PER_MINUTE_PUBLIC: int = 100

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rate_limiter_storage_uri(self) -> str:
        return "async+" + str(
            RedisDsn(
                MultiHostUrl.build(
                    scheme="redis",
                    host=self.REDIS_SERVER,
                    port=6379,
                    path=f"{self.RATE_LIMITING_REDIS_DB}",
                )  # type: ignore[arg-type]
            )
        )

    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    USER_PASSWORD_MIN_LENGTH: int = 8
    USER_PASSWORD_MAX_LENGTH: int = 40

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_SERVER: str
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM: EmailStr
    MAIL_FROM_NAME: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def VALID_MAIL_SSL_TLS(self) -> bool:  # noqa: N802
        return False if self.MAIL_STARTTLS else self.MAIL_SSL_TLS

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mailer_config(self) -> ConnectionConfig:
        return ConnectionConfig(
            MAIL_USERNAME=self.MAIL_USERNAME,
            MAIL_PASSWORD=self.MAIL_PASSWORD,
            MAIL_SERVER=self.MAIL_SERVER,
            MAIL_PORT=self.MAIL_PORT,
            MAIL_STARTTLS=self.MAIL_STARTTLS,
            MAIL_SSL_TLS=self.VALID_MAIL_SSL_TLS,
            MAIL_FROM=self.MAIL_FROM,
            MAIL_FROM_NAME=self.MAIL_FROM_NAME,
            TEMPLATE_FOLDER=Path(__file__).parent.parent / "email-templates",
        )


settings = Settings()  # type: ignore[call-arg]
