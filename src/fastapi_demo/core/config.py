import secrets
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi_mail import ConnectionConfig
from pydantic import (
    AmqpDsn,
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

    PROJECT_NAME: str
    API_PREFIX: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(nbytes=32)
    # 60 minutes * 24 hours * 7 days = 7 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    API_KEY_EXPIRE_MINUTES: int = 60

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )  # type: ignore[return-value]

    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_RECYCLE: int = -1
    POOL_PRE_PING: bool = False
    POOL_TIMEOUT: int = 30

    REDIS_SERVER: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    REDIS_USERS_DB: int = 0
    REDIS_USERS_TOKEN_KEY_PREFIX: str = "fastapi_users_token:"  # noqa: S105
    REDIS_USERS_APIKEY_KEY_PREFIX: str = "fastapi_users_api_key:"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URI(self) -> RedisDsn:
        return MultiHostUrl.build(scheme="redis", host=self.REDIS_SERVER, port=self.REDIS_PORT)  # type: ignore[return-value]

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
    # RATE_LIMITING_USERS_CACHE_REDIS_DB: int = 3
    # RATE_LIMITING_USERS_CACHE_TTL: int = 3600

    @computed_field  # type: ignore[prop-decorator]
    @property
    def rate_limiter_storage_uri(self) -> str:
        return "async+" + str(
            RedisDsn(
                MultiHostUrl.build(
                    scheme="redis",
                    host=self.REDIS_SERVER,
                    port=self.REDIS_PORT,
                    path=f"{self.RATE_LIMITING_REDIS_DB}",
                )  # type: ignore[arg-type]
            )
        )

    # @computed_field  # type: ignore[prop-decorator]
    # @property
    # def RATE_LIMITING_USERS_CACHE_REDIS_CONFIG(self) -> dict:
    #     return {
    #         "cache": RedisCache,
    #         "endpoint": self.REDIS_SERVER,
    #         "port": self.REDIS_PORT,
    #         "db": self.RATE_LIMITING_USERS_CACHE_REDIS_DB,
    #         "password": self.REDIS_PASSWORD,
    #         "serializer": JsonSerializer(),
    #         "ttl": self.RATE_LIMITING_USERS_CACHE_TTL,
    #         "namespace": "user_id_for_rate_limiting",
    #     }

    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    USER_PASSWORD_MIN_LENGTH: int = 8
    USER_PASSWORD_MAX_LENGTH: int = 40
    USE_DYNAMICALLY_ENABLED_AUTH_BACKENDS: bool = False

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URL: HttpUrl
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URL: HttpUrl

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
    def VALID_MAIL_SSL_TLS(self) -> bool:
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

    CELERY_APP_NAME: str = "celery_app"
    CELERY_REDIS_DB: int = 2

    RABBITMQ_SERVER: str
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_DEFAULT_VHOST: str
    RABBITMQ_AMQP_PORT: int = 5672

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_BROKER_URL(self) -> AmqpDsn:
        return MultiHostUrl.build(
            scheme="amqp",
            username=self.RABBITMQ_DEFAULT_USER,
            password=self.RABBITMQ_DEFAULT_PASS,
            host=self.RABBITMQ_SERVER,
            port=self.RABBITMQ_AMQP_PORT,
            path=f"{self.RABBITMQ_DEFAULT_VHOST}",
        )  # type: ignore[return-value]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_REDIS_URI(self) -> RedisDsn:
        return MultiHostUrl.build(
            scheme="redis",
            host=self.REDIS_SERVER,
            port=self.REDIS_PORT,
            path=f"{self.CELERY_REDIS_DB}",
        )  # type: ignore[return-value]

    OPENFGA_AUTHN_METHOD: Literal["preshared"] | None = None
    FGA_API_URL: HttpUrl
    FGA_STORE_NAME: str
    FGA_API_TOKEN: str = secrets.token_urlsafe(32)
    FGA_STORE_ID: str = ""
    FGA_MODEL_ID: str = ""


settings = Settings()  # type: ignore[call-arg]
