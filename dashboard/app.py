"""
dashboard/app.py

Painel Streamlit de monitoramento de preços da concorrência da Formare Metais.

Rodar localmente:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "prices.db"

CATEGORY_LABELS = {
    "rolinho_galvalume": "Rolinho Galvalume",
    "rolinho_zincado_fosco": "Rolinho Zincado Fosco",
    "rolinho_zincado_brilhante": "Rolinho Zincado Brilhante",
    "telha_termoacustica_sanduiche_trapezio": "Telha Termoacústica Sanduíche Trapézio",
    "divisoria_drywall": "Divisória Drywall",
    "perfil_montante": "Perfil Montante",
    "perfil_guia": "Perfil Guia",
    "geral": "Geral / Institucional",
}

st.set_page_config(page_title="Concorrência Formare Metais", layout="wide")


@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM price_observations", conn)
    if df.empty:
        return df
    df["collected_at"] = pd.to_datetime(df["collected_at"], utc=True, errors="coerce")
    df["product_category_label"] = df["product_category"].map(CATEGORY_LABELS).fillna(df["product_category"])
    return df


def render_manual_quote_form(df: pd.DataFrame) -> None:
    st.subheader("📋 Cotações manuais pendentes")
    st.caption(
        "Fontes sem preço público (modelo 'solicitar orçamento'). Registre aqui o valor "
        "obtido por telefone/WhatsApp — o robô nunca envia esses formulários sozinho."
    )
    pending = df[df["price_type"] == "manual_quote"][
        ["competitor_name", "product_category_label", "source_url", "collected_at"]
    ].drop_duplicates(subset=["competitor_name", "product_category_label"])

    st.dataframe(pending, use_container_width=True, hide_index=True)

    with st.form("manual_quote_form"):
        col1, col2, col3 = st.columns(3)
        competitor = col1.selectbox("Concorrente", sorted(df["competitor_name"].unique()))
        category = col2.selectbox("Categoria", sorted(df["product_category_label"].unique()))
        price = col3.number_input("Preço obtido (R$)", min_value=0.0, step=0.01)
        note = st.text_input("Observação (condições de pagamento, prazo, etc.)")
        submitted = st.form_submit_button("Salvar cotação manual")
        if submitted:
            # Implementação mínima: acrescenta uma linha no CSV histórico.
            # Em produção, prefira gravar direto no SQLite com a mesma
            # conexão/schema usados pelo runner.py.
            new_row = {
                "collected_at": datetime.utcnow().isoformat(),
                "competitor_name": competitor,
                "product_category": category,
                "price_value": price,
                "price_type": "manual_quote_confirmed",
                "notes": note,
            }
            st.session_state.setdefault("manual_entries", []).append(new_row)
            st.success("Cotação registrada nesta sessão. Para persistir entre execuções, "
                       "conecte este formulário à mesma base SQLite usada pelo runner.py.")


def main() -> None:
    st.title("📊 Monitoramento de Preços — Concorrência Formare Metais")
    st.caption("Prioridade: Grande BH e Minas Gerais. Atualizado no mínimo 2x/dia via GitHub Actions.")

    df = load_data()
    if df.empty:
        st.warning(
            "Ainda não há dados em data/prices.db. Rode `python -m scrapers.runner` "
            "localmente ou aguarde a primeira execução do GitHub Actions."
        )
        return

    # ---------------- Filtros ----------------
    with st.sidebar:
        st.header("Filtros")
        tiers = st.multiselect("Tier", sorted(df["competitor_tier"].unique()), default=list(df["competitor_tier"].unique()))
        categories = st.multiselect(
            "Categoria de produto",
            sorted(df["product_category_label"].unique()),
            default=list(df["product_category_label"].unique()),
        )
        price_types = st.multiselect(
            "Tipo de preço", sorted(df["price_type"].unique()), default=list(df["price_type"].unique())
        )

    filtered = df[
        df["competitor_tier"].isin(tiers)
        & df["product_category_label"].isin(categories)
        & df["price_type"].isin(price_types)
    ]

    # ---------------- KPIs ----------------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Observações totais", len(filtered))
    col2.metric("Com preço automático", int((filtered["price_type"] == "auto_scraped").sum()))
    col3.metric("Aguardando cotação manual", int((filtered["price_type"] == "manual_quote").sum()))
    col4.metric("Concorrentes monitorados", filtered["competitor_name"].nunique())

    # ---------------- Tabela geral ----------------
    st.subheader("📄 Tabela geral")
    st.dataframe(
        filtered[
            [
                "collected_at",
                "competitor_name",
                "competitor_tier",
                "competitor_city_region",
                "product_category_label",
                "price_value",
                "unit_measure",
                "normalized_price_per_kg",
                "price_type",
                "source_url",
            ]
        ].sort_values("collected_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    # ---------------- Evolução de preço ----------------
    scraped = filtered[filtered["price_type"] == "auto_scraped"]
    if not scraped.empty:
        st.subheader("📈 Evolução de preço ao longo do tempo")
        fig = px.line(
            scraped.sort_values("collected_at"),
            x="collected_at",
            y="price_value",
            color="competitor_name",
            facet_col="product_category_label",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("⚖️ Comparativo por kg (base normalizada)")
        normalized = scraped.dropna(subset=["normalized_price_per_kg"])
        if not normalized.empty:
            fig2 = px.bar(
                normalized.sort_values("normalized_price_per_kg"),
                x="competitor_name",
                y="normalized_price_per_kg",
                color="product_category_label",
                barmode="group",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(
                "Nenhuma observação com espessura/largura suficientes para calcular R$/kg ainda. "
                "Preencha spec_thickness_mm e spec_width_mm nos scrapers para habilitar esta comparação."
            )

    # ---------------- CMV: custo interno vs mercado ----------------
    st.subheader("🧮 Comparativo de CMV — custo interno da Formare vs. mercado")
    own_cost = st.number_input("Custo interno da Formare para este item (R$)", min_value=0.0, step=0.01)
    if not scraped.empty and own_cost > 0:
        market_min = scraped["price_value"].min()
        market_avg = scraped["price_value"].mean()
        market_max = scraped["price_value"].max()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Custo interno Formare", f"R$ {own_cost:,.2f}")
        c2.metric("Mínimo de mercado", f"R$ {market_min:,.2f}")
        c3.metric("Média de mercado", f"R$ {market_avg:,.2f}")
        c4.metric("Máximo de mercado", f"R$ {market_max:,.2f}")

    # ---------------- Cotações manuais ----------------
    render_manual_quote_form(df)

    # ---------------- Exportação ----------------
    st.download_button(
        "⬇️ Exportar tabela filtrada (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="precos_concorrencia_formare.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
