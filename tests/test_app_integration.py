from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from streamlit.testing.v1 import AppTest


@pytest.fixture
def app(monkeypatch):
    get = Mock()
    monkeypatch.setattr("product_search.requests.get", get)
    get.return_value.json.return_value = {"products": [
        {"id": 1, "title": "Budget phone", "price": 10, "rating": 2,
         "brand": "Acme", "category": "phones"},
        {"id": 2, "title": "Better phone", "price": 30, "rating": 5,
         "brand": "Acme", "category": "phones"},
        {"id": 3, "title": "Other phone", "price": 1, "rating": 5,
         "brand": "Other", "category": "phones"},
    ]}
    return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(), get


def submit(app):
    app.text_input[0].set_value("phone")
    app.button[0].click().run()
    assert not app.exception


def test_default_stage1_order_and_no_weighted_scores(app):
    ui, _ = app
    submit(ui)
    assert [m.value for m in ui.metric] == ["$1.00", "$10.00", "$30.00"]
    assert not any("Weighted score:" in m.value for m in ui.markdown)


def test_combined_constraints_inclusive_boundaries_and_rerun(app):
    ui, _ = app
    ui.number_input[0].set_value(30.0)
    ui.number_input[1].set_value(5.0)
    ui.text_input[1].set_value(" ACME ")
    ui.text_input[2].set_value(" PHONES ")
    submit(ui)
    assert [m.value for m in ui.metric] == ["$30.00"]
    ui.number_input[0].set_value(29.99)
    submit(ui)
    assert not ui.metric
    assert any("No products match" in m.value for m in ui.info)
    assert any("No conditions were relaxed" in m.value for m in ui.markdown)
    assert ui.number_input[0].value == 29.99
    ui.number_input[0].set_value(None)
    submit(ui)
    assert [m.value for m in ui.metric] == ["$30.00"]


def test_weighted_mode_explanation_and_weight_changes(app):
    ui, _ = app
    ui.radio[0].set_value("Weighted recommendations")
    ui.text_input[1].set_value("Acme")
    ui.slider[0].set_value(0.4)
    submit(ui)
    scores = [m.value for m in ui.markdown if m.value.startswith("Weighted score:")]
    assert scores == ["Weighted score: 0.6400", "Weighted score: 0.6000"]
    assert any("Scores depend on the eligible set" in m.value for m in ui.caption)
    ui.slider[0].set_value(0.0)
    submit(ui)
    assert [m.value for m in ui.metric] == ["$30.00", "$10.00"]


def test_resubmit_065_updates_ranking_and_every_explanation(app, monkeypatch):
    import product_ranking

    ui, _ = app
    ranking = Mock(wraps=product_ranking.rank_products)
    monkeypatch.setattr(product_ranking, "rank_products", ranking)
    ui.radio[0].set_value("Weighted recommendations")
    ui.text_input[1].set_value("Acme")
    submit(ui)
    assert any("Weights: price 50%, rating 50%" in c.value for c in ui.caption)
    ui.slider[0].set_value(0.65).run()
    submit(ui)
    assert ranking.call_args.kwargs["price_weight"] == pytest.approx(0.65)
    assert ranking.call_args.kwargs["rating_weight"] == pytest.approx(0.35)
    assert any("Weights: price 65%, rating 35%" in c.value for c in ui.caption)
    explanations = [c.value for c in ui.caption if "Price component" in c.value]
    assert len(explanations) == 2
    assert all("× 0.65" in c and "× 0.35" in c and "× 0.50" not in c for c in explanations)
    assert [m.value for m in ui.markdown if m.value.startswith("Weighted score:")] == [
        "Weighted score: 0.7900", "Weighted score: 0.3500"]
    ui.slider[0].set_value(0.2).run()
    submit(ui)
    assert any("Weights: price 20%, rating 80%" in c.value for c in ui.caption)
    assert [m.value for m in ui.markdown if m.value.startswith("Weighted score:")] == [
        "Weighted score: 0.8000", "Weighted score: 0.5200"]


def test_unknown_attributes_and_active_zero_rating(app):
    ui, get = app
    get.return_value.json.return_value = {"products": [{"title": "Unknown", "price": 0}]}
    ui.radio[0].set_value("Weighted recommendations")
    submit(ui)
    assert any("Brand: Unknown" in m.value and "Rating: Unknown" in m.value for m in ui.caption)
    assert any(m.value == "Weighted score: 0.5000" for m in ui.markdown)
    ui.number_input[1].set_value(0.0)
    submit(ui)
    assert not ui.metric
    assert any("lower or clear" in m.value for m in ui.markdown)


def test_all_matches_ranked_before_five_limit(app):
    ui, get = app
    records = [{"id": i, "title": f"Phone {i}", "price": i, "rating": 0} for i in range(1, 7)]
    records[-1]["rating"] = 5
    get.return_value.json.return_value = {"products": records}
    ui.radio[0].set_value("Weighted recommendations")
    ui.slider[0].set_value(0.1)
    submit(ui)
    assert len(ui.metric) == 5
    assert ui.metric[0].value == "$6.00"


def test_blank_and_api_failure_remove_previous_results(app):
    ui, get = app
    submit(ui)
    ui.text_input[0].set_value(" ")
    ui.button[0].click().run()
    assert ui.warning and not ui.metric
    assert get.call_count == 1
    get.side_effect = requests.Timeout()
    submit(ui)
    assert ui.error and not ui.metric
    assert not any("No products match" in m.value for m in ui.info)
