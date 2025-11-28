# add_food/tests/test_save_image.py

import os

from add_food.services import save_image


def test_save_image_success(mocker, settings, tmp_path):
    # download_image вернул байты → пишем файл
    mock_download = mocker.patch(
        "add_food.services.download_image",
        return_value=b"fakebinarydata",
    )
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mock_makedirs = mocker.patch("os.makedirs")

    settings.MEDIA_ROOT = tmp_path
    data = {"product": {"barcode": "123"}}
    image_url = "http://example.com/image.jpg"

    result = save_image(data, image_url)

    expected_dir = tmp_path / "products"
    mock_makedirs.assert_called_once_with(str(expected_dir), exist_ok=True)
    mock_open.assert_called_once_with(str(expected_dir / "image.jpg"), "wb")
    mock_download.assert_called_once_with(image_url)

    assert result == os.path.join("products", "image.jpg")


def test_save_image_download_fails(mocker, settings, tmp_path):
    # download_image вернул None → используем дефолтную картинку
    mock_download = mocker.patch(
        "add_food.services.download_image",
        return_value=None,
    )
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mock_makedirs = mocker.patch("os.makedirs")

    settings.MEDIA_ROOT = tmp_path
    data = {"product": {"barcode": "123"}}
    image_url = "http://example.com/image.jpg"

    result = save_image(data, image_url)

    expected_rel = os.path.join("products", "default_image.png")

    mock_download.assert_called_once_with(image_url)
    mock_makedirs.assert_not_called()
    mock_open.assert_not_called()

    assert result == expected_rel


def test_save_image_oserror(mocker, settings, tmp_path):
    mocker.patch("add_food.services.download_image", return_value=b"123")

    mock_open = mocker.patch(
        "builtins.open",
        side_effect=OSError("disk error"),
    )
    mock_makedirs = mocker.patch("os.makedirs")

    settings.MEDIA_ROOT = tmp_path
    data = {"product": {"barcode": "123"}}
    image_url = "http://example.com/image.jpg"

    result = save_image(data, image_url)

    expected_rel = os.path.join("products", "default_image.png")
    assert result == expected_rel

    mock_makedirs.assert_called_once()
    mock_open.assert_called_once()


def test_save_image_when_image_url_none(mocker, settings, tmp_path):
    # В текущей реализации save_image всё равно вызовет download_image(None)
    settings.MEDIA_ROOT = tmp_path

    mock_download = mocker.patch(
        "add_food.services.download_image",
        return_value=None,
    )
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mock_makedirs = mocker.patch("os.makedirs")

    data = {"product": {"barcode": "123"}}

    result = save_image(data, None)

    expected_rel = os.path.join("products", "default_image.png")

    mock_download.assert_called_once_with(None)
    mock_makedirs.assert_not_called()
    mock_open.assert_not_called()
    assert result == expected_rel
