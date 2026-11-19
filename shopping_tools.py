"""Stage 3 agent tools backed by the Stage 2 shopping functions."""

from smolagents import tool

import product_ranking
import product_search


@tool
def search_products(keyword: str) -> list[dict]:
    """Retrieve all normalized sample product matches from DummyJSON.

    Args:
        keyword: Nonempty product search keyword. Surrounding spaces are removed.
    """
    return product_search.search_all_products(keyword)


@tool
def filter_products(
    products: list[dict],
    max_budget: float | None = None,
    min_rating: float | None = None,
    brand: str | None = None,
    category: str | None = None,
) -> list[dict]:
    """Return all products that meet every active constraint, in input order.

    Args:
        products: Full list of normalized records from the search tool.
        max_budget: Inclusive maximum price. Omit to allow any price.
        min_rating: Inclusive minimum rating from 0 to 5. Omit to allow any rating.
        brand: Exact brand, ignoring case and surrounding spaces. Omit for any brand.
        category: Exact category, ignoring case and surrounding spaces. Omit for any category.
    """
    return product_ranking.filter_products(
        products, max_budget=max_budget, min_rating=min_rating, brand=brand, category=category
    )


@tool
def rank_products(
    products: list[dict], price_weight: float = 0.5, rating_weight: float = 0.5
) -> list[dict]:
    """Return up to five eligible products ordered by weighted price and rating score.

    Args:
        products: All normalized records that passed mandatory filtering. Use the full search result if there are no constraints.
        price_weight: Weight for lower prices, between 0 and 1. Defaults to 0.5.
        rating_weight: Weight for higher ratings, between 0 and 1. Defaults to 0.5. Both weights must sum to 1.
    """
    return product_ranking.rank_products(
        products, price_weight=price_weight, rating_weight=rating_weight
    )
