"""
Step 3 — NLP price-sentiment analysis.

For each review we:
  1. Detect whether the review contains price-related language
     (keyword list + regex dollar amounts)
  2. Extract the price-bearing sentence(s)
  3. Score those sentences with VADER sentiment
  4. Aggregate to a monthly "Price Concern Index"

Price Concern Index (PCI):
  PCI_t = (reviews with negative price sentiment in month t)
          ─────────────────────────────────────────────────── × 100
                  (total reviews in month t)

PCI gives a single monthly series that we compare against CPI.

Run: python 03_nlp_analysis.py
"""

import os
import re
import sqlite3
from collections import Counter

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

DB_PATH    = "data/yelp_restaurants.db"
OUTPUT_DIR = "data/processed"

# ── Price keyword patterns ────────────────────────────────────────────────────
_PRICE_TOKENS = [
    r"\bexpensive\b", r"\bpricey\b",  r"\boverpriced\b", r"\bpricy\b",
    r"\bcheap\b",     r"\baffordable\b", r"\breasonable\b", r"\binexpensive\b",
    r"\bcost\b",      r"\bcosts\b",  r"\bcostly\b",
    r"\bprice\b",     r"\bprices\b", r"\bpricing\b", r"\bpriced\b",
    r"\bworth\b",     r"\bvalue\b",  r"\bwallet\b",  r"\bbudget\b",
    r"\bsplurge\b",   r"\bsteal\b",  r"\bdeal\b",    r"\brip.?off\b",
    r"\$\d+",
]
PRICE_RE = re.compile("|".join(_PRICE_TOKENS), re.IGNORECASE)

# Phrases we want to count explicitly for the word-cloud chart
TRACKED_PHRASES = [
    "too expensive", "a bit pricey", "overpriced", "pricey",
    "prices have gone up", "price hike", "expensive",
    "not worth", "rip-off", "way too expensive",
    "good value", "affordable", "reasonable price",
    "great deal", "cheap", "worth the price",
    "prices have skyrocketed", "hard to justify",
]


def extract_price_sentences(text: str) -> list[str]:
    return [
        s.strip()
        for s in re.split(r"[.!?]+", text)
        if s.strip() and PRICE_RE.search(s)
    ]


def analyse_reviews(conn: sqlite3.Connection, batch: int = 5_000) -> tuple:
    analyser = SentimentIntensityAnalyzer()

    total = conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE year BETWEEN 2015 AND 2023"
    ).fetchone()[0]
    print(f"  Processing {total:,} reviews …")

    records      = []
    phrase_counts = Counter()
    processed    = 0

    while True:
        rows = conn.execute(
            """
            SELECT review_id, stars, year, month, text
            FROM reviews
            WHERE year BETWEEN 2015 AND 2023
            LIMIT ? OFFSET ?
            """,
            (batch, processed),
        ).fetchall()

        if not rows:
            break

        for rid, stars, year, month, text in rows:
            text = text or ""
            has_price = bool(PRICE_RE.search(text))
            price_sentences = extract_price_sentences(text) if has_price else []

            price_sentiment = None
            if price_sentences:
                scores = [analyser.polarity_scores(s)["compound"] for s in price_sentences]
                price_sentiment = sum(scores) / len(scores)

                tl = text.lower()
                for phrase in TRACKED_PHRASES:
                    if phrase in tl:
                        phrase_counts[phrase] += 1

            records.append({
                "review_id":       rid,
                "year":            year,
                "month":           month,
                "stars":           stars,
                "has_price":       has_price,
                "price_sentiment": price_sentiment,
            })

        processed += len(rows)
        if processed % 20_000 == 0:
            print(f"    … {processed:,} / {total:,}", end="\r")

    print(f"    … {processed:,} reviews done   ")
    return pd.DataFrame(records), phrase_counts


def build_monthly_pci(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-review data into monthly Price Concern Index."""
    monthly = (
        df.groupby(["year", "month"])
        .agg(
            total_reviews=("review_id", "count"),
            price_mentions=("has_price", "sum"),
            avg_stars=("stars", "mean"),
        )
        .reset_index()
    )

    # Negative price sentiment = compound < -0.05
    neg = (
        df[df["has_price"] & (df["price_sentiment"].fillna(0) < -0.05)]
        .groupby(["year", "month"])
        .size()
        .reset_index(name="neg_price_reviews")
    )

    monthly = monthly.merge(neg, on=["year", "month"], how="left")
    monthly["neg_price_reviews"] = monthly["neg_price_reviews"].fillna(0)

    monthly["price_concern_index"] = (
        monthly["neg_price_reviews"] / monthly["total_reviews"] * 100
    ).round(2)

    monthly["price_mention_rate"] = (
        monthly["price_mentions"] / monthly["total_reviews"] * 100
    ).round(2)

    monthly["date"] = (
        monthly["year"].astype(str)
        + "-"
        + monthly["month"].astype(str).str.zfill(2)
    )

    return monthly.sort_values(["year", "month"]).reset_index(drop=True)


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        print("Run 01_load_data.py first.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    print("Running NLP price-sentiment analysis …")
    df_reviews, phrase_counts = analyse_reviews(conn)
    conn.close()

    print("\nBuilding monthly Price Concern Index …")
    monthly = build_monthly_pci(df_reviews)
    monthly.to_csv(f"{OUTPUT_DIR}/price_concern_index.csv", index=False)

    # Quick print summary
    def pci_mean(y_from, y_to):
        sub = monthly[(monthly["year"] >= y_from) & (monthly["year"] <= y_to)]
        return sub["price_concern_index"].mean()

    print("\nPrice Concern Index (avg %):")
    print(f"  2015–2019 : {pci_mean(2015,2019):.1f}%")
    print(f"  2020      : {pci_mean(2020,2020):.1f}%")
    print(f"  2021      : {pci_mean(2021,2021):.1f}%")
    print(f"  2022      : {pci_mean(2022,2022):.1f}%")
    print(f"  2023      : {pci_mean(2023,2023):.1f}%")

    # Save phrase counts
    phrase_df = pd.DataFrame(
        [{"phrase": p, "count": c} for p, c in phrase_counts.most_common(20)]
    )
    phrase_df.to_csv(f"{OUTPUT_DIR}/top_price_phrases.csv", index=False)

    print("\nTop price phrases:")
    for _, row in phrase_df.head(10).iterrows():
        print(f"  '{row['phrase']}': {int(row['count']):,}")

    print(f"\nSaved to {OUTPUT_DIR}/")
    print("Next: python 04_cpi_analysis.py")


if __name__ == "__main__":
    main()
