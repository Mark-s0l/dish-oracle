from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from food_hub.forms import SearchForm, AddProductForm
from food_hub.models import Product, Category, Company, Country
from food_hub.services import fetch_product_data
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.db import transaction


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

class AddProductView(FormView):
    template_name = 'food_hub/add_product.html'
    form_class = AddProductForm

    def _show_product(self, context):
        return render(self.request, 'food_hub/checkproduct.html', context)

    def form_valid(self, form):
        ean = form.cleaned_data['ean_code']
        try:
            product = Product.objects.get(ean_code=ean)
            return self._show_product({'product': product})
        except Product.DoesNotExist:
            pass

        api_data = fetch_product_data(ean)
        if not api_data:
            return self._show_product({'error_message': "Сервис недоступен"})

        with transaction.atomic():
            country, _  = Country.objects.get_or_create(name=api_data['country'])
            company, _  = Company.objects.get_or_create(
                name=api_data['company'], country=country
            )
            category, _ = Category.objects.get_or_create(name=api_data['category'])

            product = Product.objects.create(
                name=api_data['name'],
                ean_code=ean,
                category=category,
                company=company,
                img_field=api_data.get('image_path') 
            )

        return self._show_product({'product': product})