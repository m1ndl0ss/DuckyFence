import math

import features


def test_empty_gaps_give_zero_vector():
    assert features.from_gaps([]) == [0, 0.0, 0.0, 0.0, 0.0]


def test_known_values():
    key_count, avg_gap, variance, cv, span = features.from_gaps([0.1, 0.2])
    assert key_count == 2
    assert math.isclose(avg_gap, 0.15)
    assert math.isclose(variance, 0.0025)
    assert math.isclose(cv, 0.05 / 0.15)
    assert math.isclose(span, 0.3)


def test_constant_gaps_have_zero_cv():
    # perfectly regular timing is the signature of injected input
    _, _, variance, cv, _ = features.from_gaps([0.005] * 20)
    assert math.isclose(variance, 0.0, abs_tol=1e-12)
    assert math.isclose(cv, 0.0, abs_tol=1e-6)


def test_from_gaps_matches_from_aggregates():
    gaps = [0.08, 0.21, 0.12, 0.33, 0.09]
    direct = features.from_gaps(gaps)
    key_count, avg_gap, variance = direct[0], direct[1], direct[2]
    assert features.from_aggregates(key_count, avg_gap, variance) == direct


def test_feature_vector_matches_feature_names():
    assert len(features.from_gaps([0.1] * 6)) == len(features.FEATURE_NAMES)
