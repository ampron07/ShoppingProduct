from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests

from product_ranking import filter_products
from product_search import ProductSearchError, normalize_product, search_all_products, search_products


@pytest.fixture
def api(monkeypatch):
    get = Mock()
    monkeypatch.setattr("product_search.requests.get", get)
    return get


def record(identifier=1, **fields):
    return {"id": identifier, "title": f"Product {identifier}", "price": 100,
            "brand": "Acme", "category": "phones", "rating": 4, **fields}


def test_combined_constraints_from_mocked_api(api):
    api.return_value.json.return_value = {"products": [
        record(1, price="100", rating="4"), record(2, price=100.01),
        record(3, rating=3.99), record(4, brand="Acme Pro"),
        record(5, category="phone"), record(6, price=50, rating=5),
    ]}
    products = search_all_products(" phone ")
    eligible = filter_products(products, max_budget=100, min_rating=4,
                               brand=" ACME ", category=" PHONES ")
    assert [p["id"] for p in eligible] == [1, 6]
    api.assert_called_once_with("https://dummyjson.com/products/search",
                                params={"q": "phone", "limit": 0}, timeout=15)


def test_full_results_not_truncated_and_stage1_exact_shape(api):
    records = [record(i, price=str(i)) for i in range(8, 0, -1)]
    api.return_value.json.return_value = {"products": records}
    all_products = search_all_products("phone")
    assert len(filter_products(all_products)) == 8
    assert [p["id"] for p in all_products] == list(range(8, 0, -1))
    assert search_products("phone") == [
        {"title": f"Product {i}", "price": float(i), "image": None}
        for i in range(1, 6)
    ]


def test_normalization_preserves_unknowns_and_does_not_mutate():
    raw = record(price="12.50", brand=" ACME ", category=" phones ", rating="4.5",
                 dimensions={"width": "10", "height": True, "depth": "nan"})
    before = deepcopy(raw)
    result = normalize_product(raw)
    assert result["price"] == 12.5
    assert result["brand"] == "ACME"
    assert result["category"] == "phones"
    assert result["rating"] == 4.5
    assert result["dimensions"] == {"width": 10, "height": None, "depth": None}
    assert "size" not in result and "dimension_unit" not in result
    assert raw == before


@pytest.mark.parametrize("value", [None, "", "bad", True, -1, 5.01, "nan", "inf"])
def test_invalid_optional_rating_remains_unknown(value):
    product = normalize_product(record(rating=value))
    assert product["rating"] is None
    assert filter_products([product]) == [product]
    assert filter_products([product], min_rating=0) == []


@pytest.mark.parametrize("field,conditions", [
    ("brand", {"brand": "Acme"}), ("category", {"category": "phones"}),
    ("rating", {"min_rating": 0}),
])
@pytest.mark.parametrize("value", [None, "", True, {}])
def test_missing_or_invalid_required_attribute_fails_constraint(field, conditions, value):
    product = normalize_product(record(**{field: value}))
    assert filter_products([product], **conditions) == []
    assert filter_products([product]) == [product]


def test_absent_fields_unknown_and_unused_filters_noop():
    product = normalize_product({"title": "Unknown specs", "price": 0})
    assert product["brand"] is None and product["rating"] is None
    assert product["dimensions"] == dict.fromkeys(("width", "height", "depth"))
    assert filter_products([product], brand=" ", category="", max_budget=None) == [product]
    assert filter_products([product], brand="Acme") == []


def test_inclusive_boundaries_and_zero_are_active():
    products = [normalize_product(record(i, price=p, rating=r))
                for i, p, r in [(1, 0, 0), (2, 0.01, 0), (3, 0, 5)]]
    assert [p["id"] for p in filter_products(products, max_budget=0, min_rating=0)] == [1, 3]
    assert [p["id"] for p in filter_products(products, max_budget=0, min_rating=5)] == [3]


@pytest.mark.parametrize("conditions", [
    {"max_budget": -1}, {"max_budget": True}, {"max_budget": "nan"},
    {"max_budget": "inf"}, {"min_rating": -1}, {"min_rating": 5.01},
    {"min_rating": True}, {"min_rating": "nan"}, {"min_rating": "bad"},
    {"brand": 1}, {"category": []},
])
def test_invalid_constraints_rejected_even_with_no_products(conditions):
    with pytest.raises(ValueError):
        filter_products([], **conditions)


def test_no_matches_and_no_silent_relaxation(api):
    api.return_value.json.return_value = {"products": [record()]}
    assert filter_products(search_all_products("phone"), max_budget=99) == []
    api.return_value.json.return_value = {"products": []}
    assert search_all_products("nothing") == []
    assert search_all_products(" ") == []
    assert api.call_count == 2


def test_filter_preserves_order_and_input(api):
    api.return_value.json.return_value = {"products": [record(2), record(1)]}
    products = search_all_products("phone")
    before = deepcopy(products)
    assert filter_products(products, min_rating=4) == products
    assert products == before


def test_unsupported_dimensions_not_accepted_as_filter():
    with pytest.raises(TypeError):
        filter_products([], max_width=10)


@pytest.mark.parametrize("price", [None, True, -1, "nan", "inf", "bad"])
def test_invalid_required_price_is_readable_error(api, price):
    api.return_value.json.return_value = {"products": [record(price=price)]}
    with pytest.raises(ProductSearchError, match="invalid name or price"):
        search_all_products("phone")


@pytest.mark.parametrize("data", [{}, {"products": None}, []])
def test_malformed_api_shape(api, data):
    api.return_value.json.return_value = data
    with pytest.raises(ProductSearchError, match="unexpected response"):
        search_all_products("phone")


def test_api_failures_are_not_empty_results(api):
    api.side_effect = requests.Timeout()
    with pytest.raises(ProductSearchError):
        search_all_products("phone")
    api.side_effect = None
    api.return_value.raise_for_status.side_effect = requests.HTTPError()
    with pytest.raises(ProductSearchError):
        search_all_products("phone")
    api.return_value.raise_for_status.side_effect = None
    api.return_value.json.side_effect = ValueError("bad JSON")
    with pytest.raises(ProductSearchError):
        search_all_products("phone")
