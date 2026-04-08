from unittest.mock import Mock, patch

import pytest
import requests

from add_food.services import api_request, ApiError, ProductNotFoundError, ResponseTimeOutError, ResponseConnectionError, ValueReadingJsonError


@pytest.fixture
def mock_requests_get():
    with patch("add_food.services.requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def product_json():
    return {"balance": 105, "product": {...}}


def test_api_404(mock_requests_get):
    mock_response = Mock(status_code=404)
    mock_response.json.return_value = {"detail": "Not Found"}
    mock_requests_get.return_value = mock_response
    with pytest.raises(ProductNotFoundError):
        api_request("123")


@pytest.mark.parametrize("status_code", [401, 403, 500, 502, 503])
def test_api_errors(mock_requests_get, status_code):
    mock_response = Mock(status_code=status_code)
    mock_response.json.return_value = {"detail": "Error"}
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        str(status_code)
    )
    mock_requests_get.return_value = mock_response

    with pytest.raises(ApiError):
        api_request("4607145590012")


def test_api_invalid_json(mock_requests_get):
    mock_response = Mock(status_code=200)
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Invalid JSON")

    mock_requests_get.return_value = mock_response

    with pytest.raises(ApiError):
        api_request("4607145590012")

def test_api_timeout(mock_requests_get):
    mock_requests_get.side_effect = requests.exceptions.Timeout()

    with pytest.raises(ApiError):
        api_request("4607145590012")


def test_api_another_raise(mock_requests_get):
    mock_requests_get.side_effect = requests.exceptions.RequestException()
    with pytest.raises(ApiError):
        api_request("4607145590012")


def test_api_successfully(mock_requests_get, product_json):
    mock_response = Mock(status_code=200)
    mock_response.json.return_value = product_json
    mock_requests_get.return_value = mock_response

    result = api_request("4607145590012")
    assert isinstance(result, dict)
    assert "product" in result
