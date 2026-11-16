"""Isolated implementation using the explicit product-ranking task prompt."""

from math import isclose, isfinite


def _finite_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def _rating(product):
    number = _finite_number(product.get('rating'))
    return number if number is not None and 0 <= number <= 5 else None


def _tie_key(product):
    rating = _rating(product)
    return (-product['score'], product['price'],
            -rating if rating is not None else float('inf'),
            product['title'].strip().casefold(), product['id'])


def rank_candidates(products, price_weight=0.5, rating_weight=0.5):
    """Return at most five scored copies of already eligible products."""
    price_weight = _finite_number(price_weight)
    rating_weight = _finite_number(rating_weight)
    if (price_weight is None or rating_weight is None
            or price_weight < 0 or rating_weight < 0
            or not isclose(price_weight + rating_weight, 1, rel_tol=0, abs_tol=1e-9)):
        raise ValueError('Weights must be finite, nonnegative, and sum to one.')
    if not products:
        return []
    minimum = min(product['price'] for product in products)
    maximum = max(product['price'] for product in products)
    scored = []
    for product in products:
        price_score = (maximum - product['price']) / (maximum - minimum) if maximum != minimum else 1.0
        rating = _rating(product)
        rating_score = rating / 5 if rating is not None else 0.0
        scored.append({**product, 'price_score': price_score,
                       'rating_score': rating_score,
                       'score': price_weight * price_score + rating_weight * rating_score})
    return sorted(scored, key=_tie_key)[:5]
