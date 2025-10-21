from search_hub import views
from django.urls import path

app_name = 'search_hub'

urlpatterns = [
    path("", views.ProductSearchView.as_view(), name="product_search"),
]
