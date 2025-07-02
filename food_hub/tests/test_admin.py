import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import admin
from food_hub import admin as food_admin
from food_hub.models import (
    Category,
    Company,
    Country,
    Product,
    ProductRating,
    TasteTag,
)


@pytest.fixture
def superuser(db):
    User = get_user_model()
    user = User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass"
    )
    return user


@pytest.fixture
def admin_client(client, superuser):
    client.force_login(superuser)
    return client


@pytest.mark.django_db
def test_admin_registered_models():
    site = admin.site
    assert site.is_registered(Category)
    assert site.is_registered(Company)
    assert site.is_registered(Country)
    assert site.is_registered(Product)
    assert site.is_registered(ProductRating)
    assert site.is_registered(TasteTag)


def test_admin_class_attributes():
    for admin_class in [
        food_admin.CategoryAdmin,
        food_admin.CompanyAdmin,
        food_admin.CountryAdmin,
        food_admin.ProductAdmin,
        food_admin.ProductRatingAdmin,
        food_admin.TasteTagAdmin,
    ]:
        assert hasattr(admin_class, "list_display")
        assert hasattr(admin_class, "search_fields")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model, changelist_urlname, add_urlname",
    [
        (Category, "admin:food_hub_category_changelist", "admin:food_hub_category_add"),
        (Company, "admin:food_hub_company_changelist", "admin:food_hub_company_add"),
        (Country, "admin:food_hub_country_changelist", "admin:food_hub_country_add"),
        (Product, "admin:food_hub_product_changelist", "admin:food_hub_product_add"),
        (
            ProductRating,
            "admin:food_hub_productrating_changelist",
            "admin:food_hub_productrating_add",
        ),
        (TasteTag, "admin:food_hub_tastetag_changelist", "admin:food_hub_tastetag_add"),
    ],
)
def test_admin_changelist_and_add_pages(
    admin_client, model, changelist_urlname, add_urlname
):
    url = reverse(changelist_urlname)
    response = admin_client.get(url)
    assert response.status_code == 200
    url = reverse(add_urlname)
    response = admin_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_product_search_and_filter(admin_client):
    country = Country.objects.create(name="Россия")
    company = Company.objects.create(name="Компания", country=country)
    category = Category.objects.create(name="Десерты")
    product = Product.objects.create(
        company=company,
        category=category,
        name="Мороженое",
        ean_code="4006381333931",
        img_field="test.jpg",
    )
    url = reverse("admin:food_hub_product_changelist")
    # Поиск по имени
    response = admin_client.get(url, {"q": "Мороженое"})
    assert response.status_code == 200
    assert "Мороженое" in response.content.decode()
    # Фильтрация по категории
    response = admin_client.get(url, {"category__id__exact": category.id})
    assert response.status_code == 200
    assert "Мороженое" in response.content.decode()
    # Фильтрация по компании
    response = admin_client.get(url, {"company__id__exact": company.id})
    assert response.status_code == 200
    assert "Мороженое" in response.content.decode()


@pytest.mark.django_db
def test_admin_company_search_and_filter(admin_client):
    country = Country.objects.create(name="Россия")
    company = Company.objects.create(name="Компания", country=country)
    url = reverse("admin:food_hub_company_changelist")
    # Поиск по имени
    response = admin_client.get(url, {"q": "Компания"})
    assert response.status_code == 200
    assert "Компания" in response.content.decode()
    # Фильтрация по стране
    response = admin_client.get(url, {"country__id__exact": country.id})
    assert response.status_code == 200
    assert "Компания" in response.content.decode()


@pytest.mark.django_db
def test_admin_category_search(admin_client):
    category = Category.objects.create(name="Десерты")
    url = reverse("admin:food_hub_category_changelist")
    response = admin_client.get(url, {"q": "Десерты"})
    assert response.status_code == 200
    assert "Десерты" in response.content.decode()


@pytest.mark.django_db
def test_admin_country_search(admin_client):
    country = Country.objects.create(name="Россия")
    url = reverse("admin:food_hub_country_changelist")
    response = admin_client.get(url, {"q": "Россия"})
    assert response.status_code == 200
    assert "Россия" in response.content.decode()


@pytest.mark.django_db
def test_admin_tastetag_search_and_filter(admin_client):
    tag = TasteTag.objects.create(name="Сладкий", taste_type="P", slug="sladkiy")
    url = reverse("admin:food_hub_tastetag_changelist")
    response = admin_client.get(url, {"q": "Сладкий"})
    assert response.status_code == 200
    assert "Сладкий" in response.content.decode()
    # Фильтрация по taste_type
    response = admin_client.get(url, {"taste_type": "P"})
    assert response.status_code == 200
    assert "Сладкий" in response.content.decode()


@pytest.mark.django_db
def test_admin_productrating_search_and_filter(admin_client):
    country = Country.objects.create(name="Россия")
    company = Company.objects.create(name="Компания", country=country)
    category = Category.objects.create(name="Десерты")
    product = Product.objects.create(
        company=company,
        category=category,
        name="Мороженое",
        ean_code="9780306406157",
        img_field="test2.jpg",
    )
    rating = ProductRating.objects.create(
        product=product, rate=5, comment="Очень вкусно!"
    )
    url = reverse("admin:food_hub_productrating_changelist")
    # Поиск по имени продукта
    response = admin_client.get(url, {"q": "Мороженое"})
    assert response.status_code == 200
    assert "Очень вкусно!" in response.content.decode()
    # Поиск по комментарию
    response = admin_client.get(url, {"q": "вкусно"})
    assert response.status_code == 200
    assert "Очень вкусно!" in response.content.decode()
    # Фильтрация по rate
    response = admin_client.get(url, {"rate": 5})
    assert response.status_code == 200
    assert "Очень вкусно!" in response.content.decode()


@pytest.mark.django_db
def test_admin_add_product(admin_client):
    country = Country.objects.create(name="Россия")
    company = Company.objects.create(name="Компания", country=country)
    category = Category.objects.create(name="Десерты")
    url = reverse("admin:food_hub_product_add")
    data = {
        "company": company.id,
        "category": category.id,
        "name": "Пломбир",
        "ean_code": "5012345678900",
        "img_field": "",
    }
    response = admin_client.post(url, data)
    assert response.status_code == 200
    assert (
        "Пломбир" in response.content.decode()
        or "img_field" in response.content.decode()
    )


@pytest.mark.django_db
def test_create_superuser(superuser):
    User = get_user_model()
    assert User.objects.filter(username="admin").exists()
