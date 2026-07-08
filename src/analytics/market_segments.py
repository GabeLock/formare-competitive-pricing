from __future__ import annotations

import pandas as pd

B2B_SEGMENT = "b2b_atacado"
B2C_SEGMENT = "b2c_varejo"


def priced_by_segment(df: pd.DataFrame, segment: str) -> pd.DataFrame:
    if df.empty or "customer_segment" not in df or "parsed_price" not in df:
        return df.iloc[0:0].copy()
    return df[(df["customer_segment"] == segment) & df["parsed_price"].notna()].copy()


def b2b_competitive_reference(df: pd.DataFrame) -> pd.DataFrame:
    """Minimum/average competitive references using only wholesale B2B rows."""
    b2b = priced_by_segment(df, B2B_SEGMENT)
    if b2b.empty:
        return pd.DataFrame(columns=["product_id", "menor_preco_b2b", "media_b2b"])
    return (
        b2b.groupby("product_id")["parsed_price"]
        .agg(menor_preco_b2b="min", media_b2b="mean")
        .reset_index()
    )


def b2c_retail_ceiling(df: pd.DataFrame) -> pd.DataFrame:
    """Retail rows are displayed separately as an informational market ceiling."""
    b2c = priced_by_segment(df, B2C_SEGMENT)
    if b2c.empty:
        return pd.DataFrame(columns=["product_id", "teto_b2c_varejo", "media_b2c_varejo"])
    return (
        b2c.groupby("product_id")["parsed_price"]
        .agg(teto_b2c_varejo="max", media_b2c_varejo="mean")
        .reset_index()
    )
