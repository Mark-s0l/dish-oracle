from unittest.mock import call, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.test import TestCase
from django.urls import reverse, reverse_lazy

from accounts.forms import ChangeEmailUser
from accounts.tests.factories import UserFactory
from accounts.utils.cache_manager import CacheError
from accounts.utils.mailer import Mailer, MailerError

User = get_user_model()


class ViewBaseMixin:
    url = None
    template_name = None
    form_class = None
    login_url_name = "accounts:login"

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        super().setUpTestData()

    def setUp(self):
        self.user.refresh_from_db()
        self.client.force_login(self.user)

    def test_url_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unauth_user_request(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"{reverse(self.login_url_name)}?next={self.url}"
        )

    def test_correct_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, template_name=self.template_name)

    def test_correct_form_used(self):
        response = self.client.get(self.url)
        self.assertIsInstance(response.context["form"], self.form_class)


class TestUserProfileView(ViewBaseMixin, TestCase):
    template_name = "accounts/user_profile.html"
    form_class = ChangeEmailUser

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse("accounts:profile")


class TestChangePasswordView(ViewBaseMixin, TestCase):

    template_name = "accounts/change_password.html"
    form_class = PasswordChangeForm
    success_url = reverse_lazy("accounts:verification_change_password")
    except_url = reverse("accounts:profile")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse("accounts:change_password")

    def test_form_kwargs_contains_user(self):
        request = self.client.get(self.url)
        self.assertEqual(request.context["form"].user, self.user)

    @patch("accounts.views.secrets.randbelow", return_value=42)
    @patch("accounts.views.make_password", side_effect=["hashed_code", "hashed_pw"])
    @patch("accounts.views.mailer")
    @patch("accounts.views.CacheManager")
    def test_happy_path(
        self, mock_cache_cls, mock_mailer, mock_make_password, mock_randbelow
    ):
        mock_cache = mock_cache_cls.return_value
        mock_cache.cache_get.return_value = None

        data = {
            "old_password": "testpass123",
            "new_password1": "newpass456!",
            "new_password2": "newpass456!",
        }

        response = self.client.post(self.url, data)

        mock_cache.cache_get.assert_called_once_with(key="password_change_attempt")

        self.assertRedirects(response, self.success_url, fetch_redirect_response=False)

        mock_cache.cache_set.assert_has_calls(
            [
                call(
                    "password_change",
                    {
                        "hash": "hashed_pw",
                        "code": "hashed_code",
                        "session_key": self.client.session.session_key,
                    },
                    timeout=300,
                ),
                call("password_change_attempt", {"attempt": 1}, timeout=3600),
            ]
        )

        mock_make_password.assert_any_call("000042")

        mock_mailer.send.assert_called_once_with(
            subject="Подтверждение смены пароля",
            message="Ваш код: 000042",
            recipient_list=[self.user.email],
        )

    @patch("accounts.views.CacheManager")
    def test_get_attempt_cache_error(self, mock_cache_cls):
        mock_cache = mock_cache_cls.return_value
        mock_cache.cache_get.side_effect = CacheError

        data = {
            "old_password": "testpass123",
            "new_password1": "newpass456!",
            "new_password2": "newpass456!",
        }

        response = self.client.post(self.url, data)

        mock_cache.cache_get.assert_called_once_with(key="password_change_attempt")

        self.assertRedirects(response, self.except_url, fetch_redirect_response=False)

    @patch("accounts.views.CacheManager")
    def test_max_attempt(self, mock_cache_cls):
        mock_cache = mock_cache_cls.return_value
        data = {
            "old_password": "testpass123",
            "new_password1": "newpass456!",
            "new_password2": "newpass456!",
        }
        for attempt in [5, 6]:
            with self.subTest(attempt=attempt):
                mock_cache.cache_get.return_value = {"attempt": attempt}
                response = self.client.post(self.url, data)
                messages_list = list(response.wsgi_request._messages)
                self.assertEqual(
                    str(messages_list[0]), "Слишком много попыток, попробуйте позже"
                )
                self.assertRedirects(
                    response, self.except_url, fetch_redirect_response=False
                )

    @patch("accounts.views.secrets.randbelow", return_value=42)
    @patch("accounts.views.make_password", side_effect=["hashed_code", "hashed_pw"])
    @patch("accounts.views.CacheManager")
    def test_set_cache_error(self, mock_cache_cls, mock_make_password, mock_randbelow):
        mock_cache = mock_cache_cls.return_value
        mock_cache.cache_set.side_effect = CacheError
        mock_cache.cache_get.return_value = None

        data = {
            "old_password": "testpass123",
            "new_password1": "newpass456!",
            "new_password2": "newpass456!",
        }

        response = self.client.post(self.url, data)

        mock_cache.cache_get.assert_called_once_with(key="password_change_attempt")

        mock_cache.cache_set.assert_called_once()

        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(str(messages_list[0]), "Произошла ошибка. Попробуйте позже")
        self.assertRedirects(response, self.except_url, fetch_redirect_response=False)

    @patch("accounts.views.secrets.randbelow", return_value=42)
    @patch("accounts.views.make_password", side_effect=["hashed_code", "hashed_pw"])
    @patch("accounts.views.mailer")
    @patch("accounts.views.CacheManager")
    def test_mailer_error(
        self, mock_cache_cls, mock_mailer, mock_make_password, mock_randbelow
    ):
        mock_cache = mock_cache_cls.return_value
        mock_cache.cache_get.return_value = None
        mock_mailer.send.side_effect = MailerError

        data = {
            "old_password": "testpass123",
            "new_password1": "newpass456!",
            "new_password2": "newpass456!",
        }

        response = self.client.post(self.url, data)

        mock_cache.cache_get.assert_called_once_with(key="password_change_attempt")

        mock_cache.cache_set.assert_has_calls(
            [
                call(
                    "password_change",
                    {
                        "hash": "hashed_pw",
                        "code": "hashed_code",
                        "session_key": self.client.session.session_key,
                    },
                    timeout=300,
                ),
                call("password_change_attempt", {"attempt": 1}, timeout=3600),
            ]
        )

        mock_make_password.assert_any_call("000042")

        mock_mailer.send.assert_called_once()

        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(
            str(messages_list[0]), "Ошибка отправки письма. Попробуйте позже"
        )
        self.assertRedirects(response, self.except_url, fetch_redirect_response=False)

    def test_form_invalid_rerenders_form(self):
        data = {
            "old_password": "wrongpassword",
            "new_password1": "newpass456!",
            "new_password2": "newpass456!",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)
        self.assertFalse(response.context["form"].is_valid())
