from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.db import DatabaseError, IntegrityError
from add_food.forms import AddProductForm
from add_food.services import ApiError
from food_hub.models import Category, Company, Country, Product


VALID_EAN = "4006381333931"


def make_api_data(**kwargs):
    defaults = {
        "name": "Test Product",
        "country": "Germany",
        "company": "Test Corp",
        "category": "Snacks",
        "save_path": "/images/test.jpg",
    }
    return {**defaults, **kwargs}


def make_product():
    country = Country.objects.create(name="Germany")
    company = Company.objects.create(name="Test Corp", country=country)
    category = Category.objects.create(name="Snacks")
    return Product.objects.create(
        ean_code=VALID_EAN,
        name="Test Product",
        category=category,
        company=company,
        img_field="/images/test.jpg",
    )


class AddProductViewTests(TestCase):

    def setUp(self):
        self.url = reverse("add_food:add_product")
        self.form_data = {"ean_code": VALID_EAN}


    def test_existing_product_redirects(self):
        make_product()
        with patch("add_food.views.add_product") as mock_api, \
             patch.object(AddProductForm, "validate_unique"):
            response = self.client.post(self.url, self.form_data)
            mock_api.assert_not_called()
        self.assertRedirects(response, reverse("rate_food:add_rate"))

    def test_existing_product_saves_id_in_session(self):
        product = make_product()
        with patch.object(AddProductForm, "validate_unique"):
            self.client.post(self.url, self.form_data)
        self.assertEqual(self.client.session["current_product_id"], product.pk)


    @patch("add_food.views.add_product")
    def test_new_product_created_via_api(self, mock_api):
        mock_api.return_value = make_api_data()
        response = self.client.post(self.url, self.form_data)
        self.assertRedirects(response, reverse("rate_food:add_rate"))
        self.assertTrue(Product.objects.filter(ean_code=VALID_EAN).exists())

    @patch("add_food.views.add_product")
    def test_new_product_saves_id_in_session(self, mock_api):
        mock_api.return_value = make_api_data()
        self.client.post(self.url, self.form_data)
        product = Product.objects.get(ean_code=VALID_EAN)
        self.assertEqual(self.client.session["current_product_id"], product.pk)

    @patch("add_food.views.add_product")
    def test_duplicate_ean_no_duplicate_created(self, mock_api):
        mock_api.return_value = make_api_data()
        with patch.object(AddProductForm, "validate_unique"):
            self.client.post(self.url, self.form_data)
            self.client.post(self.url, self.form_data)
        self.assertEqual(Product.objects.filter(ean_code=VALID_EAN).count(), 1)


    @patch("add_food.views.add_product")
    def test_api_error_shows_form_error(self, mock_api):
        mock_api.side_effect = ApiError("Продукт не найден в базе")
        response = self.client.post(self.url, self.form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Продукт не найден в базе", response.context["form"].errors["ean_code"])

    @patch("add_food.views.AddProductView._get_or_create_product")
    @patch("add_food.views.add_product")
    def test_database_error_shows_form_error(self, mock_api, mock_create):
        mock_api.return_value = make_api_data()
        mock_create.side_effect = DatabaseError()
        response = self.client.post(self.url, self.form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Ошибка записи данных", response.context["form"].errors["ean_code"][0])


    def test_get_or_create_creates_all_objects(self):
        from add_food.views import AddProductView
        product = AddProductView()._get_or_create_product(VALID_EAN, make_api_data())
        self.assertEqual(product.ean_code, VALID_EAN)
        self.assertEqual(product.company.name, "Test Corp")
        self.assertEqual(product.company.country.name, "Germany")
        self.assertEqual(product.category.name, "Snacks")

    def test_get_or_create_is_idempotent(self):
        from add_food.views import AddProductView
        view = AddProductView()
        view._get_or_create_product(VALID_EAN, make_api_data())
        view._get_or_create_product(VALID_EAN, make_api_data())
        self.assertEqual(Product.objects.filter(ean_code=VALID_EAN).count(), 1)

    def test_get_or_create_handles_integrity_error(self):
        from add_food.views import AddProductView

        product = make_product()

        view = AddProductView()

        with patch(
            "add_food.views.Product.objects.get_or_create",
            side_effect=IntegrityError,
        ):
            result = view._get_or_create_product(VALID_EAN, make_api_data())

        self.assertEqual(result.pk, product.pk)
        self.assertEqual(result.ean_code, VALID_EAN)