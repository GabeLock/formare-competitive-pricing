from __future__ import annotations

from app.common import brl, load_all, setup_page

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.market_segments import B2B_SEGMENT, B2C_SEGMENT

setup_page("Formare Price Intelligence")
st.caption("Monitoramento etico de precos publicos, cotacoes manuais e CMV da Formare Metais.")

observations, competitors, products, costs, alerts = load_all()

if observations.empty:
    st.info("Banco inicial criado. Rode `python run.py --collect` para buscar dados reais ou registre cotacoes manuais nas paginas.")
    st.write("Produtos cadastrados")
    st.dataframe(products, use_container_width=True, hide_index=True)
    st.write("Concorrentes cadastrados")
    st.dataframe(competitors, use_container_width=True, hide_index=True)
    st.stop()

today = pd.Timestamp.utcnow().date()
today_count = int((observations["collected_at"].dt.date == today).sum())
success = observations[observations["collection_status"] == "success"]
latest_at = observations["collected_at"].max()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ultima atualizacao", latest_at.tz_convert("America/Sao_Paulo").strftime("%d/%m %H:%M") if pd.notna(latest_at) else "-")
col2.metric("Produtos", products["id"].nunique())
col3.metric("Concorrentes", competitors["id"].nunique())
col4.metric("Coletas hoje", today_count)

col5, col6, col7, col8 = st.columns(4)
col5.metric("Precos com sucesso", len(success))
col6.metric("Sob orcamento", int((observations["collection_status"] == "quote_required").sum()))
col7.metric("Bloqueados", int((observations["collection_status"] == "blocked").sum()))
col8.metric("Alertas ativos", int((alerts["resolved"] == 0).sum()) if not alerts.empty else 0)

st.subheader("Menores precos competitivos - B2B atacado")
priced = success.dropna(subset=["parsed_price"])
b2b_priced = priced[priced["customer_segment"] == B2B_SEGMENT]
b2c_priced = priced[priced["customer_segment"] == B2C_SEGMENT]
if b2b_priced.empty:
    st.info("Ainda nao ha preco B2B atacado com valor numerico para referencia competitiva.")
else:
    latest_by_item = b2b_priced.sort_values("collected_at").groupby(["product_id", "competitor_name"]).tail(1)
    ranking = latest_by_item.sort_values(["tier_order", "parsed_price"])
    st.dataframe(
        ranking[
            [
                "formare_product_name",
                "competitor_name",
                "tier",
                "customer_segment",
                "parsed_price",
                "raw_unit",
                "normalized_price",
                "normalized_unit",
                "confidence_score",
                "url",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    fig = px.bar(
        ranking.head(20),
        x="competitor_name",
        y="parsed_price",
        color="tier",
        facet_col="formare_product_name",
        title="Ranking de preco por produto",
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Teto de mercado informativo - B2C varejo")
if b2c_priced.empty:
    st.info("Ainda nao ha preco B2C varejo numerico. Quando houver, ele aparece separado e nao entra na media B2B.")
else:
    retail = b2c_priced.sort_values(["formare_product_name", "parsed_price"], ascending=[True, False])
    st.dataframe(
        retail[
            [
                "formare_product_name",
                "competitor_name",
                "tier",
                "customer_segment",
                "parsed_price",
                "raw_unit",
                "confidence_score",
                "url",
            ]
        ].head(30),
        use_container_width=True,
        hide_index=True,
    )
