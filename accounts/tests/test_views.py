from unittest.mock import MagicMock, call, patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse, reverse_lazy

from accounts.forms import ChangeEmailUser, ChangePasswordForm, EmailVerificationCode
from accounts.tasks import send_email_task
from accounts.tests.factories import UserFactory
from accounts.utils.cache_manager import CacheError
from accounts.utils.mailer import Mailer, MailerError
from accounts.views import MAX_ATTEMPTS

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
    form_class = ChangePasswordForm
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


class TestVerificationChangePassword(ViewBaseMixin, TestCase):
    template_name = "accounts/verification_email_code.html"
    form_class = EmailVerificationCode
    profile_url = reverse_lazy("accounts:profile")
    change_password_url = reverse("accounts:change_password")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse("accounts:verification_change_password")

    def setUp(self):
        super().setUp()
        patcher = patch("accounts.views.CacheManager")
        self.mock_cache_cls = patcher.start()
        self.addCleanup(patcher.stop)

    def _post(self):
        response = self.client.post(self.url)
        self.mock_cache_cls.assert_called_once_with(self.user.id)
        return response

    def test_happy_dispatch(self):
        mock_cache = self.mock_cache_cls.return_value
        mock_cache.cache_get.return_value = "valid_data"

        response = self._post()

        mock_cache.cache_get.assert_called_once_with("password_change")

    def test_cache_error_dispatch(self):
        mock_cache = self.mock_cache_cls.return_value
        mock_cache.cache_get.side_effect = CacheError

        response = self._post()

        mock_cache.cache_get.assert_called_once_with("password_change")
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(str(messages_list[0]), "Произошла ошибка. Попробуйте позже")
        self.assertRedirects(response, self.profile_url, fetch_redirect_response=False)

    def test_not_data_dispatch(self):
        mock_cache = self.mock_cache_cls.return_value
        mock_cache.cache_get.return_value = None

        response = self._post()

        mock_cache.cache_get.assert_called_once_with("password_change")
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(str(messages_list[0]), "Сессия истекла. Попробуйте еще раз")
        self.assertRedirects(
            response, self.change_password_url, fetch_redirect_response=False
        )

    @patch("accounts.views.update_session_auth_hash")
    @patch("accounts.views.check_password")
    @patch("accounts.tasks.send_email_task.delay")
    def test_form_valid_happy_path(
        self, mock_delay, mock_check_password, mock_update_session
    ):
        mock_cache_manager = self.mock_cache_cls.return_value
        session_key = self.client.session.session_key

        cache_data = {
            "password_change": {
                "code": "hashed_code",
                "hash": "new_hashed_password",
                "session_key": session_key,
            },
            "password_change_attempt": None,
        }
        mock_cache_manager.cache_get.side_effect = cache_data.get
        mock_check_password.return_value = True

        response = self.client.post(self.url, data={"code": "123456"})

        self.mock_cache_cls.assert_called_with(self.user.id)

        mock_check_password.assert_called_once_with("123456", "hashed_code")

        self.user.refresh_from_db()
        self.assertEqual(self.user.password, "new_hashed_password")

        mock_update_session.assert_called_once_with(response.wsgi_request, self.user)
        mock_cache_manager.cache_del.assert_called_once_with("password_change")
        mock_delay.assert_called_once()

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("accounts:profile"), fetch_redirect_response=False
        )

    def test_form_valid_cache_error(self):
        mock_cache_manager = self.mock_cache_cls.return_value
        mock_cache_manager.cache_get.side_effect = [
            MagicMock(),  # To successfully complete the dispatch
            CacheError,
        ]

        response = self.client.post(self.url, data={"code": "123456"})

        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(str(messages_list[0]), "Произошла ошибка. Попробуйте позже")
        self.assertRedirects(
            response, reverse("accounts:profile"), fetch_redirect_response=False
        )

    @patch("accounts.tasks.send_email_task.delay")
    def test_form_valid_attempt_exceeded(self, mock_delay):
        mock_cache_manager = self.mock_cache_cls.return_value
        cache_data = {
            "password_change": {
                "code": "hashed_code",
                "hash": "new_hashed_password",
                "session_key": "x",
            },
            "password_change_attempt": {"attempt": MAX_ATTEMPTS + 1},
        }
        mock_cache_manager.cache_get.side_effect = cache_data.get

        response = self.client.post(self.url, data={"code": "123456"})

        mock_delay.assert_called_once()
        mock_cache_manager.cache_del.assert_called_once_with("password_change")
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(
            str(messages_list[0]), "Слишком много ошибок, попробуйте позже"
        )
        self.assertRedirects(response, self.profile_url, fetch_redirect_response=False)

    @patch("accounts.views.mailer")
    def test_form_valid_attempt_exceeded_mailer_error(self, mock_mailer):
        mock_cache_manager = self.mock_cache_cls.return_value
        cache_data = {
            "password_change": {
                "code": "hashed_code",
                "hash": "new_hashed_password",
                "session_key": "x",
            },
            "password_change_attempt": {"attempt": MAX_ATTEMPTS + 1},
        }
        mock_cache_manager.cache_get.side_effect = cache_data.get
        mock_mailer.send.side_effect = MailerError

        response = self.client.post(self.url, data={"code": "123456"})

        mock_cache_manager.cache_del.assert_called_once_with("password_change")
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(
            str(messages_list[0]), "Слишком много ошибок, попробуйте позже"
        )
        self.assertRedirects(response, self.profile_url, fetch_redirect_response=False)

    def test_form_valid_no_data(self):
        # data expires after passing dispatch
        mock_cache_manager = self.mock_cache_cls.return_value
        mock_cache_manager.cache_get.side_effect = [
            {
                "code": "x",
                "hash": "x",
                "session_key": "x",
            },  # dispatch: cache_get("password_change")
            None,  # form_valid: cache_get("password_change_attempt")
            None,  # form_valid: cache_get("password_change")
        ]

        response = self.client.post(self.url, data={"code": "123456"})

        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(str(messages_list[0]), "Сессия истекла. Попробуйте еще раз")
        self.assertRedirects(
            response, self.change_password_url, fetch_redirect_response=False
        )

    @patch("accounts.views.check_password")
    def test_form_valid_wrong_code(self, mock_check_password):
        mock_cache_manager = self.mock_cache_cls.return_value
        cache_data = {
            "password_change": {
                "code": "hashed_code",
                "hash": "new_hashed_password",
                "session_key": "x",
            },
            "password_change_attempt": None,
        }
        mock_cache_manager.cache_get.side_effect = cache_data.get
        mock_check_password.return_value = False

        response = self.client.post(self.url, data={"code": 999999})

        mock_check_password.assert_called_once_with("999999", "hashed_code")
        mock_cache_manager.cache_set.assert_called_once_with(
            "password_change_attempt", {"attempt": 1}, timeout=3600
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)

    @patch("accounts.views.check_password")
    def test_form_valid_wrong_code_cache_error(self, mock_check_password):
        mock_cache_manager = self.mock_cache_cls.return_value
        cache_data = {
            "password_change": {
                "code": "hashed_code",
                "hash": "new_hashed_password",
                "session_key": "x",
            },
            "password_change_attempt": None,
        }
        mock_cache_manager.cache_get.side_effect = cache_data.get
        mock_check_password.return_value = False
        mock_cache_manager.cache_set.side_effect = CacheError

        response = self.client.post(self.url, data={"code": "999999"})
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages_list[0]), "Произошла ошибка. Попробуйте позже")
        self.assertRedirects(response, self.profile_url, fetch_redirect_response=False)

    @patch("accounts.views.check_password")
    def test_form_valid_session_key_mismatch(self, mock_check_password):
        mock_cache_manager = self.mock_cache_cls.return_value
        cache_data = {
            "password_change": {
                "code": "hashed_code",
                "hash": "new_hashed_password",
                "session_key": "wrong_session_key",
            },
            "password_change_attempt": None,
        }
        mock_cache_manager.cache_get.side_effect = cache_data.get
        mock_check_password.return_value = True

        response = self.client.post(self.url, data={"code": "123456"})

        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(str(messages_list[0]), "Сессия истекла. Попробуйте еще раз")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.template_name)

    @patch("accounts.views.update_session_auth_hash")
    @patch("accounts.views.check_password")
    @patch("accounts.views.mailer")
    def test_form_valid_mailer_error_on_success(
        self, mock_mailer, mock_check_password, mock_update_session
    ):
        mock_cache_manager = self.mock_cache_cls.return_value
        session_key = self.client.session.session_key
        cache_data = {
            "password_change": {
                "code": "hashed_code",
                "hash": "new_hashed_password",
                "session_key": session_key,
            },
            "password_change_attempt": None,
        }
        mock_cache_manager.cache_get.side_effect = cache_data.get
        mock_check_password.return_value = True
        mock_mailer.send.side_effect = MailerError

        response = self.client.post(self.url, data={"code": "123456"})

        self.user.refresh_from_db()
        self.assertEqual(self.user.password, "new_hashed_password")
        mock_cache_manager.cache_del.assert_called_once_with("password_change")
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(str(messages_list[0]), "Пароль успешно изменен")
        self.assertRedirects(response, self.profile_url, fetch_redirect_response=False)
