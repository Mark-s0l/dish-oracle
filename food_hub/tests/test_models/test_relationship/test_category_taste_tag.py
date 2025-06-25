import pytest
from django.core.exceptions import ValidationError

from food_hub.models import Category, TasteTag


class TestTasteTagM2MCategory:
    @pytest.mark.django_db
    def test_created(self, save_and_clean):
        tag_salty = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        tag_sour = TasteTag(name="кислый", taste_type="N", slug="kisliy")
        save_and_clean(tag_salty)
        save_and_clean(tag_sour)
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        category.taste_tags.add(tag_salty, tag_sour)
        assert tag_salty in category.taste_tags.all()
        assert tag_sour in category.taste_tags.all()

    @pytest.mark.django_db
    def test_taste_tags_deleted_unlinks_from_category(self, save_and_clean):
        tag_bitter = TasteTag(name="bitter", taste_type="N", slug="bitter")
        tag_sweet = TasteTag(name="сладкий", taste_type="P", slug="sweet")
        save_and_clean(tag_bitter)
        save_and_clean(tag_sweet)

        category = Category(name="Кондитерские изделия")
        save_and_clean(category)

        category.taste_tags.add(tag_bitter, tag_sweet)

        tag_bitter.delete()
        tag_sweet.delete()

        updated_tags = list(category.taste_tags.all())

        assert tag_bitter not in updated_tags
        assert tag_sweet not in updated_tags

    @pytest.mark.django_db
    def test_remove_taste_taag_from_category(self, save_and_clean):
        tag_sweet = TasteTag(name="сладкий", taste_type="P", slug="sweet")
        save_and_clean(tag_sweet)
        category = Category(name="Конфеты")
        save_and_clean(category)
        category.taste_tags.add(tag_sweet)
        assert tag_sweet in category.taste_tags.all()
        category.taste_tags.remove(tag_sweet)
        assert tag_sweet not in category.taste_tags.all()
        assert TasteTag.objects.filter(pk=tag_sweet.pk).exists()

    @pytest.mark.django_db
    def test_clear_taste_tags_from_category(self, save_and_clean):
        tag1 = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        tag2 = TasteTag(name="кислый", taste_type="N", slug="kisliy")
        save_and_clean(tag1)
        save_and_clean(tag2)
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        category.taste_tags.add(tag1, tag2)
        assert category.taste_tags.count() == 2
        category.taste_tags.clear()
        assert category.taste_tags.count() == 0
        assert TasteTag.objects.filter(pk=tag1.pk).exists()
        assert TasteTag.objects.filter(pk=tag2.pk).exists()

    @pytest.mark.django_db
    def test_related_name_categories(self, save_and_clean):
        tag = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        save_and_clean(tag)
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        category.taste_tags.add(tag)
        assert category in tag.categories.all()

    @pytest.mark.django_db
    def test_taste_tag_in_multiple_categories(self, save_and_clean):
        tag = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        save_and_clean(tag)
        cat1 = Category(name="Молочные продукты")
        cat2 = Category(name="Сыры")
        save_and_clean(cat1)
        save_and_clean(cat2)
        cat1.taste_tags.add(tag)
        cat2.taste_tags.add(tag)
        assert tag in cat1.taste_tags.all()
        assert tag in cat2.taste_tags.all()

    @pytest.mark.django_db
    def test_add_invalid_taste_tag_to_category(self, save_and_clean):
        tag = TasteTag(name="123", taste_type="P", slug="invalid")
        category = Category(name="Молочные продукты")
        save_and_clean(category)
        with pytest.raises(ValidationError):
            save_and_clean(tag)
            category.taste_tags.add(tag)
