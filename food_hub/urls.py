from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from food_hub import views

urlpatterns = [
    path("list/", views.ProductsView.as_view(), name="product_list"),
    path(
        "list/tag/<slug:slug>/",
        views.ProductsView.as_view(),
        name="product_list_by_tag",
    ),
]

# Для разработки: отдача медиафайлов через Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
