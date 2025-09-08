from contextlib import nullcontext as does_not_raise
from django.urls import reverse
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

import food_hub.models as models


@pytest.fixture
def country(db):
    return models.Country.objects.create(name="Россия")


@pytest.fixture
def company1(db, country):
    return models.Company.objects.create(name="Завод мороженого", country=country)

@pytest.fixture
def company2(db, country):
    return models.Company.objects.create(name="Вафельный комбинат", country=country)

@pytest.fixture
def company3(db, country):
    return models.Company.objects.create(name="Цех Кремлбрюле", country=country)

@pytest.fixture
def category(db):
    cat = models.Category.objects.create(name="Десерты")
    return cat


@pytest.fixture
def product1(db, company1, category):
    product1 = models.Product.objects.create(
        company=company1,
        category=category,
        name="Мороженое Сливочное Яшкино 20% 70г",
        ean_code="4006381333931",
    )
    return product1

@pytest.fixture
def product2(db, company2, category):
        product2 = models.Product.objects.create(
        company=company2,
        category=category,
        name="Вафли Яшкино 200г",
        ean_code="4607145590012",
    )
        return product2

@pytest.fixture
def product3(db, company3, category):
    product3 = models.Product.objects.create(
        company=company3,
        category=category,
        name="Крем-брюле Бодрая Корова 200г",
        ean_code="4600699502197",
    )
    return product3


@pytest.mark.parametrize(
    "query,expected_names",
    [
        ("Моро", ["Мороженое Сливочное Яшкино 20% 70г"]),
        ("Мороженое", ["Мороженое Сливочное Яшкино 20% 70г"]),
        ("Кетчуп", []),
        (" ", []),
        ("", []),
        ("МоРОЖЕное", ["Мороженое Сливочное Яшкино 20% 70г"]),
        ("МаРОЖЕное", []),
        ("Ваф", ["Вафли Яшкино 200г"]),
        ("Крем", ["Крем-брюле Бодрая Корова 200г"]),
        ("Крем-брюле Бодрая Корова 200г", ["Крем-брюле Бодрая Корова 200г"]),
        ("7", ["Мороженое Сливочное Яшкино 20% 70г"]),
        ("№2", []),
        ("Десерты", ["Мороженое Сливочное Яшкино 20% 70г", "Вафли Яшкино 200г", "Крем-брюле Бодрая Корова 200г"]),
        ("Яшкино", ["Мороженое Сливочное Яшкино 20% 70г", "Вафли Яшкино 200г"])
    ]
)
@pytest.mark.django_db
def test_product_search_various_queries(client, product1, product2, product3, query, expected_names):
    url = reverse("search_hub:product_search")
    response = client.get(url, {"query": query})
    products = list(response.context["products"].values_list("name", flat=True))
    assert  set(products) == set(expected_names)