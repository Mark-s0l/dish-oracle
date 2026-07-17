import pytest
from django.contrib.auth import get_user_model


User = get_user_model()

@pytest.fixture
def save_and_clean(db):
    def _save(obj):
        obj.full_clean()
        obj.save()
        return obj

    return _save

@pytest.fixture(scope="class")
def user2(django_db_blocker):
    with django_db_blocker.unblock():
        user = User.objects.create_user(username="testuser2", email="user2_email@inbox.com", password="testpass")
    yield user
    with django_db_blocker.unblock():
        user.delete()
