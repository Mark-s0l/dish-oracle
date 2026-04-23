from django.db import DatabaseError, IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.generic.edit import FormView

from add_food.forms import AddProductForm
from add_food.services import ApiError, add_product
from food_hub.models import Category, Company, Country, Product

from django.contrib.auth.mixins import LoginRequiredMixin


class AddProductView(LoginRequiredMixin, FormView):
    template_name = "add_food/add_product.html"
    form_class = AddProductForm

    def _get_or_create_product(self, ean: str, api_data: dict) -> Product:
        with transaction.atomic():
            country, _ = Country.objects.get_or_create(name=api_data["country"])
            company, _ = Company.objects.get_or_create(
                name=api_data["company"], country=country
            )
            category, _ = Category.objects.get_or_create(name=api_data["category"])
            try:
                with transaction.atomic():
                    product, _ = Product.objects.get_or_create(
                        ean_code=ean,
                        defaults={
                            "name": api_data["name"],
                            "category": category,
                            "company": company,
                            "img_field": api_data["save_path"],
                        },
                    )
            except IntegrityError:
                product = Product.objects.get(ean_code=ean)
        return product

    def form_valid(self, form):
        ean = form.cleaned_data["ean_code"]

        try:
            product = Product.objects.get(ean_code=ean)
        except Product.DoesNotExist:
            try:
                api_data = add_product(ean)
            except ApiError as error:
                form.add_error("ean_code", str(error))
                return render(self.request, self.template_name, {"form": form})

            try:
                product = self._get_or_create_product(ean, api_data)
            except DatabaseError:
                form.add_error("ean_code", "Ошибка записи данных, попробуйте позже")
                return render(self.request, self.template_name, {"form": form})

        self.request.session["current_product_id"] = product.pk
        return redirect("rate_food:add_rate")
