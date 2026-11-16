"""Retrieve sample products and select the cheapest keyword matches."""

from math import isfinite

import requests

API_URL = "https://dummyjson.com/products/search"


class ProductSearchError(Exception):
    """A readable failure to retrieve usable product information."""


def cheapest_products(records: list) -> list[dict]:
    """Validate prices, sort every match numerically, and keep up to five."""
    products = []
    for record in records:
        if not isinstance(record, dict):
            raise ProductSearchError("The dataset returned an invalid product record.")
        try:
            price = float(record["price"])
            title = record["title"]
            if (isinstance(record["price"], bool) or not isfinite(price)
                    or price < 0 or not isinstance(title, str) or not title.strip()):
                raise ValueError
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ProductSearchError("The dataset returned a product with an invalid name or price.") from exc
        images = record.get("images")
        image = record.get("thumbnail")
        if not image and isinstance(images, list) and images:
            image = images[0]
        products.append({"title": title, "price": price, "image": image})
    return sorted(products, key=lambda product: product["price"])[:5]


def optional_number(value, *, minimum=0, maximum=None) -> float | None:
    """Return a supported finite number, or None for unknown/invalid data."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not isfinite(number) or number < minimum:
        return None
    if maximum is not None and number > maximum:
        return None
    return number


def optional_text(value) -> str | None:
    """Preserve display casing while removing surrounding whitespace."""
    return value.strip() or None if isinstance(value, str) else None


def normalize_product(record: dict) -> dict:
    """Normalize known fields without filling in missing specifications.

    Dimensions preserve reported axis values only. Their units are unverified,
    so this stage does not support physical size or dimension constraints.
    """
    product = cheapest_products([record])[0]
    dimensions = record.get("dimensions")
    product.update({
        "id": optional_number(record.get("id")),
        "brand": optional_text(record.get("brand")),
        "category": optional_text(record.get("category")),
        "rating": optional_number(record.get("rating"), maximum=5),
        "dimensions": {
            axis: optional_number(dimensions.get(axis))
            if isinstance(dimensions, dict) else None
            for axis in ("width", "height", "depth")
        },
    })
    return product


def fetch_product_records(keyword: str) -> list[dict]:
    """Retrieve every matching record without sorting or truncating."""
    keyword = keyword.strip()
    if not keyword:
        return []
    try:
        response = requests.get(API_URL, params={"q": keyword, "limit": 0}, timeout=15)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ProductSearchError("Could not load products from DummyJSON. Please try again.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("products"), list):
        raise ProductSearchError("DummyJSON returned an unexpected response. Please try again.")
    return data["products"]


def search_all_products(keyword: str) -> list[dict]:
    """Return all normalized matches in API order for Stage 2 filtering."""
    return [normalize_product(record) for record in fetch_product_records(keyword)]


def search_products(keyword: str) -> list[dict]:
    """Preserve Stage 1's five-cheapest result shape and ordering."""
    return cheapest_products(fetch_product_records(keyword))
