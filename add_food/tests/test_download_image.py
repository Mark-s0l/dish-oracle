import requests
import pytest
from add_food.services import download_image, ImageDownloadError

MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _mock_img_bytes():
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
        b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00"
        b"\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_download_image_success(mocker):
    img_bytes = _mock_img_bytes()

    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "image/png"}
    mock_resp.iter_content.return_value = [img_bytes]

    mocker.patch("requests.get", return_value=mock_resp)

    mock_img = mocker.MagicMock()
    mock_ctx = mocker.MagicMock()
    mock_ctx.__enter__.return_value = mock_img
    mock_ctx.__exit__.return_value = False

    mocker.patch("add_food.services.Image.open", return_value=mock_ctx)

    result = download_image("http://x")
    assert result == img_bytes


def test_download_image_disallowed_content_type(mocker):
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_resp.iter_content.return_value = []

    mocker.patch("requests.get", return_value=mock_resp)

    with pytest.raises(ImageDownloadError):
        download_image("http://x")


def test_download_image_declared_too_large(mocker):
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {
        "Content-Type": "image/jpeg",
        "Content-Length": str(MAX_IMAGE_BYTES + 1),
    }
    mock_resp.iter_content.return_value = []

    mocker.patch("requests.get", return_value=mock_resp)

    with pytest.raises(ImageDownloadError):
        download_image("http://x")


def test_download_image_real_size_too_large(mocker):
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "image/png"}

    huge_chunk = b"0" * (MAX_IMAGE_BYTES + 100)
    mock_resp.iter_content.return_value = [huge_chunk]

    mocker.patch("requests.get", return_value=mock_resp)

    with pytest.raises(ImageDownloadError):
        download_image("http://x")


def test_download_image_invalid_image(mocker):
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "image/jpeg"}

    mock_resp.iter_content.return_value = [b"not-an-image"]

    mocker.patch("requests.get", return_value=mock_resp)

    with pytest.raises(ImageDownloadError):
        download_image("http://x")


def test_download_image_timeout(mocker):
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(ImageDownloadError):
        download_image("http://x")


def test_download_image_connection_error(mocker):
    mocker.patch("requests.get", side_effect=requests.exceptions.ConnectionError)

    with pytest.raises(ImageDownloadError):
        download_image("http://x")


def test_download_image_none_url(mocker):
    with pytest.raises(ImageDownloadError, match="Image url is None"):
        download_image(None)


def test_download_image_invalid_content_length(mocker):
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {
        "Content-Type": "image/png",
        "Content-Length": "not-a-number",
    }

    img_bytes = _mock_img_bytes()
    mock_resp.iter_content.return_value = [img_bytes]

    mocker.patch("requests.get", return_value=mock_resp)

    mock_img = mocker.MagicMock()
    mock_ctx = mocker.MagicMock()
    mock_ctx.__enter__.return_value = mock_img
    mock_ctx.__exit__.return_value = False
    mocker.patch("add_food.services.Image.open", return_value=mock_ctx)

    result = download_image("http://x")
    assert result == img_bytes


def test_download_image_empty_chunks(mocker):
    img_bytes = _mock_img_bytes()

    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "image/png"}
    mock_resp.iter_content.return_value = [b"", b"", img_bytes]

    mocker.patch("requests.get", return_value=mock_resp)

    mock_img = mocker.MagicMock()
    mock_ctx = mocker.MagicMock()
    mock_ctx.__enter__.return_value = mock_img
    mock_ctx.__exit__.return_value = False
    mocker.patch("add_food.services.Image.open", return_value=mock_ctx)

    result = download_image("http://x")
    assert result == img_bytes


class TestImageDownloadErrorInheritance:

    def test_is_api_error(self):
        from add_food.services import ApiError

        assert issubclass(ImageDownloadError, ApiError)

    def test_instance_is_api_error(self):
        from add_food.services import ApiError

        err = ImageDownloadError("test")
        assert isinstance(err, ApiError)