from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from food_hub.forms import SearchForm, AddProductForm
from food_hub.models import Product, Category, Company, Country
from food_hub.services import fetch_product_data
from django.shortcuts import render


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

def add_product(request, ):
    if request.method == 'POST':
        form = AddProductForm(request.POST)
        if form.is_valid():
            ean_code = form.cleaned_data['ean_code']
            api_response = fetch_product_data(ean_code)
            if api_response is not None:
                try:
                    product = Product.objects.get(ean_code=ean_code)
                    return render(request, 'food_hub/checkproduct.html', {'product': product})
                except Product.DoesNotExist:
                    country_obj, created = Country.objects.get_or_create(name=api_response["country"])
                    company_obj, created = Company.objects.get_or_create(name=api_response["company"],
                                                                country=country_obj)
                    category_obj, created = Category.objects.get_or_create(name=api_response["category"])
                    product = Product.objects.create(name=api_response["name"],
                                            ean_code=form.cleaned_data["ean_code"],
                                            category=category_obj,
                                            company=company_obj)
                    return render(request, 'food_hub/checkproduct.html', {'product': product})
            else:
                error_message = "Извините, в данный момент сервис не доступен. Пожалуйста, попробуйте позже."
                return render(request, 'food_hub/checkproduct.html', {'error_message': error_message})
    form = AddProductForm()
    return render(request, 'food_hub/add_product.html', {'form': form})