from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    avatar = models.ImageField(default="default_image_profile", upload_to="static/icons")

