from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class AddFoodConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "add_food"

    def ready(self):
        from django.conf import settings
        if not settings.EAN_DB_JWT or not settings.EAN_DB_API_URL:
            raise ImproperlyConfigured("Не заданы параметры EAN_DB_JWT или EAN_DB_API_URL")
        elif settings.EAN_DB_API_URL[-1] != "/":
            raise ImproperlyConfigured("Неправильно задан параметр EAN_DB_API_URL - Отстствует '/' в конце строки")