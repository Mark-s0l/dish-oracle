from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVector)
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from food_hub.forms import AddProductForm, SearchForm
from food_hub.models import (Category, Company, Country, Product,
                             ProductRating, TasteTag)
from food_hub.utils.services import fetch_product_data
from food_hub.utils.tags_choose import choose_taste_tags


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

class AddProductView(FormView):
    template_name = "food_hub/add_product.html"
    form_class = AddProductForm

    def form_valid(self, form):
        ean = form.cleaned_data["ean_code"]
        try:
            product = Product.objects.get(ean_code=ean)
        except Product.DoesNotExist:
            api_data = fetch_product_data(ean)
            if not api_data:
                return render(
                    self.request,
                    "food_hub/add_product.html",
                    {"error_message": "Сервис недоступен"},
                )

            with transaction.atomic():
                country, _ = Country.objects.get_or_create(name=api_data["country"])
                company, _ = Company.objects.get_or_create(
                    name=api_data["company"], country=country
                )
                category, _ = Category.objects.get_or_create(name=api_data["category"])

                product = Product.objects.create(
                    name=api_data["name"],
                    ean_code=ean,
                    category=category,
                    company=company,
                    img_field=api_data.get("image_path"),
                )

        return redirect("add_rating", product_id=product.pk)


class AddRatingView(View):
    def get(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs["product_id"])
        context = {"product": product}
        return render(request, "food_hub/add_rating.html", context)

    def post(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs["product_id"])
        rate = int(request.POST.get("rate"))
        category = product.category.name
        tags = choose_taste_tags(rate, category)
        return render(
            request,
            "food_hub/partials/tag_selector.html",
            {"tags": tags, "product_id": product.pk, "rate": rate},
        )


class SaveRatingView(View):
    def post(self, request):
        product_id = request.POST.get("product_id")
        rate = int(request.POST.get("rate"))
        selected_tags = request.POST.getlist("tags")

        product = get_object_or_404(Product, pk=product_id)
        tags = TasteTag.objects.filter(pk__in=selected_tags)

        with transaction.atomic():
            rating_obj = ProductRating.objects.create(product=product, rate=rate)
            rating_obj.taste_tags.set(tags)

        return redirect("product_list")
