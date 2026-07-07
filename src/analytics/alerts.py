from __future__ import annotations

import pandas as pd


def build_alert_candidates(df: pd.DataFrame, variation_threshold_pct: float = 10) -> list[dict]:
    if df.empty or "variation_previous_pct" not in df:
        return []
    alerts: list[dict] = []
    for row in df.dropna(subset=["variation_previous_pct"]).itertuples():
        variation = abs(float(row.variation_previous_pct))
        if variation >= variation_threshold_pct:
            alerts.append(
                {
                    "product_id": row.product_id,
                    "competitor_id": row.competitor_id,
                    "alert_type": "price_variation",
                    "severity": "high" if variation >= 20 else "medium",
                    "message": f"Variacao de preco de {row.variation_previous_pct:.1f}%.",
                }
            )
    return alerts

