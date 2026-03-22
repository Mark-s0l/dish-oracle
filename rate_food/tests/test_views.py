from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from food_hub.models import (Category, Company, Country, Product,
                             ProductRating, TasteTag)
from rate_food.forms import RatingForm, TasteTagForm
from rate_food.views import get_product_from_session


@pytest.fixture
def country(db):
    return Country.objects.create(name="Россия")


@pytest.fixture
def make_company(db, country):
    def _make(name):
        return Company.objects.create(name=name, country=country)

    return _make


@pytest.fixture
def make_product(db, category):
    def _make(company, name, ean):
        return Product.objects.create(
            company=company, category=category, name=name, ean_code=ean
        )

    return _make


@pytest.fixture
def category(db):
    category = Category.objects.create(name="Десерты")
    return category


@pytest.fixture
def setup_product(db, make_company, make_product, category, country):
    c1 = make_company("Завод мороженого")

    p1 = make_product(c1, "Мороженое Сливочное Яшкино 20% 70г", "4006381333931")
    return p1


@pytest.fixture
def product_with_session(client, setup_product):
    session = client.session
    session["current_product_id"] = setup_product.pk
    session.save()
    return setup_product


@pytest.fixture
def taste_tag(db, category):
    taste_tag = TasteTag.objects.create(
        name="Сладкий", taste_type=TasteTag.TypeTag.POSITIVE, slug="sladkiy"
    )
    category.taste_tags.add(taste_tag)
    return taste_tag


