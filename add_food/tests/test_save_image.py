import os

from add_food.services import save_image, ImageDownloadError

def test_save_image_success(mocker, settings, tmp_path):
    mock_download = mocker.patch(
        "add_food.services.download_image",
        return_value=b"fake_image_data"
    )

    mock_save = mocker.patch(
        "add_food.services.default_storage.save",
        return_value="products/image.jpg"
    )

    data = {"product": {"barcode": "123"}}
    image_url = "http://example.com/image.jpg"

    result = save_image(data, image_url)

    mock_download.assert_called_once_with(image_url)

    mock_save.assert_called_once()

    called_path = mock_save.call_args.args[0]
    called_content = mock_save.call_args.args[1]

    assert called_path == "products/image.jpg"
    assert called_content.read() == b"fake_image_data"

    assert result == "products/image.jpg"


def test_save_image_download_error(mocker, settings, tmp_path):
    mocker.patch(
        "add_food.services.download_image",
        side_effect=ImageDownloadError("Failed to download")
    )

    mock_save = mocker.patch(
        "add_food.services.default_storage.save",
        return_value="products/image.jpg"
    )

    data = {"product": {"barcode": "123"}}
    image_url = "http://example.com/image.jpg"

    result = save_image(data, image_url)

    mock_save.assert_not_called()

    assert result == "products/default_image.png"

def test_save_image_url_is_none(mocker, settings, tmp_path):
    mock_download = mocker.patch(
        "add_food.services.download_image",
        return_value=None
    )

    mock_save = mocker.patch(
        "add_food.services.default_storage.save",
        return_value="products/image.jpg"
    )

    data = {"product": {"barcode": "123"}}

    result = save_image(data, None)

    mock_download.assert_not_called()

    mock_save.assert_not_called()

    assert result == "products/default_image.png"


def test_save_image_storage_error(mocker, settings, tmp_path):
    mocker.patch(
        "add_food.services.download_image",
        return_value=b"image_data"
    )

    mocker.patch(
        "add_food.services.default_storage.save",
        side_effect=Exception("Disk full")
    )

    data = {"product": {"barcode": "123"}}
    image_url = "http://example.com/image.jpg"

    result = save_image(data, image_url)

    assert result == "products/default_image.png"

def test_save_image_with_real_storage(mocker, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    mocker.patch(
        "add_food.services.download_image",
        return_value=b"fake_png_data"
    )

    data = {"product": {"barcode": "123"}}
    image_url = "http://example.com/image.jpg"

    result = save_image(data, image_url)

    assert result.startswith("products/")

    full_path = os.path.join(settings.MEDIA_ROOT, result)
    assert os.path.exists(full_path)

    with open(full_path, "rb") as f:
        assert f.read() == b"fake_png_data"
