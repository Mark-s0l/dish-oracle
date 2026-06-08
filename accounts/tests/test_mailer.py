from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPException
from unittest.mock import MagicMock, patch

import pytest
from django.core.mail.backends.smtp import EmailBackend

from django.conf import settings
from accounts.utils.mailer import (Mailer, MailerAuthError,
                                   MailerConnectionError, MailerError)


class TestCheckConnection:

    @patch("accounts.utils.mailer.get_connection")
    def test_smtp_success(self, mock_get_connection):
        mock_conn = MagicMock(spec=EmailBackend)
        mock_get_connection.return_value = mock_conn

        result = Mailer.check_connection()

        assert result is True
        mock_conn.open.assert_called_once_with()
        mock_conn.close.assert_called_once_with()

    @patch("accounts.utils.mailer.get_connection")
    def test_non_smtp_backend(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn

        result = Mailer.check_connection()

        assert result is False
        mock_conn.open.assert_not_called()
        mock_conn.close.assert_not_called()

    @patch("accounts.utils.mailer.get_connection")
    @patch.object(Mailer, "_handle_error")
    def test_open_raises_calls_handle_error(
        self, mock_handle_error, mock_get_connection
    ):
        mock_conn = MagicMock(spec=EmailBackend)
        mock_conn.open.side_effect = Exception("wooops")
        mock_get_connection.return_value = mock_conn

        Mailer.check_connection()

        mock_handle_error.assert_called_once()


class TestSend:

    @patch("accounts.utils.mailer.send_mail")
    def test_success(self, mock_send):
        mailer = Mailer()
        mailer.send(
            subject="TestSubject",
            message="message",
            recipient_list=["user_inbox@inbox.com"],
        )
        mock_send.assert_called_once_with(
            subject="TestSubject",
            message="message",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["user_inbox@inbox.com"],
            html_message=None,
        )

    @patch("accounts.utils.mailer.send_mail")
    @patch.object(Mailer, "_handle_error")
    def test_smtp_exception(self, mock_handle_error, mock_send):
        mailer = Mailer()
        mock_send.side_effect = Exception("wooops")
        mailer.send(
            subject="TestSubject",
            message="message",
            recipient_list=["user_inbox@inbox.com"],
        )

        mock_handle_error.assert_called_once()


class TestHandleError:

    @pytest.mark.parametrize(
        "input_exc, excepted_exc",
        [
            (SMTPAuthenticationError(535, "Auth failed"), MailerAuthError),
            (SMTPConnectError(421, "Connection failed"), MailerConnectionError),
            (SMTPException("SMTP error"), MailerError),
            (Exception("Unexpected"), MailerError),
            ],
    )
    def test_exception_handle_error(self, input_exc, excepted_exc):
        with pytest.raises(excepted_exc):
            Mailer._handle_error(input_exc)

