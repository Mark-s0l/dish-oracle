from django.urls import path

from search_hub import views

app_name = "search_hub"

urlpatterns = [
    path("", views.ProductSearchView.as_view(), name="product_search"),
]
