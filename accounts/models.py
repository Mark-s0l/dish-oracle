from django.contrib.auth.models import AbstractUser
from django.db import models
from django.templatetags.static import static


class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def get_avatar(self):
        if self.avatar:
            return self.avatar.url
        return static("icons/default_image_profile.svg")
