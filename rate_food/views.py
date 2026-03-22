import logging

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django_htmx.http import HttpResponseClientRedirect

from food_hub.models import Product, ProductRating, TasteTag
from rate_food.forms import RatingForm, TasteTagForm
from rate_food.tags_choose import choose_taste_tags

logger = logging.getLogger("rate_food")


def get_product_from_session(request, select_category=False):
    product_id = request.session.get("current_product_id")
    if product_id is None:
        logger.warning("[Cookie] Product id is not found")
        messages.error(request, "Сессия истекла. Начните заново")
        return None, True
    try:
        if select_category:
            product = Product.objects.select_related("category").get(pk=product_id)
        else:
            product = Product.objects.only("id").get(pk=product_id)
    except Product.DoesNotExist:
        logger.warning(f"[DB] Product with pk = {product_id} is not found")
        request.session.pop("current_product_id", None)
        request.session.pop("rate", None)
        messages.error(request, "Продукт не найден. Начните заново")
        return None, True
    return product, None


def is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


class RateProductView(View):
    template_name = "rate_food/add_rating.html"

    def get(self, request):
        rate_form = RatingForm()

        product, error = get_product_from_session(request)
        if error:
            if is_htmx(request):
                return HttpResponseClientRedirect(reverse("add_food:add_product"))
            return redirect("add_food:add_product")

        context = {"product": product, "rate_form": rate_form}

        if is_htmx(request):
            logger.info("[S1] HTMX — load rate_selector")
            return render(request, "rate_food/partials/rate_selector.html", context)
        logger.info("[S1] User on Stage 1")
        return render(request, "rate_food/add_rating.html", context)

    def post(self, request):

        product, error = get_product_from_session(request, select_category=True)
        if error:
            if is_htmx(request):
                return HttpResponseClientRedirect(reverse("add_food:add_product"))
            return redirect("add_food:add_product")

        rate_form = RatingForm(request.POST)  # Bind POST data to the form

        if not rate_form.is_valid():
            logger.warning("[RATE] RatingForm is not valid")
            context = {
                "product": product,
                "rate_form": rate_form,
            }
            return render(request, "rate_food/partials/rate_selector.html", context)

        rate = rate_form.cleaned_data["rate"]
        request.session["rate"] = rate  # Save rate to session

        tags_form = TasteTagForm()
        # Load filtered tags based on rate and category

        unique_tags = choose_taste_tags(rate, product.category)
        if not unique_tags.exists():  # No tags available for this category yet
            logger.warning(
                f"[TAGS] No tags available rate={rate}, category={product.category.id}"
            )
            messages.info(
                request,
                "Для этого продукта нет тегов. Администратор добавит их",
            )
        tags_form.fields["taste_tags"].queryset = unique_tags

        tag_ids = list(unique_tags.values_list("id", flat=True))
        request.session["tag_ids"] = tag_ids

        return render(
            request,
            "rate_food/partials/tag_selector.html",
            context={"tags_form": tags_form},
        )


class SaveRatingView(View):
    def post(self, request):
        logger.info("[S3] User on Stage 3")
        rate = request.session.get("rate")
        tag_ids = request.session.get("tag_ids")

        product, error = get_product_from_session(request)
        if error or rate is None:
            return redirect("add_food:add_product")

        # Bind POST data to the form
        tags_form = TasteTagForm(request.POST)
        allowed_tags = TasteTag.objects.filter(id__in=tag_ids or [])
        tags_form.fields["taste_tags"].queryset = allowed_tags

        if not tags_form.is_valid():
            logger.warning("[RATE] TasteTagsForm is not valid")
            return render(
                request, "rate_food/add_rating.html", {"tags_form": tags_form}
            )

        tags = tags_form.cleaned_data["taste_tags"]

        with transaction.atomic():
            rating_obj = ProductRating.objects.create(product=product, rate=rate)
            rating_obj.taste_tags.set(tags)
        logger.info("[DB] Add new rate for product")

        request.session.pop("current_product_id", None)
        request.session.pop("rate", None)
        request.session.pop("tag_ids", None)

        # Regular redirect here — HTMX is not involved at this stage,
        # full page reload is expected
        return redirect("food_hub:product_list")
