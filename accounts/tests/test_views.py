from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.test import TestCase
from django.urls import reverse

from accounts.forms import ChangeEmailUser
from accounts.tests.factories import UserFactory

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

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse("accounts:change_password")
