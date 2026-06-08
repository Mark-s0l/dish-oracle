from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from accounts.forms import ChangeEmailUser


User = get_user_model()

class TestUserProfileView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("accounts:profile")
        cls.user = User.objects.create_user(username="testuser", password="testpassword123")

    def setUp(self):
        self.client.force_login(self.user)

    def test_url_success(self):
        response = self.client.get(self.url) 
        self.assertEqual(response.status_code, 200)

    def test_unauth_user_url_request(self):
        self.client.logout()
        response = self.client.get(self.url) 
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_correct_template_used(self):
        response = self.client.get(self.url) 
        self.assertTemplateUsed(response, template_name="accounts/user_profile.html")

    def test_correct_form_used(self):
        response = self.client.get(self.url) 
        self.assertIsInstance(response.context['form'], ChangeEmailUser)

    