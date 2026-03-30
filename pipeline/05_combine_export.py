"""
Step 5 — Combine all results and export JSON for the Next.js web app.

Reads:
  data/processed/price_concern_index.csv
  data/processed/cpi_data.csv
  data/processed/city_stats.csv
  data/processed/price_tier_by_city.csv
  data/processed/top_price_phrases.csv   (optional)

Writes JSON to ../web/public/data/:
  sentiment_cpi.json   — monthly PCI + CPI time series
  city_stats.json      — per-city stats for the map
  price_tiers.json     — stacked bar chart data
  summary.json         — key headline numbers
  phrases.json         — top price phrases
  scatter.json         — scatter plot (PCI vs CPI)

Run: python 05_combine_export.py
"""

import json
import math
import os

import numpy as np
import pandas as pd
from scipy import stats

PROCESSED   = "data/processed"
WEB_DATA    = "../web/public/data"


# ── Load ──────────────────────────────────────────────────────────────────────

def load_all():
    pci     = pd.read_csv(f"{PROCESSED}/price_concern_index.csv")
    cpi     = pd.read_csv(f"{PROCESSED}/cpi_data.csv")
    cities  = pd.read_csv(f"{PROCESSED}/city_stats.csv")
    tiers   = pd.read_csv(f"{PROCESSED}/price_tier_by_city.csv")

    phrases_path = f"{PROCESSED}/top_price_phrases.csv"
    phrases = pd.read_csv(phrases_path) if os.path.exists(phrases_path) else pd.DataFrame()
    return pci, cpi, cities, tiers, phrases


# ── Merge & correlations ──────────────────────────────────────────────────────

def merge_pci_cpi(pci: pd.DataFrame, cpi: pd.DataFrame) -> pd.DataFrame:
    pci = pci.rename(columns={"date": "date_str"})
    merged = pci.merge(
        cpi[["date_str", "cpi", "cpi_yoy_pct"]],
        on="date_str", how="inner",
    )
    merged = merged.sort_values(["year", "month"]).reset_index(drop=True)
    merged = merged.rename(columns={"date_str": "date"})
    return merged


def compute_correlations(merged: pd.DataFrame) -> dict:
    clean = merged.dropna(subset=["price_concern_index", "cpi", "cpi_yoy_pct"])

    r_lvl, p_lvl = stats.pearsonr(clean["price_concern_index"], clean["cpi"])

    # YoY correlation (skip first 12 months — no lag available)
    yoy_df = clean.dropna(subset=["cpi_yoy_pct"])
    if len(yoy_df) > 12:
        r_yoy, p_yoy = stats.pearsonr(yoy_df["price_concern_index"], yoy_df["cpi_yoy_pct"])
    else:
        r_yoy, p_yoy = None, None

    slope, intercept, r_reg, _, _ = stats.linregress(
        clean["cpi"], clean["price_concern_index"]
    )

    return {
        "pearson_r":         round(float(r_lvl), 3),
        "pearson_p":         round(float(p_lvl), 4),
        "pearson_r_yoy":     round(float(r_yoy), 3) if r_yoy else None,
        "pearson_p_yoy":     round(float(p_yoy), 4) if p_yoy else None,
        "regression_slope":  round(float(slope), 5),
        "regression_r2":     round(float(r_reg ** 2), 3),
        "n_months":          int(len(clean)),
    }


# ── City / tier builders ──────────────────────────────────────────────────────

