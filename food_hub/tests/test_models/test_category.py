from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError

from food_hub.models import Category


class TestCategory:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "name, expectation",
        [
            ("Молочные продукты", does_not_raise()),
            (" ", pytest.raises(ValidationError)),
            ("", pytest.raises(ValidationError)),
            (5, pytest.raises(ValidationError)),
            ("a" * 51, pytest.raises(ValidationError)),
            ("Рыбные прÖдукты", pytest.raises(ValidationError)),
        ],
    )
    def test_taste_tag_validation(self, name, expectation, save_and_clean):
        with expectation:
            tag = Category(name=name)

            save_and_clean(tag)
            assert tag.name == name

    @pytest.mark.django_db
    def test_country_duplicate_name(self, save_and_clean):
        first_category = Category(name="Фрукты")
        save_and_clean(first_category)
        second_category = Category(name="Фрукты")
        with pytest.raises(ValidationError):
            save_and_clean(second_category)
