import math


def assert_json_has_no_non_finite(payload: object) -> None:
    if isinstance(payload, float):
        assert math.isfinite(payload)
    elif isinstance(payload, dict):
        for value in payload.values():
            assert_json_has_no_non_finite(value)
    elif isinstance(payload, list):
        for value in payload:
            assert_json_has_no_non_finite(value)
