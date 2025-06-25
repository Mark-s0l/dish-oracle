import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from food_hub.models import (Category, Company, Country, Product,
                             ProductRating, TasteTag)


class TestTasteTagM2MProductRating:
    @pytest.mark.django_db
    def test_created(self, save_and_clean):
        tag_salty = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        tag_sour = TasteTag(name="кислый", taste_type="N", slug="kisliy")
        save_and_clean(tag_salty)
        save_and_clean(tag_sour)
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Йогурт",
            ean_code="4006381333931",
            img_field=SimpleUploadedFile(
                "test.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=5)
        save_and_clean(rating)
        rating.taste_tags.add(tag_salty, tag_sour)
        assert tag_salty in rating.taste_tags.all()
        assert tag_sour in rating.taste_tags.all()

    @pytest.mark.django_db
    def test_taste_tags_deleted_unlinks_from_rating(self, save_and_clean):
        tag_bitter = TasteTag(name="bitter", taste_type="N", slug="bitter")
        tag_sweet = TasteTag(name="сладкий", taste_type="P", slug="sweet")
        save_and_clean(tag_bitter)
        save_and_clean(tag_sweet)
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Кондитерские изделия")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Пончик",
            ean_code="9780306406157",
            img_field=SimpleUploadedFile(
                "test2.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=4)
        save_and_clean(rating)
        rating.taste_tags.add(tag_bitter, tag_sweet)
        tag_bitter.delete()
        tag_sweet.delete()
        updated_tags = list(rating.taste_tags.all())
        assert tag_bitter not in updated_tags
        assert tag_sweet not in updated_tags

    @pytest.mark.django_db
    def test_remove_taste_tag_from_rating(self, save_and_clean):
        tag_sweet = TasteTag(name="сладкий", taste_type="P", slug="sweet")
        save_and_clean(tag_sweet)
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Конфеты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Ириска",
            ean_code="9780306406157",
            img_field=SimpleUploadedFile(
                "test3.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=3)
        save_and_clean(rating)
        rating.taste_tags.add(tag_sweet)
        assert tag_sweet in rating.taste_tags.all()
        rating.taste_tags.remove(tag_sweet)
        assert tag_sweet not in rating.taste_tags.all()
        assert TasteTag.objects.filter(pk=tag_sweet.pk).exists()

    @pytest.mark.django_db
    def test_clear_taste_tags_from_rating(self, save_and_clean):
        tag1 = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        tag2 = TasteTag(name="кислый", taste_type="N", slug="kisliy")
        save_and_clean(tag1)
        save_and_clean(tag2)
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Кефир",
            ean_code="5012345678900",
            img_field=SimpleUploadedFile(
                "test4.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=2)
        save_and_clean(rating)
        rating.taste_tags.add(tag1, tag2)
        assert rating.taste_tags.count() == 2
        rating.taste_tags.clear()
        assert rating.taste_tags.count() == 0
        assert TasteTag.objects.filter(pk=tag1.pk).exists()
        assert TasteTag.objects.filter(pk=tag2.pk).exists()

    @pytest.mark.django_db
    def test_related_name_ratings(self, save_and_clean):
        tag = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        save_and_clean(tag)
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Сыр",
            ean_code="5901234123457",
            img_field=SimpleUploadedFile(
                "test5.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=5)
        save_and_clean(rating)
        rating.taste_tags.add(tag)
        assert rating in tag.ratings.all()

    @pytest.mark.django_db
    def test_taste_tag_in_multiple_ratings(self, save_and_clean):
        tag = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        save_and_clean(tag)
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Творог",
            ean_code="5012345678900",
            img_field=SimpleUploadedFile(
                "test6.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating1 = ProductRating(product=product, rate=4)
        rating2 = ProductRating(product=product, rate=5)
        save_and_clean(rating1)
        save_and_clean(rating2)
        rating1.taste_tags.add(tag)
        rating2.taste_tags.add(tag)
        assert tag in rating1.taste_tags.all()
        assert tag in rating2.taste_tags.all()

    @pytest.mark.django_db
    def test_add_invalid_taste_tag_to_rating(self, save_and_clean):
        tag = TasteTag(name="123", taste_type="P", slug="invalid")
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Компания", country=country)
        save_and_clean(company)
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        product = Product(
            company=company,
            category=category,
            name="Йогурт",
            ean_code="9781861972712",
            img_field=SimpleUploadedFile(
                "test7.jpg", b"filecontent", content_type="image/jpeg"
            ),
        )
        save_and_clean(product)
        rating = ProductRating(product=product, rate=5)
        save_and_clean(rating)
        with pytest.raises(ValidationError):
            save_and_clean(tag)
            rating.taste_tags.add(tag)
