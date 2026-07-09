import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from celery.utils.log import get_task_logger

from accounts.utils.mailer import Mailer, MailerError

logger = logging.getLogger("accounts")

mailer = Mailer()


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_email_task(self, subject, message, recipient_list, log_context=""):
    try:
        mailer.send(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
        )
    except MailerError as exc:
        logger.warning(
            f"[{log_context}]: Failed to send email; recipients={recipient_list}",
            exc_info=True,
        )
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(
                f"[{log_context}]: Attempts to send an email message have been exhausted; recipients={recipient_list}",
                exc_info=True,
            )
    except SoftTimeLimitExceeded:
        logger.error(
            f"[{log_context}]: Task timed out (30s+), not retrying; recipients={recipient_list}",
            exc_info=True,
        )
