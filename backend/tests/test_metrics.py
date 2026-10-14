from app.core.metrics import engagement_rate


def test_engagement_rate_uses_the_documented_formula():
    assert engagement_rate(500, 100, 50, 10000) == 6.5


def test_engagement_rate_rejects_non_positive_views():
    assert engagement_rate(10, 2, 1, 0) is None
    assert engagement_rate(10, 2, 1, -5) is None


def test_engagement_rate_does_not_treat_missing_parts_as_zero():
    assert engagement_rate(None, 2, 1, 100) is None
    assert engagement_rate(1, None, 1, 100) is None
    assert engagement_rate(1, 2, None, 100) is None


def test_real_zeros_are_included():
    assert engagement_rate(0, 0, 0, 100) == 0.0
