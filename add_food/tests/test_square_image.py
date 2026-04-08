from add_food.services import get_square_image


def test_get_square_image_returns_square_image_url():
    data = {
        "product": {
            "barcode": "1234567890123",
            "images": [
                {"width": 200, "height": 100, "url": "http://example.com/rect.jpg"},
                {"width": 150, "height": 150, "url": "http://example.com/square.jpg"},
                {"width": 300, "height": 600, "url": "http://example.com/another.jpg"},
            ],
        }
    }

    assert get_square_image(data) == "http://example.com/square.jpg"


def test_get_square_image_returns_first_when_no_square():
    data = {
        "product": {
            "barcode": "9876543210987",
            "images": [
                {"width": 120, "height": 180, "url": "http://example.com/first.jpg"},
                {"width": 200, "height": 100, "url": "http://example.com/second.jpg"},
            ],
        }
    }

    assert get_square_image(data) == "http://example.com/first.jpg"


def test_get_square_image_returns_none_when_no_images():

    data_no_images = {"product": {"barcode": "0000000000000", "images": []}}
    assert get_square_image(data_no_images) is None

    data_missing_product = {}
    assert get_square_image(data_missing_product) is None


def test_get_square_image_considers_missing_dimensions_as_equal():
    data = {
        "product": {
            "barcode": "1111111111111",
            "images": [
                {"url": "http://example.com/no_dims.jpg"},
                {"width": 120, "height": 180, "url": "http://example.com/rect.jpg"},
            ],
        }
    }

    assert get_square_image(data) == "http://example.com/no_dims.jpg"

def test_get_square_image_skips_image_without_url():
    data = {
        "product": {
            "barcode": "1234567890123",
            "images": [
                {"width": 150, "height": 150, "url": None},        # ← пропускается
                {"width": 200, "height": 200, "url": "http://example.com/square.jpg"},
            ],
        }
    }
    assert get_square_image(data) == "http://example.com/square.jpg"