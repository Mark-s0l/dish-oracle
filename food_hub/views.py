from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from food_hub.models import Product, ProductRating
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, Prefetch



class ProductsView(LoginRequiredMixin, TemplateView):
    template_name = "food_hub/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.select_related('company').prefetch_related(
            Prefetch('ratings', queryset=ProductRating.objects.filter(
                user=self.request.user
                ).prefetch_related('taste_tags'), to_attr='user_ratings')
            ).filter(ratings__user=self.request.user)
        context["products"] = products
        return context
