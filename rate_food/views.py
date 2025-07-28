from django.views import View
from django.shortcuts import get_object_or_404, redirect, render
from food_hub.models import (Product,
                             ProductRating, TasteTag)
from rate_food.tags_choose import choose_taste_tags
from django.db import transaction


class AddRatingView(View):
    def get(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs["product_id"])
        context = {"product": product}
        return render(request, "rate_food/add_rating.html", context)

    def post(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs["product_id"])
        rate = int(request.POST.get("rate"))
        category = product.category.name
        tags = choose_taste_tags(rate, category)
        return render(request,
            "rate_food/partials/tag_selector.html",
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

        return redirect("food_hub:product_list")
