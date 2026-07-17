import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dish_oracle.settings")

app = Celery("dish_oracle")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()