from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

import food_hub.models as models


@pytest.fixture
def country(db):
    return models.Country.objects.create(name="Россия")


@pytest.fixture
def company(db, country):
    return models.Company.objects.create(name="Компания", country=country)


@pytest.fixture
def taste_tag(db):
    return models.TasteTag.objects.create(
        name="Сладкий", taste_type=models.TasteTag.TypeTag.POSITIVE, slug="sladkiy"
    )


@pytest.fixture
def category(db, taste_tag):
    cat = models.Category.objects.create(name="Десерты")
    cat.taste_tags.add(taste_tag)
    return cat


@pytest.fixture
def image_file():
    return SimpleUploadedFile("test.jpg", b"filecontent", content_type="image/jpeg")


class TestProduct:
    @pytest.mark.django_db
    def test_product_creation(self, company, category, image_file, save_and_clean):
        product = models.Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="4006381333931",
            img_field=image_file,
        )
        save_and_clean(product)
        from_db = models.Product.objects.get(pk=product.pk)
        assert from_db.name == "Мороженое"
        assert from_db.ean_code == "4006381333931"
        assert from_db.img_field.name.startswith("products/")
        assert str(from_db) == "Мороженое (Компания)"

    @pytest.mark.django_db
    def test_product_unique_ean_code(
        self, company, category, image_file, save_and_clean
    ):
        product1 = models.Product(
            company=company,
            category=category,
            name="Пирожное",
            ean_code="4006381333931",
            img_field=image_file,
        )
        save_and_clean(product1)
        product2 = models.Product(
            company=company,
            category=category,
            name="Эклер",
            ean_code="4006381333931",
            img_field=image_file,
        )
        with pytest.raises(ValidationError):
            save_and_clean(product2)

    @pytest.mark.django_db
    def test_product_unique_name_per_company(
        self, company, category, image_file, save_and_clean
    ):
        product1 = models.Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="4006381333931",
            img_field=image_file,
        )
        save_and_clean(product1)
        product2 = models.Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="4006381333932",
            img_field=image_file,
        )
        with pytest.raises(ValidationError):
            save_and_clean(product2)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "name, expectation",
        [
            ("Мороженое", does_not_raise()),
            (" Мороженое", does_not_raise()),  # теперь не ждём ошибку
            ("", pytest.raises(ValidationError)),
            ("Мороженое123", does_not_raise()),  # теперь не ждём ошибку
            ("a" * 101, pytest.raises(ValidationError)),
            ("Мороженое ", does_not_raise()),
        ],
    )
    def test_product_name_validation(
        self, company, category, image_file, name, expectation, save_and_clean
    ):
        product = models.Product(
            company=company,
            category=category,
            name=name,
            ean_code="4006381333931",
            img_field=image_file,
        )
        with expectation:
            save_and_clean(product)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "ean_code, expectation",
        [
            ("4006381333931", does_not_raise()),
            ("123456789012", pytest.raises(ValidationError)),
            ("12345678901234", pytest.raises(ValidationError)),
            ("abcdefghijklm", pytest.raises(ValidationError)),
            ("", pytest.raises(ValidationError)),
            (" ", pytest.raises(ValidationError)),
            (" 1248796475", pytest.raises(ValidationError)),
        ],
    )
    def test_product_ean_code_validation(
        self, company, category, image_file, ean_code, expectation, save_and_clean
    ):
        product = models.Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code=ean_code,
            img_field=image_file,
        )
        with expectation:
            save_and_clean(product)

    @pytest.mark.django_db
    def test_product_name_max_length(
        self, company, category, image_file, save_and_clean
    ):
        name = "a" * 100
        product = models.Product(
            company=company,
            category=category,
            name=name,
            ean_code="4006381333931",
            img_field=image_file,
        )
        save_and_clean(product)
        assert len(product.name) == 100
