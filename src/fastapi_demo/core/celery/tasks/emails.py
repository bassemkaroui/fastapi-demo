import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from fastapi_mail import FastMail, MessageSchema, MessageType

from fastapi_demo.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@shared_task(name="email.send_welcome")
def send_welcome_email(user_data: dict) -> None:
    mailer = FastMail(settings.mailer_config)
    message = MessageSchema(
        subject="Welcome to fastapi-demo! 🎉",
        recipients=[user_data["email"]],
        template_body={
            "project_name": settings.PROJECT_NAME,
            "user_email": user_data["email"],
            "user_first_name": user_data["first_name"],
        },
        subtype=MessageType.html,
    )
    async_to_sync(mailer.send_message)(message, template_name="new_account.html")


@shared_task(name="email.send_reset")
def send_reset_password_email(user_data: dict, link: str, ttl_minutes: int) -> None:
    mailer = FastMail(settings.mailer_config)
    message = MessageSchema(
        subject="Reset your fastapi-demo password",
        recipients=[user_data["email"]],
        template_body={
            "project_name": settings.PROJECT_NAME,
            "user_email": user_data["email"],
            "user_first_name": user_data["first_name"],
            "link": link,
            "reset_password_token_lifetime_minutes": ttl_minutes,
        },
        subtype=MessageType.html,
    )
    async_to_sync(mailer.send_message)(message, template_name="reset_password.html")


@shared_task(name="email.send_verify")
def send_verify_account_email(user_data: dict, link: str, ttl_minutes: int) -> None:
    mailer = FastMail(settings.mailer_config)
    message = MessageSchema(
        subject="Confirm your fastapi-demo account 🛡️",
        recipients=[user_data["email"]],
        template_body={
            "project_name": settings.PROJECT_NAME,
            "user_email": user_data["email"],
            "user_first_name": user_data["first_name"],
            "link": link,
            "verification_token_lifetime_minutes": ttl_minutes,
        },
        subtype=MessageType.html,
    )
    async_to_sync(mailer.send_message)(message, template_name="verify_account.html")
