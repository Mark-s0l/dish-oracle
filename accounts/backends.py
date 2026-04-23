from accounts.models import CustomUser
from django.contrib.auth.backends import ModelBackend

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            login = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            login = CustomUser.objects.get(email=username)
        is_current_password = login.check_password(raw_password=password)
        if is_current_password:
            return login
        else:
            return None