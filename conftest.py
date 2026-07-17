from django.contrib.auth import get_user_model
import pytest

User = get_user_model()

@pytest.fixture(scope="module")
def user(django_db_blocker):
    with django_db_blocker.unblock():
        user = User.objects.create_user(username="testuser", email="user_email@inbox.com", password="testpass")
    yield user
    with django_db_blocker.unblock():
        user.delete()

