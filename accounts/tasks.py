import logging

from celery import shared_task
from celery.utils.log import get_task_logger

from accounts.utils.mailer import Mailer, MailerError

logger = logging.getLogger("accounts")

mailer = Mailer()


@shared_task
def send_email_task(subject, message, recipient_list, log_context=""):
    try:
        mailer.send(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
        )
    except MailerError:
        logger.warning(
            f"[{log_context}]: Failed to send email; recipients={recipient_list}",
            exc_info=True,
        )
