import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import reverse

from food_hub.models import (Category, Company, Country, Product,
                             ProductRating)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="tmail@inbox.com", password="testpass")


@pytest.fixture
def make_user(db):
    def _make(username, email):
        return User.objects.create_user(username=username, email=email, password="testpass")

    return _make


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
def make_product(db, company, category):
    def _make(name, ean):
        return Product.objects.create(
            company=company,
            category=category,
            name=name,
            ean_code=ean,
            img_field=SimpleUploadedFile(
                "test.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )

    return _make


@pytest.mark.django_db
def test_current_url(user, client):
    response = client.get(reverse("food_hub:home"))
    assert response.status_code == 302

    client.force_login(user=user)
    response = client.get(reverse("food_hub:home"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_unique_product_for_user(make_user, make_product, client):
    user1 = make_user("Viva", "t1@mail.ru")
    user2 = make_user("Python", "t2@mail.ru")

    product1 = make_product("Мороженое", "4006381333931")
    product2 = make_product("Йогурт", "1234567890123")

    ProductRating.objects.create(product=product1, rate=5, user=user1)
    ProductRating.objects.create(product=product2, rate=2, user=user2)

    client.force_login(user=user1)
    response = client.get(reverse("food_hub:home"))
    assert response.status_code == 200
    assert product1 in response.context["products"]
    assert product2 not in response.context["products"]
