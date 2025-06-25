import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from food_hub.models import Category, Company, Country, Product, ProductRating

class TestProductRatingProduct():
    @pytest.mark.django_db
    def test_productrating_product_fk_success(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Десерты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="4006381333931",
            img_field=SimpleUploadedFile(
                "test.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=5)
        save_and_clean(rating)
        assert rating.product == product
        assert rating.product.name == "Мороженое"


    @pytest.mark.django_db
    def test_productrating_product_fk_required(self, save_and_clean):
        rating = ProductRating(product=None, rate=4)
        with pytest.raises(ValidationError):
            save_and_clean(rating)


    @pytest.mark.django_db
    def test_productrating_delete_does_not_delete_product(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Десерты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Эклер",
            ean_code="9780306406157",
            img_field=SimpleUploadedFile(
                "test2.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=3)
        save_and_clean(rating)
        rating.delete()
        assert Product.objects.filter(pk=product.pk).exists()


    @pytest.mark.django_db
    def test_product_delete_cascades_to_ratings(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Десерты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Пирожное",
            ean_code="9781861972712",
            img_field=SimpleUploadedFile(
                "test3.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=4)
        save_and_clean(rating)
        product.delete()
        assert not ProductRating.objects.filter(pk=rating.pk).exists()


    @pytest.mark.django_db
    def test_productrating_change_product(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Десерты")
        save_and_clean(category)
        product1 = Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="5012345678900",
            img_field=SimpleUploadedFile(
                "test4.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        product2 = Product(
            company=company,
            category=category,
            name="Эклер",
            ean_code="5901234123457",
            img_field=SimpleUploadedFile(
                "test5.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product1)
        save_and_clean(product2)
        rating = ProductRating(product=product1, rate=2)
        save_and_clean(rating)
        rating.product = product2
        save_and_clean(rating)
        assert rating.product == product2


    @pytest.mark.django_db
    def test_multiple_ratings_for_one_product(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Десерты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Мороженое",
            ean_code="5012345678900",
            img_field=SimpleUploadedFile(
                "test6.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating1 = ProductRating(product=product, rate=5)
        rating2 = ProductRating(product=product, rate=4)
        save_and_clean(rating1)
        save_and_clean(rating2)
        ratings = list(ProductRating.objects.filter(product=product))
        assert set(ratings) == {rating1, rating2}
        assert ProductRating.objects.filter(product=product).count() == 2
