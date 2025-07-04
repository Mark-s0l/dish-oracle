from django.shortcuts import render
from django.views.generic.base import TemplateView

from .models import Product


class ProductsView(TemplateView):
    template_name = "food_hub/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.prefetch_related("ratings__taste_tags")
        tag_slug = self.kwargs.get("slug")
        if tag_slug:
            products = products.filter(ratings__taste_tags__slug=tag_slug)
        context["products"] = products
        return context
