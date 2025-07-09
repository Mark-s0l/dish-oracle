import os

import requests
from django.conf import settings


def safe_get(obj, *keys):
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key)
        elif isinstance(obj, list) and isinstance(key, int):
            if 0 <= key < len(obj):
                obj = obj[key]
            else:
                return None
        else:
            return None
    return obj


def download_image(image_url, save_dir):
    try:
        filename = os.path.basename(image_url) or "image_product.jpg"
        save_path = os.path.join(save_dir, filename)
        os.makedirs(save_dir, exist_ok=True)
        response = requests.get(image_url, stream=True, timeout=5)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        return f"product_images/{filename}"
    except Exception:
        return None


def fetch_product_data(ean_code):
    try:
        url = f"{settings.EAN_DB_API_URL}{ean_code}"
        headers = {"Authorization": f"Bearer {settings.EAN_DB_JWT}"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json().get("product", {})
    except Exception:
        return None

    image_url = safe_get(data, "images", 0, "url")
    image_path = (
        download_image(image_url, os.path.join(settings.MEDIA_ROOT, "product_images"))
        if image_url
        else None
    )

    return {
        "name": safe_get(data, "titles", "ru") or safe_get(data, "titles", "en"),
        "company": safe_get(data, "manufacturer", "titles", "ru"),
        "country": safe_get(data, "barcodeDetails", "country"),
        "category": safe_get(data, "categories", 0, "titles", "ru"),
        "image_path": image_path,
    }
