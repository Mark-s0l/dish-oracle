from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic.edit import FormView

from add_food.forms import AddProductForm
from add_food.services import add_product
from food_hub.models import Category, Company, Country, Product


class AddProductView(FormView):
    template_name = "add_food/add_product.html"
    form_class = AddProductForm

    def form_valid(self, form):
        ean = form.cleaned_data["ean_code"]
        try:
            product = Product.objects.get(ean_code=ean)
        except Product.DoesNotExist:
            api_data = add_product(ean)

            if api_data is None or api_data.get("successful") is False:
                form.add_error("ean_code", api_data.get("error", "Неизвестная ошибка"))
                return render(self.request, self.template_name, {"form": form})

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
                    img_field=api_data.get("save_path"),
                )

        return redirect("rate_food:add_rate", product_id=product.pk)
