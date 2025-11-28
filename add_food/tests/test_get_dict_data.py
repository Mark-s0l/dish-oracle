from add_food.services import get_dict_data


def test_get_dict_data_full_success(mocker):
    data = {
        "product": {
            "barcode": "123",
            "barcodeDetails": {"country": "RU"},
            "titles": {"ru": "Название"},
            "manufacturer": {"titles": {"ru": "Компания"}},
            "categories": [{"titles": {"ru": "Категория"}}],
        }
    }

    mocker.patch("add_food.services.get_quad_image", return_value="http://img")
    mocker.patch("add_food.services.save_image", return_value="saved/image.jpg")

    result = get_dict_data(data)

    assert result == {
        "company": "Компания",
        "category": "Категория",
        "name": "Название",
        "country": "RU",
        "save_path": "saved/image.jpg",
    }


def test_get_dict_data_missing_fields(mocker):
    data = {"product": {"barcode": "999"}}

    mocker.patch("add_food.services.get_quad_image", return_value=None)
    mocker.patch("add_food.services.save_image", return_value=None)

    result = get_dict_data(data)

    assert result is None


def test_get_dict_data_empty_dict(mocker):
    mocker.patch("add_food.services.get_quad_image", return_value=None)
    mocker.patch("add_food.services.save_image", return_value=None)

    assert get_dict_data({}) is None


def test_get_dict_data_language_fallback_to_en(mocker):
    data = {
        "product": {
            "barcode": "321",
            "barcodeDetails": {"country": "DE"},
            "titles": {"en": "English Name"},
            "manufacturer": {"titles": {"en": "English Company"}},
            "categories": [{"titles": {"en": "English Category"}}],
        }
    }

    mocker.patch("add_food.services.get_quad_image", return_value="http://img")
    mocker.patch("add_food.services.save_image", return_value="foo.jpg")

    result = get_dict_data(data)

    assert result["name"] == "English Name"
    assert result["company"] == "English Company"
    assert result["category"] == "English Category"
    assert result["country"] == "DE"
    assert result["save_path"] == "foo.jpg"


def test_get_dict_data_empty_categories(mocker):
    data = {
        "product": {
            "barcode": "777",
            "titles": {"ru": "Имя"},
            "manufacturer": {"titles": {"ru": "Компания"}},
            "barcodeDetails": {"country": "US"},
            "categories": [],
        }
    }

    mocker.patch("add_food.services.get_quad_image", return_value=None)
    mocker.patch("add_food.services.save_image", return_value=None)

    result = get_dict_data(data)
    assert result is None
