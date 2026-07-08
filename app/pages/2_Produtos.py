from __future__ import annotations

from app.common import load_all, setup_page, sidebar_filters

import streamlit as st

setup_page("Produtos")
observations, competitors, products, costs, alerts = load_all()
filtered = sidebar_filters(observations)

if filtered.empty:
    st.info("Nenhum produto encontrado nos filtros atuais.")
    st.stop()

st.dataframe(
    filtered[
        [
            "formare_product_name",
            "raw_product_name",
            "competitor_name",
            "tier",
            "customer_segment",
            "parsed_price",
            "raw_price",
            "raw_unit",
            "normalized_price",
            "normalized_unit",
            "collection_status",
            "confidence_score",
            "collected_at",
            "url",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)
