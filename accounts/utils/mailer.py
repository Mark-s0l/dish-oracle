import logging
from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPException

from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger("accounts")


class MailerError(Exception):
    pass


class MailerAuthError(MailerError):
    pass


class MailerConnectionError(MailerError):
    pass


class Mailer:
    @classmethod
    def check_connection(cls) -> bool:
        """Check SMTP connection availability on application startup.
    
        Returns:
            bool: True if connection successful, False if non-SMTP backend.
        
        Raises:
            MailerError: If the connection fails.
        """
        connection = get_connection()
        if isinstance(connection, EmailBackend):
            try:
                connection.open()
                connection.close()
                logger.info("[MAILER] SMTP connection successful")
                return True
            except Exception as exc:
                cls._handle_error(exc)
        else:
            logger.warning("[MAILER] Non-SMTP backend, connection check skipped")
            return False

    def send(self, subject: str, recipient_list: list[str], message: str, html_message: str | None = None) -> None:
        """Send an email message.
    
        Args:
            subject (str): Email subject.
            recipient_list (list): List of recipient email addresses.
            message (str): Plain text message body.
            html_message (str, optional): HTML message body. Defaults to None.
        
        Raises:
            MailerError: If the email could not be sent.
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
            )
        except Exception as exc:
            self._handle_error(exc)

    @staticmethod
    def _handle_error(exc) -> None:

        if isinstance(exc, SMTPAuthenticationError):
            logger.error("[MAILER] Invalid authorization data", exc_info=True)
            raise MailerAuthError("Invalid authorization data") from exc

        if isinstance(exc, SMTPConnectError):
            logger.error(f"[MAILER] Couldn't connect host={
                settings.EMAIL_HOST} port={settings.EMAIL_PORT
                }", exc_info=True)
            raise MailerConnectionError("Couldn't connect to SMTP") from exc

        if isinstance(exc, SMTPException):
            logger.error("[MAILER] SMTP unknown error", exc_info=True)
            raise MailerError("SMTP unknown error") from exc
        logger.error("[MAILER] Unexpected error", exc_info=True)
        raise MailerError("Unexpected mailing error") from exc