def build_city_json(cities: pd.DataFrame, tiers: pd.DataFrame) -> list:
    pivot = tiers.pivot_table(
        index=["city", "state"],
        columns="price_tier",
        values="restaurant_count",
        fill_value=0,
    ).reset_index()
    pivot.columns = [
        str(c) if isinstance(c, (int, float)) else c for c in pivot.columns
    ]
    for t in ["1", "2", "3", "4"]:
        if t not in pivot.columns:
            pivot[t] = 0

    tot = pivot[["1", "2", "3", "4"]].sum(axis=1)
    for t in ["1", "2", "3", "4"]:
        pivot[f"tier{t}_pct"] = (pivot[t] / tot * 100).round(1)

    merged = cities.merge(pivot, on=["city", "state"], how="left")

    result = []
    for _, row in merged.iterrows():
        result.append({
            "city":             row["city"],
            "state":            row["state"],
            "lat":              float(row["lat"]),
            "lon":              float(row["lon"]),
            "restaurant_count": int(row["restaurant_count"]),
            "total_reviews":    int(row["total_reviews"]),
            "avg_price_tier":   round(float(row["avg_price_tier"]), 2),
            "avg_stars":        round(float(row["avg_stars"]), 2),
            "tier1_pct":        float(row.get("tier1_pct", 0)),
            "tier2_pct":        float(row.get("tier2_pct", 0)),
            "tier3_pct":        float(row.get("tier3_pct", 0)),
            "tier4_pct":        float(row.get("tier4_pct", 0)),
        })
    return sorted(result, key=lambda x: x["restaurant_count"], reverse=True)


def build_tier_bar(tiers: pd.DataFrame) -> dict:
    top = (
        tiers.groupby("city")["restaurant_count"]
        .sum()
        .nlargest(12)
        .index.tolist()
    )
    sub   = tiers[tiers["city"].isin(top)]
    pivot = (
        sub.pivot_table(
            index="city", columns="price_tier",
            values="restaurant_count", fill_value=0,
        )
        .reindex(top)
        .reset_index()
    )
    pivot.columns = [str(c) if isinstance(c, (int, float)) else c for c in pivot.columns]

    result: dict = {"cities": pivot["city"].tolist()}
    for t in ["1", "2", "3", "4"]:
        result[f"tier{t}"] = [int(v) for v in pivot.get(t, [0] * len(top))]
    return result


# ── Export ────────────────────────────────────────────────────────────────────

def _clean(obj):
    """Recursively replace NaN / inf with None for JSON serialisation."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


def save_json(data, filename: str):
    os.makedirs(WEB_DATA, exist_ok=True)
    path = os.path.join(WEB_DATA, filename)
    with open(path, "w") as f:
        json.dump(_clean(data), f, indent=2)
    print(f"  {path}")


def main():
    print("Loading processed data …")
    pci, cpi, cities, tiers, phrases = load_all()

    print("Merging PCI + CPI …")
    merged = merge_pci_cpi(pci, cpi)

    print("Computing correlations …")
    corr = compute_correlations(merged)
    print(f"  Pearson r (level) = {corr['pearson_r']}  p = {corr['pearson_p']}")
    print(f"  Regression R²     = {corr['regression_r2']}")

    print("\nExporting JSON files …")

    # 1 — Monthly time series
    save_json(merged.to_dict(orient="records"), "sentiment_cpi.json")

    # 2 — City stats (map)
    save_json(build_city_json(cities, tiers), "city_stats.json")

    # 3 — Price tier bar chart
    save_json(build_tier_bar(tiers), "price_tiers.json")

    # 4 — Summary / headline stats
    summary = {
        **corr,
        "total_cities":       int(cities["city"].nunique()),
        "total_restaurants":  int(cities["restaurant_count"].sum()),
        "total_reviews":      int(cities["total_reviews"].sum()),
        "years_covered":      "2015–2023",
        "cpi_series":         "CUSR0000SEFV — Food Away from Home",
        "pci_avg_pre2020":    round(float(merged[merged["year"] < 2020]["price_concern_index"].mean()), 1),
        "pci_avg_2022":       round(float(merged[merged["year"] == 2022]["price_concern_index"].mean()), 1),
        "cpi_peak_yoy":       round(float(merged["cpi_yoy_pct"].dropna().max()), 1),
    }
    save_json(summary, "summary.json")

    # 5 — Top phrases
    phrases_list = phrases.head(15).to_dict(orient="records") if not phrases.empty else []
    save_json(phrases_list, "phrases.json")

    # 6 — Scatter (each dot = one month)
    scatter = (
        merged[["date", "price_concern_index", "cpi", "cpi_yoy_pct"]]
        .dropna()
        .to_dict(orient="records")
    )
    save_json(scatter, "scatter.json")

    print("\nAll JSON exports complete!")
    print("The web app is ready — run: cd ../web && npm run dev")


if __name__ == "__main__":
    main()
