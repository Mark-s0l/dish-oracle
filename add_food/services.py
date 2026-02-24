import logging
import os
import time
from io import BytesIO
from typing import Any

import requests
from django.conf import settings
from PIL import Image

logger = logging.getLogger("add_food")

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def get_api_url():
    return settings.EAN_DB_API_URL


def get_api_key():
    return settings.EAN_DB_JWT


def api_request(ean_code: str) -> dict[str, Any]:
    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    start = time.perf_counter()

    def elapsed() -> float:
        return time.perf_counter() - start

    try:
        url = get_api_url()
        response = requests.get(f"{url}{ean_code}", headers=headers, timeout=15)
        logger.info(f"[API] Sent request for ean={ean_code}")

        if response.status_code == 404:
            logger.error(
                f"[API] Product not found "
                f"(ean={ean_code}) | "
                f"error:404 | time:{elapsed():.3f}s"
            )
            return {"successful": False, "error": "Ошибка. Товар не был найден"}

        response.raise_for_status()

        try:
            data = response.json()
            logger.info(
                f"[API] Successfully fetched data for ean={ean_code} | "
                f"time:{elapsed():.3f}s"
            )
            return {"successful": True, "data": data}

        except ValueError:
            logger.error(
                f"[API] Invalid JSON received for ean={ean_code} | "
                f"time:{elapsed():.3f}s"
            )
            return {"successful": False, "error": "Ошибка обработки ответа"}

    except requests.exceptions.Timeout:
        logger.error(
            f"[API] Timeout while requesting ean={ean_code} | time:{elapsed():.3f}s"
        )
        return {"successful": False, "error": "Превышено время ожидания"}
    except requests.exceptions.RequestException as error:
        logger.error(
            f"[API] Request failed for ean={ean_code} | "
            f"{error} | time:{elapsed():.3f}s",
            exc_info=True,
        )
        return {"successful": False, "error": "Ошибка соединения"}


def get_quad_image(data: dict) -> str | None:
    product = data.get("product", {})
    ean_code = product.get("barcode")
    images = product.get("images", [])
    if images:
        for img in images:
            w = img.get("width")
            h = img.get("height")
            url = img.get("url")
            logger.info(f"[IMAGES] another image {ean_code} - {url}")
            if w is not None and h is not None and w == h:
                logger.info(f"[IMAGES] Found 1:1 image for ean={ean_code}")
                return url

        logger.warning(f"[IMAGES] No 1:1 image found for ean={ean_code}, using first")
        return images[0].get("url")

    logger.warning(f"[IMAGES] No images found for ean={ean_code}")
    return None


def download_image(image_url: str) -> bytes | None:
    try:
        response = requests.get(image_url, stream=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        if content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning(f"[IMAGES] Disallowed content type: {content_type}")
            return None

        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = None
            else:
                if declared_size > MAX_IMAGE_BYTES:
                    logger.warning(
                        f"[IMAGES] Declared file too large: {declared_size} bytes"
                    )
                    return None

        data = bytearray()
        for chunk in response.iter_content(8192):
            if not chunk:
                continue

            data.extend(chunk)

            if len(data) > MAX_IMAGE_BYTES:
                logger.warning("[IMAGES] Actual size exceeded limit during download")
                return None

        try:
            with Image.open(BytesIO(data)) as img:
                img.verify()
        except Exception:
            logger.warning(
                "[IMAGES] Downloaded file is not a valid image", exc_info=True
            )
            return None

        return bytes(data)

    except Exception as error:
        logger.error(f"[IMAGES] Unexpected error during download: {error}")
        return None


def save_image(data: dict, image_url: str | None) -> str:
    product = data.get("product", {})
    ean_code = product.get("barcode", "unknown")

    default_path = os.path.join("products", "default_image.png")

    image_bytes = download_image(image_url)

    if image_bytes is None:
        logger.warning(f"[IMAGES] Using default image for ean={ean_code}")
        return default_path

    filename = os.path.basename(image_url) or f"{ean_code}.jpg"
    save_dir = os.path.join(settings.MEDIA_ROOT, "products")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    relative_path = os.path.join("products", filename)

    try:
        with open(save_path, "wb") as f:
            f.write(image_bytes)
        logger.info(f"[IMAGES] Image successfully saved for ean={ean_code}")
        return relative_path
    except Exception as error:
        logger.warning(
            f"[IMAGES] Failed to save image for ean={ean_code} | reason: {error}"
        )
        return default_path


def get_dict_data(data: dict) -> dict[str, str] | None:
    product = data.get("product", {})
    ean = product.get("barcode", "")
    country = product.get("barcodeDetails", {}).get("country", "")

    def pick_lang(block: dict) -> str | None:
        if block is None:
            return None
        return block.get("ru") or block.get("en") or next(iter(block.values()), "")

    name = pick_lang(product.get("titles", {}))
    company = pick_lang(product.get("manufacturer", {}).get("titles", {}))

    categories = product.get("categories") or []
    category = pick_lang(categories[0].get("titles", {})) if categories else ""

    image_url = get_quad_image(data)
    save_path = save_image(data, image_url)

    if not name or not company or not category or save_path is None:
        logger.error(
            f"[DATA] Incomplete product data for ean={ean} | "
            f"name={name} | company={company} | "
            f"category={category} | country={country} | save_path={save_path}"
        )
        return None

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


def add_product(ean_code: str) -> dict[str, Any]:
    data = api_request(ean_code)
    if not data or data.get("successful") is False:
        return data
    return get_dict_data(data["data"])
