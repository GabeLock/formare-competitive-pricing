from __future__ import annotations

from app.common import load_all, setup_page, sidebar_filters

import plotly.express as px
import streamlit as st

setup_page("Historico de Precos")
observations, competitors, products, costs, alerts = load_all()
filtered = sidebar_filters(observations)
priced = filtered.dropna(subset=["parsed_price"])

if priced.empty:
    st.info("Sem historico numerico para plotar.")
    st.stop()

fig = px.line(
    priced.sort_values("collected_at"),
    x="collected_at",
    y="parsed_price",
    color="competitor_name",
    line_dash="customer_segment",
    facet_col="formare_product_name",
    markers=True,
)
st.plotly_chart(fig, use_container_width=True)

priced = priced.sort_values(["item_hash", "collected_at"]).copy()
priced["media_movel_7"] = priced.groupby("item_hash")["parsed_price"].transform(lambda s: s.rolling(7, min_periods=1).mean())
st.dataframe(priced, use_container_width=True, hide_index=True)
