from __future__ import annotations

import pandas as pd


def add_price_variations(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "parsed_price" not in df:
        return df
    out = df.sort_values(["item_hash", "collected_at"]).copy()
    out["variation_previous_pct"] = out.groupby("item_hash")["parsed_price"].pct_change() * 100
    return out

