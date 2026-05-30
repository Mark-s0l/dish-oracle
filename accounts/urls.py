from django.urls import path

from accounts import views

from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('change_password/verification', views.VerificationChangePassword.as_view(), name='verification_change_password')
]
