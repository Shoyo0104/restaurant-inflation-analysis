"""
Step 4 — Fetch CPI for Food Away from Home from FRED.

Series : CUSR0000SEFV — CPI, All Urban Consumers, Food Away from Home
Source : US Bureau of Labor Statistics via FRED (St. Louis Fed)

If FRED_API_KEY is not set, the script uses a hard-coded table of
approximate historical values so the pipeline still runs offline.

Run: python 04_cpi_analysis.py
     FRED_API_KEY=<your_key> python 04_cpi_analysis.py
"""

import os

import pandas as pd

OUTPUT_DIR = "data/processed"
CPI_SERIES = "CUSR0000SEFV"

# ── Fallback data (CUSR0000SEFV approximate values, 1982-84 = 100) ────────────
_FALLBACK = [
    # (year, month, cpi)
    (2015, 1,251.4),(2015, 2,251.9),(2015, 3,252.6),(2015, 4,253.0),(2015, 5,253.4),(2015, 6,253.9),
    (2015, 7,254.1),(2015, 8,254.3),(2015, 9,254.6),(2015,10,254.9),(2015,11,255.1),(2015,12,255.3),
    (2016, 1,255.6),(2016, 2,256.1),(2016, 3,256.7),(2016, 4,257.2),(2016, 5,257.6),(2016, 6,258.0),
    (2016, 7,258.3),(2016, 8,258.6),(2016, 9,259.0),(2016,10,259.4),(2016,11,259.7),(2016,12,260.0),
    (2017, 1,260.4),(2017, 2,261.0),(2017, 3,261.7),(2017, 4,262.2),(2017, 5,262.6),(2017, 6,263.0),
    (2017, 7,263.3),(2017, 8,263.7),(2017, 9,264.2),(2017,10,264.6),(2017,11,265.0),(2017,12,265.4),
    (2018, 1,265.8),(2018, 2,266.4),(2018, 3,267.1),(2018, 4,267.7),(2018, 5,268.3),(2018, 6,268.8),
    (2018, 7,269.2),(2018, 8,269.6),(2018, 9,270.1),(2018,10,270.6),(2018,11,271.0),(2018,12,271.3),
    (2019, 1,271.7),(2019, 2,272.4),(2019, 3,273.2),(2019, 4,273.9),(2019, 5,274.5),(2019, 6,275.0),
    (2019, 7,275.5),(2019, 8,276.0),(2019, 9,276.6),(2019,10,277.1),(2019,11,277.5),(2019,12,277.9),
    (2020, 1,278.4),(2020, 2,279.1),(2020, 3,279.5),(2020, 4,278.8),(2020, 5,278.2),(2020, 6,278.9),
    (2020, 7,280.1),(2020, 8,281.2),(2020, 9,282.0),(2020,10,282.5),(2020,11,282.8),(2020,12,283.0),
    (2021, 1,283.5),(2021, 2,284.3),(2021, 3,285.8),(2021, 4,287.4),(2021, 5,289.0),(2021, 6,291.2),
    (2021, 7,293.4),(2021, 8,295.3),(2021, 9,297.1),(2021,10,298.9),(2021,11,300.5),(2021,12,302.0),
    (2022, 1,303.8),(2022, 2,306.1),(2022, 3,309.0),(2022, 4,311.8),(2022, 5,314.3),(2022, 6,316.9),
    (2022, 7,318.8),(2022, 8,320.1),(2022, 9,321.4),(2022,10,322.7),(2022,11,323.5),(2022,12,324.1),
    (2023, 1,324.8),(2023, 2,325.7),(2023, 3,326.5),(2023, 4,327.3),(2023, 5,328.0),(2023, 6,328.6),
    (2023, 7,329.2),(2023, 8,329.9),(2023, 9,330.4),(2023,10,330.9),(2023,11,331.2),(2023,12,331.5),
]


def fetch_fred() -> pd.DataFrame | None:
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from fredapi import Fred
        fred   = Fred(api_key=api_key)
        series = fred.get_series(
            CPI_SERIES,
            observation_start="2015-01-01",
            observation_end="2023-12-31",
        )
        df = series.reset_index()
        df.columns = ["date", "cpi"]
        df["date"]     = pd.to_datetime(df["date"])
        df["year"]     = df["date"].dt.year
        df["month"]    = df["date"].dt.month
        df["date_str"] = df["date"].dt.strftime("%Y-%m")
        return df[["year", "month", "date_str", "cpi"]]
    except Exception as exc:
        print(f"  FRED API error: {exc}")
        return None


def get_cpi() -> pd.DataFrame:
    df = fetch_fred()
    if df is not None:
        print(f"  Fetched {len(df)} months from FRED ({CPI_SERIES})")
        return df

    print("  Using built-in fallback CPI values (CUSR0000SEFV approximate)")
    df = pd.DataFrame(_FALLBACK, columns=["year", "month", "cpi"])
    df["date_str"] = (
        df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    )
    return df


def add_yoy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    df["cpi_lag12"]  = df["cpi"].shift(12)
    df["cpi_yoy_pct"] = ((df["cpi"] - df["cpi_lag12"]) / df["cpi_lag12"] * 100).round(2)
    df["cpi_mom_pct"] = df["cpi"].pct_change(1).multiply(100).round(3)
    return df


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Fetching CPI data (series: {CPI_SERIES}) …")
    df = get_cpi()
    df = add_yoy(df)
    df.to_csv(f"{OUTPUT_DIR}/cpi_data.csv", index=False)

    print("\nCPI summary (Food Away from Home):")
    for yr in [2015, 2019, 2020, 2021, 2022, 2023]:
        sub = df[df["year"] == yr]
        if sub.empty:
            continue
        avg_cpi = sub["cpi"].mean()
        avg_yoy = sub["cpi_yoy_pct"].dropna().mean()
        print(f"  {yr}  avg CPI = {avg_cpi:.1f}    YoY = {avg_yoy:+.1f}%")

    print(f"\nSaved to {OUTPUT_DIR}/cpi_data.csv")
    print("Next: python 05_combine_export.py")


if __name__ == "__main__":
    main()
