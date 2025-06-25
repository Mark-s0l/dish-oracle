from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError

from food_hub.models import Country


class TestCountry:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "name, expectation",
        [
            ("Япония", does_not_raise()),
            (" ", pytest.raises(ValidationError)),
            ("", pytest.raises(ValidationError)),
            (5, pytest.raises(ValidationError)),
            ("a" * 31, pytest.raises(ValidationError)),
            ("РÖссия", pytest.raises(ValidationError)),
        ],
    )
    def test_country_validation(self, name, expectation, save_and_clean):
        with expectation:
            country = Country(name=name)

            save_and_clean(country)
            assert country.name == name

    @pytest.mark.django_db
    def test_taste_tag_duplicate_name(self, save_and_clean):
        first_country = Country(name="Беларусь")
        save_and_clean(first_country)
        second_country = Country(name="Беларусь")
        with pytest.raises(ValidationError):
            save_and_clean(second_country)
