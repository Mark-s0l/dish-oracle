from django.urls import path

from accounts import views
from accounts.forms import LoginForm
from django.contrib.auth.views import LoginView

from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('change_password/verification', views.VerificationChangePassword.as_view(), name='verification_change_password'),
    path('sign_up/', views.SignUpUser.as_view(), name='sign_up_user')
]
