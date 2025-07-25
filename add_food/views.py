from food_hub.forms import AddProductForm
from django.views.generic.edit import FormView
from food_hub.models import Product, Country, Company, Category
from add_food.services import fetch_product_data
from django.shortcuts import redirect, render
from django.db import transaction


class AddProductView(FormView):
    template_name = "add_food/add_product.html"
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

        return redirect("food_hub:add_rating", product_id=product.pk)