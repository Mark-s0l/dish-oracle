from add_food.services import get_dict_data, IncompleteDataError, ApiError, pick_lang
import pytest

class TestGetDictData:
    def test_get_dict_data_full_success(self):
        data = {
            "product": {
                "barcode": "123",
                "barcodeDetails": {"country": "RU"},
                "titles": {"ru": "Название"},
                "manufacturer": {"titles": {"ru": "Компания"}},
                "categories": [{"titles": {"ru": "Категория"}}],
            }
        }

        result = get_dict_data(data, "saved/image.jpg")

        assert result == {
            "company": "Компания",
            "category": "Категория",
            "name": "Название",
            "country": "RU",
            "save_path": "saved/image.jpg",
        }


    def test_get_dict_data_missing_fields(self):
        data = {"product": {"barcode": "999"}}
        save_path = "saved/image.jpg"

        with pytest.raises((IncompleteDataError, ApiError)):
            result = get_dict_data(data, save_path)
            


    def test_get_dict_data_empty_dict(self):
        data = {None: {None: None}}
        save_path = "saved/image.jpg"

        with pytest.raises((IncompleteDataError, ApiError)):
            result = get_dict_data(data, save_path)
            


    def test_get_dict_data_language_fallback_to_en(self):
        data = {
            "product": {
                "barcode": "321",
                "barcodeDetails": {"country": "DE"},
                "titles": {"en": "English Name"},
                "manufacturer": {"titles": {"en": "English Company"}},
                "categories": [{"titles": {"en": "English Category"}}],
            }
        }

        save_path = "saved/image.jpg"
        result = get_dict_data(data, save_path)

        assert result["name"] == "English Name"
        assert result["company"] == "English Company"
        assert result["category"] == "English Category"
        assert result["country"] == "DE"
        assert result["save_path"] == "saved/image.jpg"


    def test_get_dict_data_empty_categories(self):
        data = {
            "product": {
                "barcode": "777",
                "titles": {"ru": "Имя"},
                "manufacturer": {"titles": {"ru": "Компания"}},
                "barcodeDetails": {"country": "US"},
                "categories": [],
            }
        }
        save_path = "saved/image.jpg"

        with pytest.raises((IncompleteDataError, ApiError)):
            result = get_dict_data(data, save_path)

class TestPickLang:
    def test_pick_lang_returns_ru(self):
        assert pick_lang({"ru": "Название", "en": "Name"}) == "Название"


    def test_pick_lang_fallback_to_en(self):
        assert pick_lang({"en": "Name"}) == "Name"


    def test_pick_lang_fallback_to_first_value(self):
        assert pick_lang({"de": "Name"}) == "Name"


    def test_pick_lang_empty_ru_fallback_to_en(self):
        assert pick_lang({"ru": "", "en": "Name"}) == "Name"


    def test_pick_lang_empty_dict(self):
        assert pick_lang({}) == None


    def test_pick_lang_none(self):
        assert pick_lang(None) is None


    def test_pick_lang_all_empty_strings(self):
        assert pick_lang({"ru": "", "en": ""}) == ""
