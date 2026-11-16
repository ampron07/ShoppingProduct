"""Isolated attempt without explicit skill invocation in its task prompt."""

from math import isclose, isfinite


def _number(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if isfinite(result) else None


def rank_candidates(products, price_weight=0.5, rating_weight=0.5):
    """Return at most five scored copies of already eligible products."""
    price_weight, rating_weight = _number(price_weight), _number(rating_weight)
    if (price_weight is None or rating_weight is None
            or price_weight < 0 or rating_weight < 0
            or not isclose(price_weight + rating_weight, 1, abs_tol=1e-9, rel_tol=0)):
        raise ValueError('Weights must be finite, nonnegative, and sum to one.')
    if not products:
        return []
    low = min(p['price'] for p in products)
    high = max(p['price'] for p in products)
    decorated = []
    for p in products:
        rating = _number(p.get('rating'))
        if rating is not None and not 0 <= rating <= 5:
            rating = None
        price_score = (high - p['price']) / (high - low) if high != low else 1.0
        rating_score = rating / 5 if rating is not None else 0.0
        score = price_weight * price_score + rating_weight * rating_score
        result = dict(p, price_score=price_score, rating_score=rating_score, score=score)
        key = (-score, p['price'], -rating if rating is not None else float('inf'),
               p['title'].strip().casefold(), p['id'])
        decorated.append((key, result))
    decorated.sort(key=lambda pair: pair[0])
    return [result for _, result in decorated[:5]]
