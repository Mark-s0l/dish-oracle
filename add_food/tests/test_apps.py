import pytest
from django.core.exceptions import ImproperlyConfigured
from add_food.apps import AddFoodConfig


def test_ready_success(settings):
    settings.EAN_DB_JWT = "some_token"
    settings.EAN_DB_API_URL = "https://example.com/api/"
    config = AddFoodConfig("add_food", __import__("add_food"))
    config.ready()


def test_ready_missing_jwt(settings):
    settings.EAN_DB_JWT = ""
    settings.EAN_DB_API_URL = "https://example.com/api/"
    config = AddFoodConfig("add_food", __import__("add_food"))
    with pytest.raises(ImproperlyConfigured, match="EAN_DB_JWT"):
        config.ready()


def test_ready_missing_api_url(settings):
    settings.EAN_DB_JWT = "some_token"
    settings.EAN_DB_API_URL = ""
    config = AddFoodConfig("add_food", __import__("add_food"))
    with pytest.raises(ImproperlyConfigured, match="EAN_DB_API_URL"):
        config.ready()


def test_ready_api_url_missing_trailing_slash(settings):
    settings.EAN_DB_JWT = "some_token"
    settings.EAN_DB_API_URL = "https://example.com/api"
    config = AddFoodConfig("add_food", __import__("add_food"))
    with pytest.raises(ImproperlyConfigured, match="'/'"):
        config.ready()