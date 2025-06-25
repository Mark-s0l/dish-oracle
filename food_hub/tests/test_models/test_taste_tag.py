from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError

from food_hub.models import TasteTag


class TestTasteTag:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "name, taste_type, slug, expectation",
        [
            ("cладкий", "P", "sladkiy", does_not_raise()),
            ("горький", "N", "gorkaiu", does_not_raise()),
            (777, "P", "kisliy", pytest.raises(ValidationError)),
            ("соленый", "O", "solonyy", pytest.raises(ValidationError)),
            ("$#)", "N", "$#)", pytest.raises(ValidationError)),
            ("кислый", "N", 0, pytest.raises(ValidationError)),
            ("spicy", "P", "spicy", does_not_raise()),
            ("swäet", "P", "swaet", pytest.raises(ValidationError)),
            ("вáнильный", "P", "vanilnyy", pytest.raises(ValidationError)),
            ("m$nt", "P", "mint", pytest.raises(ValidationError)),
            (" ", "N", "void", pytest.raises(ValidationError)),
            ("strawberry", "P", " ", pytest.raises(ValidationError)),
            ("crimson", "P", "", pytest.raises(ValidationError)),
            ("", "P", "nothing", pytest.raises(ValidationError)),
            ("apple", "", "apple", pytest.raises(ValidationError)),
            ("персиковый1", "P", "peach", pytest.raises(ValidationError)),
            ("вишнёвый", "P", "cherry", does_not_raise()),
            ("apple", "", "apple", pytest.raises(ValidationError)),
            ("молочный", "P", "1actic", pytest.raises(ValidationError)),
            ("лаймовый", "В", "lime", pytest.raises(ValidationError)),
            ("абрикосовый", "Ü", "apricot", pytest.raises(ValidationError)),
            ("апельсиновый", 4, "orange", pytest.raises(ValidationError)),
        ],
    )
    def test_taste_tag_validation(
        self, name, taste_type, slug, expectation, save_and_clean
    ):
        tag = TasteTag(name=name, taste_type=taste_type, slug=slug)
        with expectation:
            save_and_clean(tag)
            assert tag.name == name
            assert tag.taste_type == taste_type
            assert tag.slug == slug

    @pytest.mark.django_db
    def test_taste_tag_duplicate_name(self, save_and_clean):
        tag1 = TasteTag(name="солёный", taste_type="P", slug="soleniy")
        save_and_clean(tag1)
        tag2 = TasteTag(name="солёный", taste_type="N", slug="soleniy2")
        with pytest.raises(ValidationError):
            save_and_clean(tag2)

    @pytest.mark.django_db
    def test_taste_tag_duplicate_slug(self, save_and_clean):
        tag1 = TasteTag(name="мятный", taste_type="P", slug="myatniy")
        save_and_clean(tag1)
        tag2 = TasteTag(name="мятный2", taste_type="N", slug="myatniy")
        with pytest.raises(ValidationError):
            save_and_clean(tag2)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "field,value,expectation",
        [
            ("name", "a" * 51, pytest.raises(ValidationError)),
            ("slug", "b" * 51, pytest.raises(ValidationError)),
            ("name", "a" * 50, does_not_raise()),
            ("slug", "b" * 50, does_not_raise()),
        ],
    )
    def test_taste_tag_field_length(self, field, value, expectation, save_and_clean):
        kwargs = {"name": "testname", "taste_type": "P", "slug": "testslug"}
        kwargs[field] = value
        with expectation:
            tag = TasteTag(**kwargs)
            save_and_clean(tag)
