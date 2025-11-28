import requests

from add_food.services import MAX_IMAGE_BYTES, download_image


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

    assert download_image("http://x") is None


def test_download_image_declared_too_large(mocker):
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {
        "Content-Type": "image/jpeg",
        "Content-Length": str(MAX_IMAGE_BYTES + 1),
    }
    mock_resp.iter_content.return_value = []

    mocker.patch("requests.get", return_value=mock_resp)

    assert download_image("http://x") is None


def test_download_image_real_size_too_large(mocker):
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "image/png"}

    huge_chunk = b"0" * (MAX_IMAGE_BYTES + 100)
    mock_resp.iter_content.return_value = [huge_chunk]

    mocker.patch("requests.get", return_value=mock_resp)

    assert download_image("http://x") is None


def test_download_image_invalid_image(mocker):
    mock_resp = mocker.Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.headers = {"Content-Type": "image/jpeg"}

    # данные не являются картинкой
    mock_resp.iter_content.return_value = [b"not-an-image"]

    mocker.patch("requests.get", return_value=mock_resp)

    assert download_image("http://x") is None


def test_download_image_timeout(mocker):
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    assert download_image("http://x") is None
