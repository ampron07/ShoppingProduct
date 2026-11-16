from copy import deepcopy
from itertools import permutations
from unittest.mock import Mock

import pytest

from product_ranking import rank_products
from product_search import normalize_product, search_all_products, search_products


def product(identifier, price=10, rating=4, title="Phone", **fields):
    return normalize_product({"id": identifier, "title": title, "price": price,
                              "rating": rating, "brand": "Acme", "category": "phones", **fields})


def test_hand_calculated_scores():
    results = rank_products([product(1, 10, 2), product(2, 30, 5)],
                            price_weight=0.4, rating_weight=0.6)
    assert [p["id"] for p in results] == [1, 2]
    assert [p["price_score"] for p in results] == [1, 0]
    assert [p["rating_score"] for p in results] == [0.4, 1]
    assert [p["score"] for p in results] == pytest.approx([0.64, 0.60])


def test_equal_prices_and_single_product():
    results = rank_products([product(1, rating=1), product(2, rating=5)])
    assert [p["id"] for p in results] == [2, 1]
    assert [p["price_score"] for p in results] == [1, 1]
    assert [p["score"] for p in results] == pytest.approx([1, 0.6])
    assert rank_products([product(1, rating=2)])[0]["score"] == pytest.approx(0.7)


@pytest.mark.parametrize("rating", [None, "bad", True, -1, 6, "nan", "inf"])
def test_unknown_rating_penalty_does_not_invent_rating(rating):
    p = product(1, rating=rating)
    result = rank_products([p])[0]
    assert result["rating"] is None
    assert result["rating_score"] == 0
    assert result["score"] == 0.5
    assert rank_products([p], min_rating=0) == []


@pytest.mark.parametrize("weights,expected", [((1, 0), [1, 2]), ((0, 1), [2, 1])])
def test_zero_and_one_weights(weights, expected):
    results = rank_products([product(1, 10, 1), product(2, 20, 5)],
                            price_weight=weights[0], rating_weight=weights[1])
    assert [p["id"] for p in results] == expected


@pytest.mark.parametrize("weights", [(-0.1, 1.1), (True, 0), (0, False),
    (None, 1), ("nan", 1), ("inf", 0), (0.3, 0.3), (0, 0), (1, 1), (0.5, 0.50000001)])
def test_invalid_weights_rejected_even_for_empty_input(weights):
    with pytest.raises(ValueError, match="weights"):
        rank_products([], price_weight=weights[0], rating_weight=weights[1])


def test_weight_sum_tolerance():
    assert rank_products([], price_weight=0.5, rating_weight=0.5000000005) == []


def test_filter_before_normalization_all_conditions():
    eligible = [product(1, 10, 4), product(2, 20, 5)]
    excluded = [product(3, 0, 5, brand="Other"), product(4, 999, 5),
                product(5, 0, 1), product(6, 0, 5, category="watches")]
    conditions = dict(max_budget=20, brand=" ACME ", category=" PHONES ", min_rating=4)
    assert rank_products(eligible + excluded, **conditions) == rank_products(eligible, **conditions)
    assert rank_products(eligible, max_budget=9) == []
    assert rank_products([]) == []


def test_winner_outside_cheapest_five_using_mocked_api(monkeypatch):
    records = [{"id": i, "title": str(i), "price": i, "rating": 0} for i in range(1, 7)]
    records[-1]["rating"] = 5
    get = Mock()
    get.return_value.json.return_value = {"products": records}
    monkeypatch.setattr("product_search.requests.get", get)
    all_products = search_all_products("phone")
    results = rank_products(all_products, price_weight=0.1, rating_weight=0.9)
    assert len(results) == 5
    assert results[0]["id"] == 6
    assert len(search_products("phone")) == 5
    assert [p["price"] for p in search_products("phone")] == [1, 2, 3, 4, 5]


def test_ties_price_then_rating_then_title_then_id():
    # Identical scores: rating-only makes cheaper products win first.
    assert [p["id"] for p in rank_products([product(1, 20), product(2, 10)],
        price_weight=0, rating_weight=1)] == [2, 1]
    # Price-only ties: higher known ratings win, including valid zero over unknown.
    assert [p["id"] for p in rank_products([product(1, rating=None), product(2, rating=0),
        product(3, rating=5)], price_weight=1, rating_weight=0)] == [3, 2, 1]
    products = [product(3, title="Beta"), product(2, title=" alpha "), product(1, title="ALPHA")]
    for ordering in permutations(products):
        assert [p["id"] for p in rank_products(list(ordering))] == [1, 2, 3]


def test_missing_id_sorts_last():
    assert [p["id"] for p in rank_products([product(None), product(2)])] == [2, None]


def test_scoring_does_not_modify_input_and_keeps_precision():
    products = [product(1, rating=4.000001), product(2, rating=4.000002)]
    before = deepcopy(products)
    results = rank_products(products)
    assert products == before
    assert results[0]["id"] == 2
    assert results[0]["score"] > results[1]["score"]
    assert all(0 <= p["score"] <= 1 for p in results)


def test_invalid_price_cannot_be_ranked():
    with pytest.raises(ValueError, match="prices"):
        rank_products([{"title": "Bad price", "price": None}])
