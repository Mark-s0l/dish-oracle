from django.urls import path

from accounts import views

from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
]
