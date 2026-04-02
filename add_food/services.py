import logging
import os
from io import BytesIO
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image


class ApiError(Exception):
    pass


class ProductNotFoundError(ApiError):
    pass


class ResponseTimeOutError(ApiError):
    pass


class ResponseConnectionError(ApiError):
    pass


class ValueReadingJsonError(ApiError):
    pass


class ImageDownloadError(ApiError):
    pass


class IncompleteDataError(ApiError):
    pass


logger = logging.getLogger("add_food")


def pick_lang(block: dict | None) -> str | None:
    if block is None:
        return None
    return block.get("ru") or block.get("en") or next(iter(block.values()), None)


def api_request(ean_code: str) -> dict:
    api_key = settings.EAN_DB_JWT
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    try:
        url = settings.EAN_DB_API_URL
        logger.info(f"[API] Sent request for ean={ean_code}")
        response = requests.get(f"{url}{ean_code}", headers=headers, timeout=10)

        if response.status_code == 404:
            logger.error(
                f"[API] Product not found ean={ean_code} error:404"
            )
            raise ProductNotFoundError("Ошибка, товар не был найден")

        response.raise_for_status()

        try:
            data = response.json()
            logger.info(f"[API] Successfully fetched data for ean={ean_code}")
            return data

        except ValueError:
            logger.error(f"[API] Invalid JSON received for ean={ean_code}")
            raise ValueReadingJsonError("Ошибка чтения данных")

    except requests.exceptions.Timeout:
        logger.error(f"[API] Timeout while requesting ean={ean_code}")
        raise ResponseTimeOutError("Превышено время ожидания")
    except requests.exceptions.RequestException as error:
        logger.error(
            f"[API] Request failed for ean={ean_code} {error}",
            exc_info=True,
        )
        raise ResponseConnectionError("Ошибка соединения")


def get_square_image(data: dict) -> str | None:
    product = data.get("product", {})
    ean_code = product.get("barcode")
    images = product.get("images", [])
    if images:
        for img in images:
            w = img.get("width")
            h = img.get("height")
            url = img.get("url")
            if url is None:
                continue
            logger.info(f"[IMAGES] another image {ean_code} - {url}")
            if w is not None and h is not None and w == h:
                logger.info(f"[IMAGES] Found 1:1 image for ean={ean_code}")
                return url

        logger.warning(f"[IMAGES] No 1:1 image found for ean={ean_code}, using first")
        return images[0].get("url")

    logger.warning(f"[IMAGES] No images found for ean={ean_code}")
    return None


def download_image(image_url: str | None) -> bytes:
    allowed_content_type = {"image/jpeg", "image/png"}
    max_image_bytes = 5 * 1024 * 1024
    if image_url is None:
        raise ImageDownloadError("Image url is None")
    try:
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        if content_type not in allowed_content_type:
            logger.warning(f"[IMAGES] Disallowed content type: {content_type}")
            raise ImageDownloadError("Disallowed content type")

        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = None
            else:
                if declared_size > max_image_bytes:
                    logger.warning(
                        f"[IMAGES] Declared file too large: {declared_size} bytes"
                    )
                    raise ImageDownloadError("Declared file too large")

        data = bytearray()
        for chunk in response.iter_content(8192):
            if not chunk:
                continue

            data.extend(chunk)

            if len(data) > max_image_bytes:
                logger.warning("[IMAGES] Actual size exceeded limit during download")
                raise ImageDownloadError("Actual size exceeded limit during download")

        try:
            with Image.open(BytesIO(data)) as img:
                img.verify()
        except Exception:
            logger.warning(
                "[IMAGES] Downloaded file is not a valid image", exc_info=True
            )
            raise ImageDownloadError("Downloaded file is not a valid image")

        return bytes(data)

    except requests.exceptions.RequestException:
        logger.error(f"[IMAGES] Connection error", exc_info=True)
        raise ImageDownloadError("Unknown connection error")


def save_image(data: dict, image_url: str | None) -> str:
    product = data.get("product", {})
    ean_code = product.get("barcode", "unknown")

    default_path = os.path.join("products", "default_image.png")
    if image_url is None:
        logger.error(f"[IMAGES] Image url is None; Return default image")
        return default_path

    try:
        image_bytes = download_image(image_url)
    except ImageDownloadError:
        logger.warning(f"[IMAGES] Using default image for ean={ean_code}")
        return default_path
    filename = os.path.basename(urlparse(image_url).path) or f"{ean_code}.jpg"
    relative_path = os.path.join("products", filename)
    try:
        actual_path = default_storage.save(relative_path, ContentFile(image_bytes))
        logger.info(f"[IMAGES] Image successfully saved for ean={ean_code}")
        return actual_path
    except Exception as error:
        logger.warning(
            f"[IMAGES] Failed to save image for ean={ean_code} | reason: {error}"
        )
        return default_path


def get_dict_data(data: dict, save_path: str) -> dict[str, str]:
    product = data.get("product", {})
    ean = product.get("barcode", "")
    manufacturer = product.get("manufacturer") or {}
    country = product.get("barcodeDetails", {}).get("country", "")

    name = pick_lang(product.get("titles", {}))
    company = pick_lang(manufacturer.get("titles", {}))

    categories = product.get("categories") or []
    category = pick_lang(categories[0].get("titles", {})) if categories else ""

    if not name or not company or not category or not country:
        logger.error(
            f"[DATA] Incomplete product data for ean={ean} | "
            f"name={name} | company={company} | "
            f"category={category} | country={country} | save_path={save_path}"
        )
        raise IncompleteDataError("Ошибка. Не все данные были найдены")

    logger.info(
        f"[DATA] Passing data to views with values: name={name} | "
        f"company={company} | category={category} | country={country}"
    )
    return {
        "company": company,
        "category": category,
        "name": name,
        "country": country,
        "save_path": save_path,
    }


def add_product(ean_code: str) -> dict[str, str]:
    """
    Fetches product data by EAN, downloads and saves its image.
    Returns dict with keys: company, category, name, country, save_path.
    Raises: ProductNotFoundError, IncompleteDataError, ResponseTimeOutError,
            ResponseConnectionError, ValueReadingJsonError.
    """
    response = api_request(ean_code)

    image_url = get_square_image(response)

    save_path = save_image(response, image_url)

    return get_dict_data(response, save_path)
