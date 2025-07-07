from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.generic import ListView
from django.views.generic.base import TemplateView

from food_hub.models import Product

from .forms import SearchForm
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


class ProductSearchView(ListView):
    model = Product
    template_name = "food_hub/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        self.form = SearchForm(self.request.GET)
        if self.form.is_valid():
            query = self.form.cleaned_data["query"]
            search_vector = SearchVector("name", "company", config="russian")
            search_query = SearchQuery(query, config="russian")
            return (
                Product.objects.annotate(
                    search=search_vector, rank=SearchRank(search_vector, search_query)
                )
                .filter(search=search_query)
                .order_by("-rank")
            )
        else:
            return Product.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form
        context["query"] = self.request.GET.get("query", "")
        return context
