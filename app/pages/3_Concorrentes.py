from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.common import load_all, setup_page

import streamlit as st

setup_page("Concorrentes")
observations, competitors, products, costs, alerts = load_all()

summary = competitors.copy()
if not observations.empty:
    counts = observations.groupby("competitor_id").agg(
        itens_monitorados=("product_id", "nunique"),
        ultima_coleta=("collected_at", "max"),
        status_ultima=("collection_status", "last"),
        confiabilidade_media=("confidence_score", "mean"),
    )
    summary = summary.merge(counts, left_on="id", right_index=True, how="left")

st.dataframe(summary, use_container_width=True, hide_index=True)
