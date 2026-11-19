from unittest.mock import Mock

import pytest

import product_search
import shopping_tools


@pytest.fixture
def sample_phones():
    return [
        {"id": 1, "title": "Budget phone", "price": 200, "rating": 4.0},
        {"id": 2, "title": "Top-rated phone", "price": 600, "rating": 4.8},
        {"id": 3, "title": "Over-budget phone", "price": 601, "rating": 5.0},
        {"id": 4, "title": "Low-rated phone", "price": 150, "rating": 3.9},
    ]


def test_search_tool_returns_normalized_records(monkeypatch, sample_phones):
    response = Mock()
    response.json.return_value = {"products": sample_phones}
    mock_get = Mock(return_value=response)
    monkeypatch.setattr(product_search.requests, "get", mock_get)

    matches = shopping_tools.search_products(keyword=" phone ")

    assert [product["id"] for product in matches] == [1, 2, 3, 4]
    assert matches[0]["brand"] is None
    assert mock_get.call_args.kwargs["params"] == {"q": "phone", "limit": 0}
    response.raise_for_status.assert_called_once_with()


def test_filter_tool_applies_inclusive_budget_and_rating(sample_phones):
    eligible = shopping_tools.filter_products(
        products=sample_phones, max_budget=600, min_rating=4.0
    )

    assert [product["id"] for product in eligible] == [1, 2]


def test_rank_tool_orders_eligible_products_by_weighted_score(sample_phones):
    eligible = shopping_tools.filter_products(
        products=sample_phones, max_budget=600, min_rating=4.0
    )

    ranked = shopping_tools.rank_products(
        products=eligible, price_weight=0.1, rating_weight=0.9
    )

    assert [product["id"] for product in ranked] == [2, 1]
    assert [product["score"] for product in ranked] == pytest.approx([0.864, 0.82])
