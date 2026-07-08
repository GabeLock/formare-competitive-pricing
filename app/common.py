from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.settings import TIERS
from src.database.repository import alerts_df, competitors_df, formare_costs_df, initialize_database, latest_observations, products_df


def setup_page(title: str) -> None:
    st.set_page_config(page_title=title, layout="wide")
    st.title(title)


@st.cache_data(ttl=300)
def load_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    initialize_database()
    observations = latest_observations()
    competitors = competitors_df()
    products = products_df()
    costs = formare_costs_df()
    alerts = alerts_df()
    if not observations.empty:
        observations["collected_at"] = pd.to_datetime(observations["collected_at"], utc=True, errors="coerce")
        observations = observations.merge(
            products[["id", "formare_product_name"]].rename(columns={"id": "product_id"}),
            on="product_id",
            how="left",
        )
        observations["tier_order"] = observations["tier"].map(TIERS).fillna(9)
        observations = observations.sort_values(["tier_order", "collected_at"], ascending=[True, False])
        if "customer_segment" not in observations:
            observations["customer_segment"] = "b2b_atacado"
    return observations, competitors, products, costs, alerts


def brl(value) -> str:
    if pd.isna(value):
        return "-"
    return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    with st.sidebar:
        st.header("Filtros")
        tiers = st.multiselect("Tier", sorted(df["tier"].dropna().unique()), default=sorted(df["tier"].dropna().unique()))
        products = st.multiselect(
            "Produto",
            sorted(df["formare_product_name"].dropna().unique()),
            default=sorted(df["formare_product_name"].dropna().unique()),
        )
        statuses = st.multiselect(
            "Status",
            sorted(df["collection_status"].dropna().unique()),
            default=sorted(df["collection_status"].dropna().unique()),
        )
        segments = st.multiselect(
            "Segmento",
            sorted(df["customer_segment"].dropna().unique()),
            default=sorted(df["customer_segment"].dropna().unique()),
        )
    return df[
        df["tier"].isin(tiers)
        & df["formare_product_name"].isin(products)
        & df["collection_status"].isin(statuses)
        & df["customer_segment"].isin(segments)
    ]
