import uuid
from decimal import Decimal

import pytest

from app.index_engine.aggregation import representative_fares
from app.index_engine.calculator import calculate_overall_index, calculate_route_index
from app.index_engine.price_relative import price_relative, price_relative_index
from app.index_engine.weights import normalize_weights


# --- Price relative ---


def test_price_relative_equal_prices():
    assert price_relative(Decimal("5000"), Decimal("5000")) == Decimal("1")


def test_price_relative_higher_current_price():
    assert price_relative(Decimal("6000"), Decimal("5000")) == Decimal("1.2")


def test_price_relative_index_matches_spec_example():
    result = price_relative_index(Decimal("6000"), Decimal("5000"))
    assert result == Decimal("120")


def test_price_relative_zero_base_raises():
    with pytest.raises(ValueError):
        price_relative(Decimal("100"), Decimal("0"))


# --- Weights ---


def test_normalize_weights_sums_to_one():
    r1, r2, r3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    weights = {r1: Decimal("0.20"), r2: Decimal("0.15"), r3: Decimal("0.12")}
    normalized = normalize_weights(weights)
    assert sum(normalized.values()) == pytest.approx(Decimal("1"), abs=Decimal("0.0001"))


def test_normalize_weights_already_summing_to_one_unchanged_ratio():
    r1, r2 = uuid.uuid4(), uuid.uuid4()
    weights = {r1: Decimal("0.6"), r2: Decimal("0.4")}
    normalized = normalize_weights(weights)
    assert normalized[r1] == Decimal("0.6")
    assert normalized[r2] == Decimal("0.4")


def test_normalize_weights_zero_total_returns_zeros():
    r1, r2 = uuid.uuid4(), uuid.uuid4()
    weights = {r1: Decimal("0"), r2: Decimal("0")}
    normalized = normalize_weights(weights)
    assert normalized[r1] == Decimal("0")
    assert normalized[r2] == Decimal("0")


# --- Aggregation ---


def test_representative_fares_uses_median():
    route_id = uuid.uuid4()
    observations = [
        {
            "route_id": route_id,
            "advance_days": 1,
            "normalized_fare": Decimal(v),
            "is_valid": True,
            "is_outlier": False,
        }
        for v in [8000, 8100, 8200]
    ]
    result = representative_fares(observations)
    assert result[(route_id, 1)] == Decimal("8100")


def test_representative_fares_excludes_outliers_by_default():
    route_id = uuid.uuid4()
    observations = [
        {"route_id": route_id, "advance_days": 1, "normalized_fare": Decimal(v), "is_valid": True, "is_outlier": False}
        for v in [8000, 8100, 8200]
    ] + [
        {"route_id": route_id, "advance_days": 1, "normalized_fare": Decimal(50000), "is_valid": True, "is_outlier": True}
    ]
    result = representative_fares(observations)
    assert result[(route_id, 1)] == Decimal("8100")


def test_representative_fares_excludes_invalid():
    route_id = uuid.uuid4()
    observations = [
        {"route_id": route_id, "advance_days": 1, "normalized_fare": Decimal(8000), "is_valid": True, "is_outlier": False},
        {"route_id": route_id, "advance_days": 1, "normalized_fare": Decimal(1), "is_valid": False, "is_outlier": False},
    ]
    result = representative_fares(observations)
    assert result[(route_id, 1)] == Decimal("8000")


def test_representative_fares_empty_input():
    assert representative_fares([]) == {}


def test_representative_fares_groups_by_route_and_window():
    route_a, route_b = uuid.uuid4(), uuid.uuid4()
    observations = [
        {"route_id": route_a, "advance_days": 1, "normalized_fare": Decimal(8000), "is_valid": True, "is_outlier": False},
        {"route_id": route_a, "advance_days": 7, "normalized_fare": Decimal(9000), "is_valid": True, "is_outlier": False},
        {"route_id": route_b, "advance_days": 1, "normalized_fare": Decimal(5000), "is_valid": True, "is_outlier": False},
    ]
    result = representative_fares(observations)
    assert result[(route_a, 1)] == Decimal("8000")
    assert result[(route_a, 7)] == Decimal("9000")
    assert result[(route_b, 1)] == Decimal("5000")


# --- Calculator ---


def test_calculate_route_index_matches_spec_example():
    assert calculate_route_index(Decimal("6000"), Decimal("5000")) == Decimal("120")


def test_calculate_overall_index_weighted_average():
    r1, r2 = uuid.uuid4(), uuid.uuid4()
    current = {r1: Decimal("6000"), r2: Decimal("5500")}
    base = {r1: Decimal("5000"), r2: Decimal("5000")}
    weights = {r1: Decimal("0.6"), r2: Decimal("0.4")}

    result = calculate_overall_index(current, base, weights)

    # route1 index = 120, route2 index = 110
    # overall = 0.6*120 + 0.4*110 = 72 + 44 = 116
    assert result.index_value == Decimal("116.0")
    assert result.sample_size == 2


def test_calculate_overall_index_missing_data_excludes_route():
    r1, r2 = uuid.uuid4(), uuid.uuid4()
    current = {r1: Decimal("6000")}  # r2 has no current fare
    base = {r1: Decimal("5000"), r2: Decimal("5000")}
    weights = {r1: Decimal("0.6"), r2: Decimal("0.4")}

    result = calculate_overall_index(current, base, weights)

    assert result.sample_size == 1
    assert result.index_value == Decimal("120")  # only route1 contributes, renormalized to weight 1.0


def test_calculate_overall_index_no_usable_routes_returns_base():
    result = calculate_overall_index({}, {}, {})
    assert result.index_value == Decimal("100")
    assert result.sample_size == 0
    assert result.route_indexes == []


def test_calculate_overall_index_renormalizes_weights():
    r1, r2, r3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    # r3 weight exists but no fare data at all -> should not affect r1/r2 renormalization
    current = {r1: Decimal("5000"), r2: Decimal("5000")}
    base = {r1: Decimal("5000"), r2: Decimal("5000")}
    weights = {r1: Decimal("0.2"), r2: Decimal("0.2"), r3: Decimal("0.6")}

    result = calculate_overall_index(current, base, weights)

    assert result.sample_size == 2
    assert result.index_value == Decimal("100")
