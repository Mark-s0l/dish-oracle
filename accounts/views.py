from django.shortcuts import render
from django.views.generic.base import TemplateView
from accounts.models import CustomUser

from django.contrib.auth.mixins import LoginRequiredMixin


class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/user_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_info"] = self.request.user   
        return context
        
    
