from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError

from food_hub.models import Company, Country


class TestCompany:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "name, country_name, expectation",
        [
            ("Вкуснотеево", "Россия", does_not_raise()),
            (" ", "Германия", pytest.raises(ValidationError)),
            ("", "Беларусь", pytest.raises(ValidationError)),
            (5, "Япония", pytest.raises(ValidationError)),
            ("a" * 51, "Австрия", pytest.raises(ValidationError)),
            ("DanÖne", "Украина", pytest.raises(ValidationError)),
            ("Nestle", "ПÖльша", pytest.raises(ValidationError)),
            ("Nestle", "", pytest.raises(ValidationError)),
            ("Nestle", " ", pytest.raises(ValidationError)),
            ("Nestle", 11, pytest.raises(ValidationError)),
        ],
    )
    def test_company_validation(self, name, country_name, expectation, save_and_clean):
        with expectation:
            country_instance = None
            if isinstance(country_name, str) and country_name.strip():
                country_instance = Country(name=country_name)
                save_and_clean(country_instance)
            company = Company(name=name, country=country_instance)
            save_and_clean(company)
            assert company.name == name
            assert company.country == country_instance

    @pytest.mark.django_db
    def test_company_duplicate_name(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        first_company = Company(name="Barilla", country=country)
        save_and_clean(first_company)
        second_company = Company(name="Barilla", country=country)
        with pytest.raises(ValidationError):
            save_and_clean(second_company)
