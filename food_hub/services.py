import requests
from django.conf import settings

def fetch_product_data(ean_code):
    """Возвращает dict с данными или None."""
    try:
        resp = requests.get(f"{settings.EAN_DB_API_URL}{ean_code}",
                            headers={"Authorization": f"Bearer {settings.EAN_DB_JWT}"},
                            timeout=5)
        resp.raise_for_status()
        data = resp.json().get("product") or {}
    except Exception:
        return None

    return {
        "name": data.get("titles", {}).get("ru") or data.get("titles", {}).get("en"),
        "company": (data.get("manufacturer", {}).get("titles") or {}).get("ru"),
        "country": data.get("barcodeDetails", {}).get("country"),
        "category": (data.get("categories") or [{}])[0].get("titles", {}).get("ru"),
        "image_url": (data.get("images") or [{}])[0].get("url"),
    }