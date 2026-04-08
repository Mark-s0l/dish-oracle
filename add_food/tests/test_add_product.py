import pytest

from add_food.services import (
    add_product,
    ApiError,
    ProductNotFoundError,
    IncompleteDataError,
    ResponseTimeOutError,
    ResponseConnectionError,
    ValueReadingJsonError,
)


def _product_data(
    titles=None,
    manufacturer_titles=None,
    categories=None,
    country="Россия",
):
    return {
        "product": {
            "barcode": "4600000000001",
            "titles": titles or {"ru": "Печенье", "en": "Cookie"},
            "manufacturer": {
                "titles": manufacturer_titles or {"ru": "Кондитер", "en": "Confectioner"},
            },
            "categories": categories or [{"titles": {"ru": "Сладости", "en": "Sweets"}}],
            "barcodeDetails": {"country": country},
            "images": [],
        }
    }


@pytest.fixture(autouse=True)
def patch_save_image(mocker):
    mocker.patch(
        "add_food.services.save_image",
        return_value="products/default_image.png",
    )


@pytest.fixture(autouse=True)
def patch_get_square_image(mocker):
    mocker.patch("add_food.services.get_square_image", return_value=None)


@pytest.fixture(autouse=True)
def patch_download_image(mocker):
    mocker.patch("add_food.services.download_image", return_value=b"fake")


@pytest.fixture(autouse=True)
def patch_api_request(mocker, product_json):
    mocker.patch("add_food.services.api_request", return_value=product_json)


@pytest.fixture
def product_json():
    return _product_data()


class TestAddProduct:

    def test_success(self, product_json):
        result = add_product("4600000000001")
        assert result == {
            "name": "Печенье",
            "company": "Кондитер",
            "category": "Сладости",
            "country": "Россия",
            "save_path": "products/default_image.png",
        }

    @pytest.mark.parametrize(
        "missing_field",
        [
            pytest.param("name", id="missing_name"),
            pytest.param("company", id="missing_company"),
            pytest.param("category", id="missing_category"),
            pytest.param("country", id="missing_country"),
        ],
    )
    def test_incomplete_data_raises(self, mocker, missing_field, product_json):
        data = _product_data()
        if missing_field == "name":
            data["product"]["titles"] = {}
        elif missing_field == "company":
            data["product"]["manufacturer"]["titles"] = {}
        elif missing_field == "category":
            data["product"]["categories"] = []
        elif missing_field == "country":
            data["product"]["barcodeDetails"]["country"] = ""

        mocker.patch("add_food.services.api_request", return_value=data)

        with pytest.raises(IncompleteDataError):
            add_product("4600000000001")

    def test_product_not_found(self, mocker):
        mocker.patch(
            "add_food.services.api_request",
            side_effect=ProductNotFoundError("Ошибка, товар не был найден"),
        )

        with pytest.raises(ProductNotFoundError):
            add_product("0000000000000")

    def test_timeout_raises(self, mocker):
        mocker.patch(
            "add_food.services.api_request",
            side_effect=ResponseTimeOutError("Превышено время ожидания"),
        )

        with pytest.raises(ResponseTimeOutError):
            add_product("4600000000001")

    def test_connection_error_raises(self, mocker):
        mocker.patch(
            "add_food.services.api_request",
            side_effect=ResponseConnectionError("Ошибка соединения"),
        )

        with pytest.raises(ResponseConnectionError):
            add_product("4600000000001")

    def test_invalid_json_raises(self, mocker):
        mocker.patch(
            "add_food.services.api_request",
            side_effect=ValueReadingJsonError("Ошибка чтения данных"),
        )

        with pytest.raises(ValueReadingJsonError):
            add_product("4600000000001")

    def test_all_exceptions_are_api_errors(self, mocker):
        mocker.patch(
            "add_food.services.api_request",
            side_effect=ProductNotFoundError("Не найден"),
        )

        with pytest.raises(ApiError):
            add_product("0000000000000")

    def test_no_image_url_returns_default(self, mocker):
        mocker.patch(
            "add_food.services.get_square_image",
            return_value=None,
        )

        result = add_product("4600000000001")
        assert result["save_path"] == "products/default_image.png"

    def test_with_image_url(self, mocker):
        mocker.patch(
            "add_food.services.get_square_image",
            return_value="http://example.com/img.png",
        )
        mocker.patch(
            "add_food.services.save_image",
            return_value="products/img.png",
        )

        result = add_product("4600000000001")
        assert result["save_path"] == "products/img.png"
