from django.urls import path

from food_hub import views

app_name = 'food_hub'

urlpatterns = [
    path("", views.ProductsView.as_view(), name="product_list"),
]
