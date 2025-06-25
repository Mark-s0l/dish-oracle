import pytest
from django.core.exceptions import ValidationError

from food_hub.models import Company, Country


class TestCompanyCountry:
    @pytest.mark.django_db
    def test_company_country_fk_success(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Вкуснотеево", country=country)
        save_and_clean(company)
        assert company.country == country
        assert company.country.name == "Россия"

    @pytest.mark.django_db
    def test_company_country_fk_required(self, save_and_clean):
        company = Company(name="Вкуснотеево", country=None)
        with pytest.raises(ValidationError):
            save_and_clean(company)

    @pytest.mark.django_db
    def test_company_country_delete_protect(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Вкуснотеево", country=country)
        save_and_clean(company)
        with pytest.raises(Exception):
            country.delete()

    @pytest.mark.django_db
    def test_company_country_change_fk(self, save_and_clean):
        country1 = Country(name="Россия")
        country2 = Country(name="Беларусь")
        save_and_clean(country1)
        save_and_clean(country2)
        company = Company(name="Вкуснотеево", country=country1)
        save_and_clean(company)
        company.country = country2
        save_and_clean(company)
        assert company.country == country2

    @pytest.mark.django_db
    def test_company_delete_country_remains(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company = Company(name="Вкуснотеево", country=country)
        save_and_clean(company)
        company.delete()
        assert Country.objects.filter(name="Россия").exists()

    @pytest.mark.django_db
    def test_country_delete_after_companies_deleted(self, save_and_clean):
        country = Country(name="Россия")
        save_and_clean(country)
        company1 = Company(name="Вкуснотеево", country=country)
        company2 = Company(name="Барилла", country=country)
        save_and_clean(company1)
        save_and_clean(company2)
        company1.delete()
        company2.delete()
        country.delete()
        assert not Country.objects.filter(name="Россия").exists()
