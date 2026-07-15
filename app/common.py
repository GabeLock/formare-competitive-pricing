from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config.settings import TIERS
from src.database.repository import alerts_df, competitors_df, formare_costs_df, initialize_database, latest_observations, products_df


def _configured_secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        return str(st.secrets[name]) if name in st.secrets else None
    except Exception:
        return None


def require_access(secret_name: str, label: str) -> None:
    expected = _configured_secret(secret_name)
    if not expected:
        if os.getenv("FORMARE_ENVIRONMENT") == "production":
            st.error(f"Acesso bloqueado: configure o segredo {secret_name} no ambiente de publicacao.")
            st.stop()
        return
    session_key = f"authenticated_{secret_name.lower()}"
    if st.session_state.get(session_key):
        return
    st.info(f"Acesso {label} protegido.")
    with st.form(f"login_{secret_name}"):
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
    if submitted and password == expected:
        st.session_state[session_key] = True
        st.rerun()
    elif submitted:
        st.error("Senha incorreta.")
    st.stop()


def setup_page(title: str) -> None:
    st.set_page_config(page_title=title, layout="wide")
    require_access("FORMARE_DASHBOARD_PASSWORD", "do cliente")
    st.title(title)


def require_admin_access() -> None:
    require_access("FORMARE_ADMIN_PASSWORD", "administrativo")


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


def freshness_status(observed_at: pd.Timestamp | None) -> tuple[str, str]:
    if observed_at is None or pd.isna(observed_at):
        return "Indisponivel", "Nenhuma coleta valida foi registrada."
    age = datetime.now(timezone.utc) - observed_at.to_pydatetime()
    if age.total_seconds() <= 3600:
        return "Atualizado", "Dados com menos de 1 hora."
    if age.total_seconds() <= 6 * 3600:
        return "Atencao", "Dados entre 1 e 6 horas."
    if age.total_seconds() <= 24 * 3600:
        return "Desatualizado", "Dados entre 6 e 24 horas."
    return "Critico", "A ultima coleta valida tem mais de 24 horas."


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
