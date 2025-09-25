from django.views.generic.base import TemplateView
from food_hub.models import Product
from django.contrib.postgres.aggregates import ArrayAgg


class ProductsView(TemplateView):
    template_name = "food_hub/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.select_related('company').annotate(
            tag_names=ArrayAgg('ratings__taste_tags__name', distinct=True))
        context["products"] = products
        return context
