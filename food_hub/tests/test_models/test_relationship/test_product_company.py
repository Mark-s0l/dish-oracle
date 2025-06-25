import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from food_hub.models import Category, Company, Country, Product


@pytest.fixture
def country(db):
    return Country.objects.create(name="Россия")


@pytest.fixture
def company(db, country):
    return Company.objects.create(name="Компания", country=country)


@pytest.fixture
def another_company(db, country):
    return Company.objects.create(name="ДругаяКомпания", country=country)


@pytest.fixture
def category(db):
    return Category.objects.create(name="Десерты")


@pytest.fixture
def image_file():
    return SimpleUploadedFile("test.jpg", b"filecontent", content_type="image/jpeg")


class TestProductCompany:
    @pytest.mark.django_db
    def test_product_company_fk_success(
        self, company, category, image_file, save_and_clean
    ):
        product = Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="4006381333931",
            img_field=image_file,
        )
        save_and_clean(product)
        from_db = Product.objects.get(pk=product.pk)
        assert from_db.company == company
        assert from_db.company.name == "Компания"

    @pytest.mark.django_db
    def test_product_company_fk_required(self, category, image_file, save_and_clean):
        product = Product(
            company=None,
            category=category,
            name="Мороженое",
            ean_code="4006381333932",
            img_field=image_file,
        )
        with pytest.raises(ValidationError):
            save_and_clean(product)

    @pytest.mark.django_db
    def test_company_delete_cascades_to_products(
        self, company, category, image_file, save_and_clean
    ):
        product = Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="9781861972712",
            img_field=image_file,
        )
        save_and_clean(product)
        company.delete()
        assert not Product.objects.filter(pk=product.pk).exists()

    @pytest.mark.django_db
    def test_product_change_company(
        self, company, another_company, category, image_file, save_and_clean
    ):
        product = Product(
            company=company,
            category=category,
            name="Пирожное",
            ean_code="4006381333931",
            img_field=image_file,
        )
        save_and_clean(product)
        product.company = another_company
        save_and_clean(product)
        from_db = Product.objects.get(pk=product.pk)
        assert from_db.company == another_company

    @pytest.mark.django_db
    def test_multiple_products_same_company(
        self, company, category, image_file, save_and_clean
    ):
        product1 = Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="5901234123457",
            img_field=image_file,
        )
        product2 = Product(
            company=company,
            category=category,
            name="Эклер",
            ean_code="5012345678900",
            img_field=image_file,
        )
        save_and_clean(product1)
        save_and_clean(product2)
        assert Product.objects.filter(company=company).count() == 2

    @pytest.mark.django_db
    def test_product_company_integrity(
        self, company, category, image_file, save_and_clean
    ):
        fake_company = Company(id=9999, name="Fake", country=company.country)
        product = Product(
            company=fake_company,
            category=category,
            name="Фейк",
            ean_code="4006381333937",
            img_field=image_file,
        )
        with pytest.raises(ValidationError):
            save_and_clean(product)

    @pytest.mark.django_db
    def test_delete_all_products_then_company(
        self, company, category, image_file, save_and_clean
    ):
        product1 = Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="9780306406157",
            img_field=image_file,
        )
        product2 = Product(
            company=company,
            category=category,
            name="Эклер",
            ean_code="9781861972712",
            img_field=image_file,
        )
        save_and_clean(product1)
        save_and_clean(product2)
        product1.delete()
        product2.delete()
        company.delete()
        assert not Company.objects.filter(pk=company.pk).exists()
