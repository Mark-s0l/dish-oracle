from rate_food import views
from django.urls import path

app_name = 'rate_food'

urlpatterns = [
    path("add_rate/", views.RateProductView.as_view(), name="add_rate"),
    path("save_rate/", views.SaveRatingView.as_view(), name="save_rate"),
]