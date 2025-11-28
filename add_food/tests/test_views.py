import pytest
from django.urls import reverse

from food_hub.models import Category, Company, Country, Product

pytestmark = pytest.mark.django_db


def test_add_product_api_failure_shows_form_error(client, mocker):
    ean = "4607145590012"

    mocker.patch(
        "add_food.views.add_product",
        return_value={
            "successful": False,
            "error": "Ошибка",
        },
    )

    url = reverse("add_food:add_product")
    response = client.post(url, {"ean_code": ean})

    assert response.status_code == 200

    content = response.content.decode()
    assert "Ошибка" in content
    assert Product.objects.count() == 0


def test_add_product_creates_new_models_and_redirects(client, mocker):
    ean = "4607145590012"

    mocker.patch(
        "add_food.views.add_product",
        return_value={
            "successful": True,
            "name": "Шоколадка",
            "company": "Nestle",
            "category": "Сладости",
            "country": "Швейцария",
            "save_path": "products/test.jpg",
        },
    )

    url = reverse("add_food:add_product")
    response = client.post(url, {"ean_code": ean})

    # редирект
    assert response.status_code == 302

    product = Product.objects.get(ean_code=ean)
    assert product.name == "Шоколадка"
    assert product.img_field == "products/test.jpg"

    assert Country.objects.filter(name="Швейцария").count() == 1
    assert Company.objects.filter(name="Nestle").count() == 1
    assert Category.objects.filter(name="Сладости").count() == 1

    expected_url = reverse("rate_food:add_rate", kwargs={"product_id": product.id})
    assert response.url == expected_url


def test_add_product_reuses_existing_related(client, mocker):
    ean = "4607145590012"

    country = Country.objects.create(name="Германия")
    company = Company.objects.create(name="Haribo", country=country)
    category = Category.objects.create(name="Жевательные конфеты")

    mocker.patch(
        "add_food.views.add_product",
        return_value={
            "successful": True,
            "name": "Goldbären",
            "company": "Haribo",
            "category": "Жевательные конфеты",
            "country": "Германия",
            "save_path": None,
        },
    )

    url = reverse("add_food:add_product")
    response = client.post(url, {"ean_code": ean})

    assert response.status_code == 302

    product = Product.objects.get(ean_code=ean)

    assert product.company == company
    assert product.category == category
    assert product.company.country == country

    assert Country.objects.filter(name="Германия").count() == 1
    assert Company.objects.filter(name="Haribo").count() == 1
    assert Category.objects.filter(name="Жевательные конфеты").count() == 1
