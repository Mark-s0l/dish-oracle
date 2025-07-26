from rate_food import views
from django.urls import path

app_name = 'rate_food'

urlpatterns = [
    path("<int:product_id>/", views.AddRatingView.as_view(), name="add_rate"),
    path("add_tags/", views.SaveRatingView.as_view(), name="add_tags"),
]