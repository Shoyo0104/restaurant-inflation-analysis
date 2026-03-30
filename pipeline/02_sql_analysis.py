"""
Step 2 — SQL analysis of restaurant price tiers.

Runs several analytical queries against the SQLite database and
saves results as CSVs to data/processed/.

Key queries
───────────
1. Price tier distribution by city
2. City summary stats (count, avg stars, lat/lon)
3. Monthly review volume + avg price tier over time
4. Top cuisine categories by restaurant count
5. Price tier mix per year (to detect upward drift)

Run: python 02_sql_analysis.py
"""

import os
import sqlite3

import pandas as pd

DB_PATH    = "data/yelp_restaurants.db"
OUTPUT_DIR = "data/processed"


def run_queries(conn: sqlite3.Connection) -> dict:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = {}

    # ── 1. Price tier distribution by city ───────────────────────────────────
    print("Query 1: Price tier distribution by city …")
    df = pd.read_sql_query(
        """
        SELECT
            city,
            state,
            price_tier,
            COUNT(*)           AS restaurant_count,
            ROUND(AVG(stars),2) AS avg_stars,
            SUM(review_count)  AS total_reviews
        FROM businesses
        WHERE price_tier IS NOT NULL
          AND city  != ''
          AND state != ''
        GROUP BY city, state, price_tier
        ORDER BY city, price_tier
        """,
        conn,
    )
    df.to_csv(f"{OUTPUT_DIR}/price_tier_by_city.csv", index=False)
    results["price_tier_by_city"] = df
    print(f"  {len(df)} rows across {df['city'].nunique()} cities")

    # ── 2. City-level summary ─────────────────────────────────────────────────
    print("Query 2: City summary stats …")
    df = pd.read_sql_query(
        """
        SELECT
            city,
            state,
            COUNT(*)                        AS restaurant_count,
            ROUND(AVG(stars), 2)            AS avg_stars,
            SUM(review_count)               AS total_reviews,
            ROUND(AVG(CAST(price_tier AS REAL)), 3) AS avg_price_tier,
            ROUND(AVG(latitude),  4)        AS lat,
            ROUND(AVG(longitude), 4)        AS lon
        FROM businesses
        WHERE price_tier IS NOT NULL
          AND city     != ''
          AND latitude  IS NOT NULL
        GROUP BY city, state
        HAVING restaurant_count > 50
        ORDER BY restaurant_count DESC
        LIMIT 20
        """,
        conn,
    )
    df.to_csv(f"{OUTPUT_DIR}/city_stats.csv", index=False)
    results["city_stats"] = df
    print(f"  {len(df)} cities")

    # ── 3. Monthly review volume + avg price tier ─────────────────────────────
    print("Query 3: Review volume by year / month …")
    df = pd.read_sql_query(
        """
        SELECT
            r.year,
            r.month,
            COUNT(*)                                AS review_count,
            ROUND(AVG(r.stars), 3)                  AS avg_stars,
            ROUND(AVG(CAST(b.price_tier AS REAL)),3) AS avg_price_tier
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE r.year BETWEEN 2015 AND 2023
          AND b.price_tier IS NOT NULL
        GROUP BY r.year, r.month
        ORDER BY r.year, r.month
        """,
        conn,
    )
    df.to_csv(f"{OUTPUT_DIR}/reviews_over_time.csv", index=False)
    results["reviews_over_time"] = df
    print(f"  {len(df)} months of data")

    # ── 4. Category breakdown ─────────────────────────────────────────────────
    print("Query 4: Top cuisine categories …")
    df = pd.read_sql_query(
        """
        SELECT
            TRIM(
                SUBSTR(categories, 1,
                    CASE WHEN INSTR(categories, ',') > 0
                         THEN INSTR(categories, ',') - 1
                         ELSE LENGTH(categories)
                    END)
            ) AS primary_category,
            COUNT(*)                                AS restaurant_count,
            ROUND(AVG(CAST(price_tier AS REAL)), 2) AS avg_price_tier,
            ROUND(AVG(stars), 2)                    AS avg_stars
        FROM businesses
        WHERE price_tier IS NOT NULL
        GROUP BY primary_category
        HAVING restaurant_count > 20
        ORDER BY restaurant_count DESC
        LIMIT 20
        """,
        conn,
    )
    df.to_csv(f"{OUTPUT_DIR}/category_stats.csv", index=False)
    results["category_stats"] = df
    print(f"  {len(df)} categories")

    # ── 5. Price tier mix per year ────────────────────────────────────────────
    print("Query 5: Annual price tier mix …")
    df = pd.read_sql_query(
        """
        SELECT
            r.year,
            b.price_tier,
            COUNT(*) AS review_count
        FROM reviews r
        JOIN businesses b ON r.business_id = b.business_id
        WHERE r.year BETWEEN 2015 AND 2023
          AND b.price_tier IS NOT NULL
        GROUP BY r.year, b.price_tier
        ORDER BY r.year, b.price_tier
        """,
        conn,
    )
    df.to_csv(f"{OUTPUT_DIR}/tier_by_year.csv", index=False)
    results["tier_by_year"] = df
    print(f"  Saved tier trends")

    return results


def print_summary(conn: sqlite3.Connection):
    print("\n=== KEY SQL FINDINGS ===")

    # Overall price tier distribution
    df = pd.read_sql_query(
        """
        SELECT price_tier,
               COUNT(*) AS n,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM businesses
        WHERE price_tier IS NOT NULL
        GROUP BY price_tier
        ORDER BY price_tier
        """,
        conn,
    )
    labels = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}
    print("\nOverall price tier distribution:")
    for _, row in df.iterrows():
        t = int(row["price_tier"])
        print(f"  {labels.get(t, str(t)):<5} {int(row['n']):>7,}  ({row['pct']}%)")

    # Top 5 cities
    df2 = pd.read_sql_query(
        "SELECT city, COUNT(*) AS n FROM businesses GROUP BY city ORDER BY n DESC LIMIT 5",
        conn,
    )
    print("\nTop 5 cities by restaurant count:")
    for _, row in df2.iterrows():
        print(f"  {row['city']:<18} {int(row['n']):,}")


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        print("Run 01_load_data.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    run_queries(conn)
    print_summary(conn)
    conn.close()

    print(f"\nCSVs saved to {OUTPUT_DIR}/")
    print("Next: python 03_nlp_analysis.py")


if __name__ == "__main__":
    main()
