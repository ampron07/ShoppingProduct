"""Pure mandatory filtering and weighted ranking for normalized products."""

from math import isclose

from product_search import optional_number, optional_text


def _numeric_constraint(value, name, maximum=None):
    if value is None:
        return None
    number = optional_number(value, maximum=maximum)
    if number is None:
        bound = "nonnegative" if maximum is None else f"between 0 and {maximum}"
        raise ValueError(f"{name} must be a finite number {bound}.")
    return number


def _text_constraint(value, name):
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be text or None.")
    text = optional_text(value)
    return text.casefold() if text is not None else None


def filter_products(products: list[dict], *, max_budget=None, brand=None,
                    category=None, min_rating=None) -> list[dict]:
    """Apply all active constraints, preserving input order and all matches.

    None (or blank text) disables a constraint; numeric zero is active.
    Unknown required attributes fail closed. Dimensions/clothing size are not
    accepted filters because their meaning/units have not been verified.
    Products should come from search_all_products/normalize_product.
    """
    budget = _numeric_constraint(max_budget, "Maximum budget")
    rating_floor = _numeric_constraint(min_rating, "Minimum rating", maximum=5)
    wanted_brand = _text_constraint(brand, "Brand")
    wanted_category = _text_constraint(category, "Category")
    eligible = []
    for product in products:
        price = optional_number(product.get("price"))
        rating = optional_number(product.get("rating"), maximum=5)
        if budget is not None and (price is None or price > budget):
            continue
        if rating_floor is not None and (rating is None or rating < rating_floor):
            continue
        if wanted_brand is not None and _text_constraint(product.get("brand"), "Brand") != wanted_brand:
            continue
        if wanted_category is not None and _text_constraint(product.get("category"), "Category") != wanted_category:
            continue
        eligible.append(product)
    return eligible


def _ranking_key(product):
    rating = optional_number(product.get("rating"), maximum=5)
    identifier = optional_number(product.get("id"))
    return (
        -product["score"], product["price"],
        -rating if rating is not None else float("inf"),
        product["title"].strip().casefold(),
        identifier if identifier is not None else float("inf"),
    )


def rank_products(products: list[dict], *, price_weight=0.5, rating_weight=0.5,
                  max_budget=None, brand=None, category=None,
                  min_rating=None) -> list[dict]:
    """Filter all matches, score eligible products, then return the best five.

    Price score is (max-price)/(max-min) over eligible prices, or 1 when
    all prices tie. Rating score is rating/5; unknown ratings contribute 0
    without changing their displayed value. Weights must sum to 1 within
    absolute tolerance 1e-9. Scores remain unrounded. Ties use price, rating,
    normalized title, then ID. Inputs are normalized products and are not
    modified. The caller must pass all matches, not Stage 1's top five.
    """
    price_weight = optional_number(price_weight, maximum=1)
    rating_weight = optional_number(rating_weight, maximum=1)
    if (price_weight is None or rating_weight is None
            or not isclose(price_weight + rating_weight, 1, rel_tol=0, abs_tol=1e-9)):
        raise ValueError("Price and rating weights must be finite, nonnegative, and sum to 1.")
    eligible = filter_products(products, max_budget=max_budget, brand=brand,
                               category=category, min_rating=min_rating)
    if not eligible:
        return []
    prices = [optional_number(product.get("price")) for product in eligible]
    if any(price is None for price in prices):
        raise ValueError("Ranking requires valid nonnegative prices for every eligible product.")
    minimum, maximum = min(prices), max(prices)
    scored = []
    for product, price in zip(eligible, prices):
        price_score = (maximum - price) / (maximum - minimum) if maximum != minimum else 1.0
        rating = optional_number(product.get("rating"), maximum=5)
        rating_score = rating / 5 if rating is not None else 0.0
        scored.append({**product, "price": price,
                       "price_score": price_score, "rating_score": rating_score,
                       "score": price_weight * price_score + rating_weight * rating_score})
    return sorted(scored, key=_ranking_key)[:5]
