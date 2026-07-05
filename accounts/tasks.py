from celery import shared_task
from celery.utils.log import get_task_logger
from accounts.utils.mailer import Mailer, MailerError
import logging

logger = logging.getLogger("accounts")

mailer = Mailer()

@shared_task
def send_registration_email_task(user_id, user_email):
    try:
        mailer.send(
            subject="Успешная регистрация",
            message="Вы были успешно зарегистрированы! Если это были не вы, пожалуйста, напишите нам",
            recipient_list=[user_email],
        )
    except MailerError:
        logger.warning(
            f"[SIGN_UP]: Failed to send registration notification email; user={user_id}",
            exc_info=True,
        )