from django.shortcuts import render
from django.views.generic.edit import UpdateView
from accounts.models import CustomUser
from accounts.forms import ChangeEmailUser
from django.urls import reverse_lazy

from django.contrib.auth.mixins import LoginRequiredMixin


class UserProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    success_url = reverse_lazy('accounts:profile')
    template_name = "accounts/user_profile.html"
    form_class = ChangeEmailUser
    
    def get_object(self):
        return self.request.user

    
