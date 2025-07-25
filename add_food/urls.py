from add_food import views
from django.urls import path

app_name = 'add_food'

urlpatterns = [
    path("", views.AddProductView.as_view(), name="add_product"),
]