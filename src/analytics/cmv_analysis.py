from __future__ import annotations


def gross_margin(sale_price: float | None, internal_cost: float | None) -> float | None:
    if sale_price is None or sale_price <= 0 or internal_cost is None:
        return None
    return (sale_price - internal_cost) / sale_price


def contribution_margin(
    sale_price: float | None,
    internal_cost: float | None,
    freight_cost: float = 0,
    taxes: float = 0,
    commission: float = 0,
    variable_expenses: float = 0,
) -> float | None:
    if sale_price is None or sale_price <= 0 or internal_cost is None:
        return None
    total_variable = internal_cost + freight_cost + taxes + commission + variable_expenses
    return (sale_price - total_variable) / sale_price

