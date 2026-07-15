from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.common import load_all, setup_page

import streamlit as st

setup_page("Visao Geral")
observations, competitors, products, costs, alerts = load_all()

if observations.empty:
    st.info("Sem observacoes ainda. Rode `python run.py --collect`.")
    st.stop()

status_counts = observations["collection_status"].value_counts().reset_index()
status_counts.columns = ["status", "quantidade"]
st.dataframe(status_counts, use_container_width=True, hide_index=True)

st.subheader("Ultimas coletas")
st.dataframe(
    observations[
        [
            "collected_at",
            "formare_product_name",
            "competitor_name",
            "tier",
            "customer_segment",
            "collection_status",
            "source_type",
            "parsed_price",
            "confidence_score",
            "notes",
        ]
    ].head(100),
    use_container_width=True,
    hide_index=True,
)
