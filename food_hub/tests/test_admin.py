import pytest
from django.contrib.admin.sites import site
from django.urls import reverse

@pytest.mark.django_db
def test_models_registered_in_admin():
    from food_hub.models import (
        Product, ProductRating, Company, Country, Category, TasteTag
    )

    for model in [Product, ProductRating, Company, Country, Category, TasteTag]:
        assert model in site._registry


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="123secure"
    )


@pytest.fixture
def admin_client(admin_user, client):
    client.login(username="admin", password="123secure")
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("model_name", [
    "tastetag",
    "category",
    "country",
    "company",
    "product",
    "productrating",
])
def test_admin_changelist_loads(admin_client, model_name):
    url = reverse(f"admin:food_hub_{model_name}_changelist")
    response = admin_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("model_name", [
    "product",
    "productrating",
])
def test_admin_add_view_loads(admin_client, model_name):
    url = reverse(f"admin:food_hub_{model_name}_add")
    response = admin_client.get(url)
    assert response.status_code == 200
