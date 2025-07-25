from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from food_hub import views

app_name = 'food_hub'

urlpatterns = [
    path("", views.ProductsView.as_view(), name="product_list"),
    path(
        "list/tag/<slug:slug>/",
        views.ProductsView.as_view(),
        name="product_list_by_tag",
    ),
    path('list/add/', views.AddProductView.as_view(), name='add_product'),
    path('list/add_rating/<int:product_id>/', views.AddRatingView.as_view(), name='add_rating'),
    path('list/save_rating/', views.SaveRatingView.as_view(), name='save_rating'),

]

# Для разработки: отдача медиафайлов через Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
