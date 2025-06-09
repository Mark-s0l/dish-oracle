from food_hub.models import Product, ProductRating, Company, Country, Category, TasteTag
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

@pytest.mark.django_db
def test_country_str():
    country = Country.objects.create(name="Япония")
    assert str(country) == "Япония"

@pytest.mark.django_db
def test_company_str():
    country = Country.objects.create(name="Франция")
    company = Company.objects.create(name="Nestlé", country=country)
    assert str(company) == "Nestlé"

@pytest.mark.django_db
def test_taste_tag_str_and_unique():
    tag = TasteTag.objects.create(name="Горький", taste_type='N')
    assert str(tag) == "Горький [Negative]"

    with pytest.raises(IntegrityError):
        TasteTag.objects.create(name="Горький", taste_type='P')

@pytest.mark.django_db
def test_category_str_and_relation():
    tag = TasteTag.objects.create(name="Сладкий", taste_type='P')
    category = Category.objects.create(name="Десерты")
    category.taste_tags.add(tag)

    assert str(category) == "Десерты"
    assert tag in category.taste_tags.all()

@pytest.mark.django_db
def test_product_str_and_unique_per_company():
    country = Country.objects.create(name="Германия")
    company = Company.objects.create(name="Milka", country=country)
    category = Category.objects.create(name="Шоколад")
    product = Product.objects.create(
        name="Milka Oreo",
        company=company,
        category=category,
        ean_code="1234567890123",
        img_url="https://example.com/image.jpg"
    )

    assert str(product) == "Milka Oreo (Milka)"

    with pytest.raises(IntegrityError):
        Product.objects.create(
            name="Milka Oreo", 
            company=company,    
            category=category,
            ean_code="9999999999999",
            img_url="https://example.com/2.jpg"
        )

@pytest.mark.django_db
def test_product_ean_code_validation():
    country = Country.objects.create(name="США")
    company = Company.objects.create(name="Hershey", country=country)
    category = Category.objects.create(name="Конфеты")

    product = Product(
        name="Reese's",
        company=company,
        category=category,
        ean_code="bad_code",
        img_url="https://example.com/img.jpg"
    )

    with pytest.raises(ValidationError):
        product.full_clean()

@pytest.mark.django_db
def test_product_rating_str_and_rate_validation():
    country = Country.objects.create(name="Россия")
    company = Company.objects.create(name="Аленка", country=country)
    category = Category.objects.create(name="Шоколад")
    product = Product.objects.create(
        name="Аленка Классика",
        company=company,
        category=category,
        ean_code="1111111111111",
        img_url="https://example.com/a.jpg"
    )

    rating = ProductRating.objects.create(product=product, rate=4)
    assert str(rating) == "Rating 4 for Аленка Классика"

    rating_invalid = ProductRating(product=product, rate=6)
    with pytest.raises(ValidationError):
        rating_invalid.full_clean()