class TestRateProductViewGet:

    def test_get_pk_in_session(self, client, product_with_session):
        response = client.get(
            reverse("rate_food:add_rate"), headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        assert response.templates[0].name == "rate_food/partials/rate_selector.html"
        assert response.context["product"] == product_with_session
        assert isinstance(response.context["rate_form"], RatingForm)
        assert client.session.get("current_product_id") == product_with_session.pk

    def test_get_pk_not_in_session(self, client, db):
        expected_url = reverse("add_food:add_product")
        response = client.get(
            reverse("rate_food:add_rate"), headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == expected_url
        assert len(response.templates) == 0
        assert "current_product_id" not in client.session

    def test_get_pk_in_session_load_main_template(self, client, product_with_session):
        response = client.get(reverse("rate_food:add_rate"))
        assert response.status_code == 200
        assert response.templates[0].name == "rate_food/add_rating.html"
        assert response.context["product"] == product_with_session
        assert isinstance(response.context["rate_form"], RatingForm)
        assert client.session.get("current_product_id") == product_with_session.pk

    def test_get_pk_not_in_session_no_htmx(self, client, db):
        response = client.get(reverse("rate_food:add_rate"))
        assert response.status_code == 302
        assert response.headers.get("Location") == reverse("add_food:add_product")


class TestRateProductViewPost:

    def test_get_pk_in_session_post(self, client, product_with_session, taste_tag):
        response = client.post(reverse("rate_food:add_rate"), {"rate": 3})
        assert response.status_code == 200
        assert client.session.get("current_product_id") == product_with_session.pk
        assert client.session.get("rate") == 3
        assert client.session.get("tag_ids") == [taste_tag.pk]
        assert response.templates[0].name == "rate_food/partials/tag_selector.html"
        assert isinstance(response.context["tags_form"], TasteTagForm)
        tags_form = response.context["tags_form"]
        assert taste_tag in tags_form.fields["taste_tags"].queryset

    def test_invalid_rate_form(self, client, product_with_session):
        response = client.post(reverse("rate_food:add_rate"), {"rate": "invalid"})
        assert response.status_code == 200
        assert isinstance(response.context["rate_form"], RatingForm)
        assert response.context["product"] == product_with_session
        assert response.templates[0].name == "rate_food/partials/rate_selector.html"

    def test_pk_not_in_session(self, db, client):
        response = client.post(reverse("rate_food:add_rate"), {"rate": "5"})
        expected_url = reverse("add_food:add_product")
        assert response.status_code == 302
        assert response.headers.get("Location") == expected_url
        assert len(response.templates) == 0
        assert "current_product_id" not in client.session

    def test_empty_taste_tag(self, client, product_with_session):
        response = client.post(reverse("rate_food:add_rate"), {"rate": 3})
        assert response.status_code == 200
        assert client.session.get("current_product_id") == product_with_session.pk
        assert client.session.get("rate") == 3
        assert client.session.get("tag_ids") == []
        assert response.templates[0].name == "rate_food/partials/tag_selector.html"
        assert isinstance(response.context["tags_form"], TasteTagForm)
        tags_form = response.context["tags_form"]
        assert not tags_form.fields["taste_tags"].queryset.exists()

    def test_post_pk_not_in_session_htmx(self, client, db):
        response = client.post(
            reverse("rate_food:add_rate"), {"rate": "5"}, headers={"HX-Request": "true"}
        )
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == reverse("add_food:add_product")


class TestSaveRatingView:

    def test_valid_work_view(self, client, product_with_session, taste_tag):
        session = client.session
        session["rate"] = 5
        session["tag_ids"] = [taste_tag.pk]
        session["current_product_id"] = product_with_session.pk
        session.save()
        response = client.post(
            reverse("rate_food:save_rate"), {"taste_tags": [taste_tag.pk]}
        )
        assert response.status_code == 302
        assert ProductRating.objects.filter(product=product_with_session).exists()
        rating = ProductRating.objects.get(product=product_with_session)
        assert taste_tag in rating.taste_tags.all()
        assert client.session.get("current_product_id") is None
        assert client.session.get("rate") is None
        assert client.session.get("tag_ids") is None

    def test_pk_is_not_in_session(self, client, db, taste_tag):
        session = client.session
        session["rate"] = 5
        session["tag_ids"] = [taste_tag.pk]
        session.save()
        response = client.post(
            reverse("rate_food:save_rate"), {"tag_ids": [taste_tag.pk]}
        )
        expected_url = reverse("add_food:add_product")
        assert response.status_code == 302
        assert response.headers.get("Location") == expected_url
        assert len(response.templates) == 0
        assert "current_product_id" not in session
        assert "rate" in session
        assert "tag_ids" in session

    def test_rate_not_in_session(self, client, db, taste_tag, product_with_session):
        session = client.session
        session["tag_ids"] = [taste_tag.pk]
        session["current_product_id"] = product_with_session.pk
        session.save()
        response = client.post(
            reverse("rate_food:save_rate"), {"tag_ids": [taste_tag.pk]}
        )
        expected_url = reverse("add_food:add_product")
        assert response.status_code == 302
        assert response.headers.get("Location") == expected_url
        assert len(response.templates) == 0
        assert "current_product_id" in session
        assert "rate" not in session
        assert "tag_ids" in session

    def test_tags_form_invalid(self, client, db, product_with_session, taste_tag):
        session = client.session
        session["rate"] = 5
        session["tag_ids"] = [taste_tag.pk]
        session["current_product_id"] = product_with_session.pk
        session.save()
        response = client.post(
            reverse("rate_food:save_rate"), {"taste_tags": "invalid"}
        )
        assert response.status_code == 200
        assert isinstance(response.context["tags_form"], TasteTagForm)
        assert response.templates[0].name == "rate_food/add_rating.html"


class TestGetProductFromSession:

    @patch("rate_food.views.messages")
    def test_no_product_id_in_session(self, mock_messages):
        request = MagicMock()
        request.session.get.return_value = None
        product, error = get_product_from_session(request)
        assert product is None
        assert error is True
        mock_messages.error.assert_called_once()
        mock_messages.error.assert_called_once_with(
            request, "Сессия истекла. Начните заново"
        )

    @patch("rate_food.views.messages")
    def test_product_id_in_session(self, mock_messages, setup_product):
        request = MagicMock()
        request.session.get.return_value = setup_product.pk
        product, error = get_product_from_session(request)
        assert product is not None
        assert error is None
        mock_messages.error.assert_not_called()

    @patch("rate_food.views.messages")
    def test_product_does_not_exists(self, mock_messages, setup_product):
        request = MagicMock()
        request.session.get.return_value = setup_product.pk + 1
        product, error = get_product_from_session(request)
        assert product is None
        assert error is True
        request.session.pop.assert_any_call("current_product_id", None)
        request.session.pop.assert_any_call("rate", None)
        mock_messages.error.assert_called_once()
        mock_messages.error.assert_called_once_with(
            request, "Продукт не найден. Начните заново"
        )

    @patch("rate_food.views.Product")
    @patch("rate_food.views.messages")
    def test_orm_request_with_select_category(
        self, mock_messages, mock_product, setup_product
    ):
        request = MagicMock()
        request.session.get.return_value = setup_product.pk
        mock_product.objects.select_related.return_value.get.return_value = (
            setup_product
        )
        product, error = get_product_from_session(request, select_category=True)
        mock_product.objects.select_related.assert_called_once_with("category")
        mock_product.objects.select_related.return_value.get.assert_called_once_with(
            pk=setup_product.pk
        )
        assert product == setup_product
        assert error is None

    @patch("rate_food.views.Product")
    @patch("rate_food.views.messages")
    def test_orm_request_only_id(self, mock_messages, mock_product, setup_product):
        request = MagicMock()
        request.session.get.return_value = setup_product.pk
        mock_product.objects.only.return_value.get.return_value = setup_product
        product, error = get_product_from_session(request)
        mock_product.objects.only.assert_called_once_with("id")
        mock_product.objects.only.return_value.get.assert_called_once_with(
            pk=setup_product.pk
        )
        assert product == setup_product
        assert error is None
