"""Price relative: the core unit of a Laspeyres-style price index.

price_relative = current_price / base_price
index = price_relative * 100

A relative of 120 means fares are 20% above the base period; 90 means 10%
below. This module has no DB/IO dependency, so it's trivial to unit test.
"""

from decimal import Decimal

from app.config.constants import INDEX_BASE_VALUE


def price_relative(current_price: Decimal, base_price: Decimal) -> Decimal:
    if base_price <= 0:
        raise ValueError("base_price must be positive")
    return current_price / base_price


def price_relative_index(current_price: Decimal, base_price: Decimal) -> Decimal:
    return price_relative(current_price, base_price) * INDEX_BASE_VALUE
