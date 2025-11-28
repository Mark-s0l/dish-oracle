from django.urls import path

from add_food import views

app_name = "add_food"

urlpatterns = [
    path("", views.AddProductView.as_view(), name="add_product"),
]
