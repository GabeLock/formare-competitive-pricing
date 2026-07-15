from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.common import load_all, setup_page

import streamlit as st

setup_page("Alertas")
observations, competitors, products, costs, alerts = load_all()

if alerts.empty:
    st.info("Nenhum alerta persistido ainda. Alertas sao gerados a partir de variacoes relevantes e falhas de coleta.")
else:
    st.dataframe(alerts, use_container_width=True, hide_index=True)

st.subheader("Falhas e pendencias recentes")
if observations.empty:
    st.info("Sem coletas.")
else:
    pending = observations[observations["collection_status"].isin(["error", "blocked", "no_price", "quote_required", "unavailable"])]
    st.dataframe(
        pending[
            [
                "collected_at",
                "formare_product_name",
                "competitor_name",
                "tier",
                "customer_segment",
                "collection_status",
                "source_type",
                "notes",
                "url",
            ]
        ].head(200),
        use_container_width=True,
        hide_index=True,
    )
