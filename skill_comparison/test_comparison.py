"""One unchanged test set, selected via --attempt for either implementation."""

from copy import deepcopy
from itertools import permutations
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def rank(request):
    path = Path(__file__).parent / f"attempt_{request.config.getoption('--attempt')}.py"
    spec = importlib.util.spec_from_file_location("isolated_attempt", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.rank_candidates


def p(identifier, price=10, rating=4, title="Phone"):
    return dict(id=identifier, title=title, price=price, rating=rating)


def test_hand_calculation(rank):
    result = rank([p(1, 10, 2), p(2, 30, 5)], 0.4, 0.6)
    assert [x['id'] for x in result] == [1, 2]
    assert [x['score'] for x in result] == pytest.approx([0.64, 0.60])
    assert [x['price_score'] for x in result] == [1, 0]
    assert [x['rating_score'] for x in result] == [0.4, 1]


def test_full_set_before_limit(rank):
    records = [p(i, i, 0) for i in range(1, 7)]
    records[-1]['rating'] = 5
    result = rank(records, 0.1, 0.9)
    assert len(result) == 5
    assert result[0]['id'] == 6


def test_equal_price_and_single_result(rank):
    assert [x['id'] for x in rank([p(1, rating=1), p(2, rating=5)])] == [2, 1]
    assert rank([p(1, rating=2)])[0]['score'] == pytest.approx(0.7)


@pytest.mark.parametrize('rating', [None, True, 'bad', -1, 6, float('nan'), float('inf')])
def test_unknown_rating(rank, rating):
    record = p(1, rating=rating)
    result = rank([record])[0]
    assert result['rating_score'] == 0
    assert result['score'] == 0.5
    assert result['rating'] is rating


def test_absent_rating(rank):
    result = rank([dict(id=1, title='Unknown', price=10)])[0]
    assert 'rating' not in result
    assert result['rating_score'] == 0


@pytest.mark.parametrize('weights', [(True, 0), (None, 1), (-0.1, 1.1),
    (float('nan'), 1), (float('inf'), 0), (0, 0), (1, 1), (0.2, 0.2), (0.5, 0.50000001)])
def test_invalid_weights_even_empty(rank, weights):
    with pytest.raises(ValueError):
        rank([], *weights)


def test_tolerance_and_empty(rank):
    assert rank([], 0.5, 0.5000000005) == []


def test_extreme_weights(rank):
    records = [p(1, 10, 1), p(2, 20, 5)]
    assert [x['id'] for x in rank(records, 1, 0)] == [1, 2]
    assert [x['id'] for x in rank(records, 0, 1)] == [2, 1]


def test_tie_breaking_and_permutations(rank):
    records = [p(3, title='Beta'), p(2, title=' alpha '), p(1, title='ALPHA')]
    for order in permutations(records):
        assert [x['id'] for x in rank(list(order))] == [1, 2, 3]
    assert [x['id'] for x in rank([p(1, 20), p(2, 10)], 0, 1)] == [2, 1]
    assert [x['id'] for x in rank([p(1, rating=None), p(2, rating=0), p(3, rating=5)], 1, 0)] == [3, 2, 1]


def test_no_mutation_or_rounding(rank):
    records = [p(1, rating=4.000001), p(2, rating=4.000002)]
    before = deepcopy(records)
    result = rank(records)
    assert result[0]['id'] == 2
    assert result[0]['score'] > result[1]['score']
    assert records == before
