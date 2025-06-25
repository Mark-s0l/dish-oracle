from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from food_hub.models import Category, Company, Country, Product, ProductRating, TasteTag


@pytest.fixture
def country(db):
    return Country.objects.create(name="Россия")


@pytest.fixture
def company(db, country):
    return Company.objects.create(name="Компания", country=country)


@pytest.fixture
def category(db):
    return Category.objects.create(name="Десерты")


@pytest.fixture
def taste_tag(db):
    return TasteTag.objects.create(
        name="Сладкий", taste_type=TasteTag.TypeTag.POSITIVE, slug="sladkiy"
    )


@pytest.fixture
def product(db, company, category):
    return Product.objects.create(
        company=company,
        category=category,
        name="Мороженое",
        ean_code="4006381333931",
        img_field=SimpleUploadedFile(
            "test.jpg", b"filecontent", content_type="image/jpeg"
        ),
    )


class TestProductRating:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "rate, expectation",
        [
            (1, does_not_raise()),
            (5, does_not_raise()),
            (0, pytest.raises(ValidationError)),
            (6, pytest.raises(ValidationError)),
            (-1, pytest.raises(ValidationError)),
            (None, pytest.raises(ValidationError)),
        ],
    )
    def test_rate_validation(self, product, rate, expectation, save_and_clean):
        rating = ProductRating(
            product=product,
            rate=rate,
        )
        with expectation:
            save_and_clean(rating)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "comment, expectation",
        [
            ("Очень вкусно!", does_not_raise()),
            ("", does_not_raise()),
            (None, does_not_raise()),
            ("a" * 100, does_not_raise()),
            ("a" * 101, pytest.raises(ValidationError)),
        ],
    )
    def test_comment_length(self, product, comment, expectation, save_and_clean):
        rating = ProductRating(product=product, rate=5, comment=comment)
        with expectation:
            save_and_clean(rating)

    @pytest.mark.django_db
    def test_str_method(self, product):
        rating = ProductRating.objects.create(
            product=product, rate=4, comment="Неплохо"
        )
        assert str(rating) == f"Rating 4 for {product.name}"

    @pytest.mark.django_db
    def test_created_and_updated_auto_fields(self, product):
        rating = ProductRating.objects.create(product=product, rate=3)
        assert rating.created_at is not None
        assert rating.updated_at is not None
