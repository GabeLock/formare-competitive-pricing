from __future__ import annotations

from app.common import load_all, setup_page

import pandas as pd
import streamlit as st

from src.analytics.cmv_analysis import contribution_margin, gross_margin
from src.analytics.scoring import classify_commercial_position, classify_risk, commercial_risk
from src.database.connection import SessionLocal
from src.database.repository import save_manual_quote, upsert_formare_cost

setup_page("CMV e Comercial")
observations, competitors, products, costs, alerts = load_all()

st.subheader("Cadastro manual de custo e preco Formare")
with st.form("formare_cost"):
    product_id = st.selectbox("Produto", products["id"].tolist(), format_func=lambda v: products.set_index("id").loc[v, "formare_product_name"])
    c1, c2, c3 = st.columns(3)
    internal_cost = c1.number_input("Custo interno", min_value=0.0, step=0.01)
    sale_price = c2.number_input("Preco de venda", min_value=0.0, step=0.01)
    target_margin = c3.number_input("Margem alvo", min_value=0.0, max_value=1.0, value=0.25, step=0.01)
    c4, c5, c6, c7 = st.columns(4)
    minimum_margin = c4.number_input("Margem minima", min_value=0.0, max_value=1.0, value=0.15, step=0.01)
    freight_cost = c5.number_input("Frete medio", min_value=0.0, step=0.01)
    taxes = c6.number_input("Impostos", min_value=0.0, step=0.01)
    commission = c7.number_input("Comissao", min_value=0.0, step=0.01)
    variable_expenses = st.number_input("Despesas variaveis", min_value=0.0, step=0.01)
    notes = st.text_input("Observacoes")
    if st.form_submit_button("Salvar custo"):
        with SessionLocal() as session:
            upsert_formare_cost(session, product_id, internal_cost, sale_price, target_margin, minimum_margin, freight_cost, taxes, commission, variable_expenses, notes)
        st.success("Custo salvo.")
        st.cache_data.clear()

margin = gross_margin(sale_price if "sale_price" in locals() else None, internal_cost if "internal_cost" in locals() else None)
contrib = contribution_margin(
    sale_price if "sale_price" in locals() else None,
    internal_cost if "internal_cost" in locals() else None,
    freight_cost if "freight_cost" in locals() else 0,
    taxes if "taxes" in locals() else 0,
    commission if "commission" in locals() else 0,
    variable_expenses if "variable_expenses" in locals() else 0,
)
col1, col2, col3 = st.columns(3)
col1.metric("Margem bruta", f"{margin:.1%}" if margin is not None else "-")
col2.metric("Margem contribuicao", f"{contrib:.1%}" if contrib is not None else "-")
col3.metric("Classificacao", classify_commercial_position(margin, target_margin if "target_margin" in locals() else None))

st.subheader("Registrar cotacao manual")
quote_candidates = observations[observations["source_type"].isin(["quote_required", "manual_quote"])] if not observations.empty else pd.DataFrame()
with st.form("manual_quote"):
    if quote_candidates.empty:
        st.info("Ainda nao ha fontes quote_required coletadas. Rode uma coleta para preencher candidatos.")
        selected = None
    else:
        labels = quote_candidates.drop_duplicates(["competitor_id", "product_id"]).copy()
        labels["label"] = labels["competitor_name"] + " - " + labels["formare_product_name"]
        selected = st.selectbox("Fonte", labels.index.tolist(), format_func=lambda i: labels.loc[i, "label"])
    price = st.number_input("Preco cotado", min_value=0.0, step=0.01, key="manual_price")
    raw_unit = st.selectbox("Unidade", ["peca", "m", "m2", "kg", "rolo"])
    quote_notes = st.text_input("Condicao/prazo/observacao")
    if st.form_submit_button("Salvar cotacao manual") and selected is not None:
        row = labels.loc[selected]
        with SessionLocal() as session:
            save_manual_quote(session, row["competitor_id"], row["competitor_name"], row["tier"], row["product_id"], row["category"], row["url"], price, raw_unit, quote_notes)
        st.success("Cotacao manual salva no SQLite.")
        st.cache_data.clear()

st.subheader("Risco comercial")
priced = observations.dropna(subset=["parsed_price"]) if not observations.empty else pd.DataFrame()
if priced.empty:
    st.info("Sem precos numericos para risco.")
else:
    lowest = priced.groupby("product_id")["parsed_price"].min().rename("menor_preco_mercado")
    risk_df = priced.merge(lowest, on="product_id", how="left")
    risk_df["risco"] = risk_df.apply(
        lambda r: commercial_risk(r.get("parsed_price"), r.get("menor_preco_mercado"), confidence=r.get("confidence_score", 100), tier=r.get("tier")),
        axis=1,
    )
    risk_df["classificacao_risco"] = risk_df["risco"].apply(classify_risk)
    st.dataframe(
        risk_df[["formare_product_name", "competitor_name", "tier", "parsed_price", "menor_preco_mercado", "risco", "classificacao_risco"]].sort_values("risco", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

