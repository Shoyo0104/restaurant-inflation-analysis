"""
Step 1 — Load Yelp dataset (or sample) into SQLite.

The script looks for real Yelp Open Dataset files in data/raw/ first.
If not found it falls back to the synthetic sample in data/sample/.

Run: python 01_load_data.py

Real data download: https://www.yelp.com/dataset  (free academic licence)
Expected files:
  data/raw/yelp_academic_dataset_business.json
  data/raw/yelp_academic_dataset_review.json
"""

import json
import os
import sqlite3
import sys

DB_PATH      = "data/yelp_restaurants.db"
SEARCH_DIRS  = ["data/raw", "data/sample"]
BIZ_FILE     = "yelp_academic_dataset_business.json"
REV_FILE     = "yelp_academic_dataset_review.json"


# ── Schema ────────────────────────────────────────────────────────────────────

DDL = """
DROP TABLE IF EXISTS businesses;
DROP TABLE IF EXISTS reviews;

CREATE TABLE businesses (
    business_id  TEXT PRIMARY KEY,
    name         TEXT,
    city         TEXT,
    state        TEXT,
    latitude     REAL,
    longitude    REAL,
    stars        REAL,
    review_count INTEGER,
    categories   TEXT,
    price_tier   INTEGER
);

CREATE TABLE reviews (
    review_id   TEXT PRIMARY KEY,
    business_id TEXT,
    stars       INTEGER,
    date        TEXT,
    year        INTEGER,
    month       INTEGER,
    text        TEXT,
    FOREIGN KEY (business_id) REFERENCES businesses(business_id)
);

CREATE INDEX idx_biz_city    ON businesses(city);
CREATE INDEX idx_biz_price   ON businesses(price_tier);
CREATE INDEX idx_rev_ym      ON reviews(year, month);
CREATE INDEX idx_rev_biz     ON reviews(business_id);
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_data_dir() -> str | None:
    for d in SEARCH_DIRS:
        if os.path.exists(os.path.join(d, BIZ_FILE)) and \
           os.path.exists(os.path.join(d, REV_FILE)):
            return d
    return None


def load_businesses(conn: sqlite3.Connection, path: str) -> int:
    print(f"  Loading businesses from {path} …")
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            b = json.loads(line)

            cats = b.get("categories") or ""
            if "Restaurant" not in cats and "Food" not in cats:
                continue

            attrs = b.get("attributes") or {}
            pt = attrs.get("RestaurantsPriceRange2")
            if isinstance(pt, str):
                try:
                    pt = int(pt)
                except ValueError:
                    pt = None

            rows.append((
                b.get("business_id", ""),
                b.get("name", ""),
                b.get("city", ""),
                b.get("state", ""),
                b.get("latitude"),
                b.get("longitude"),
                b.get("stars"),
                b.get("review_count", 0),
                cats,
                pt,
            ))

    conn.executemany(
        "INSERT OR IGNORE INTO businesses VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    return len(rows)


def load_reviews(conn: sqlite3.Connection, path: str, batch: int = 10_000) -> int:
    print(f"  Loading reviews from {path} …")

    valid = {r[0] for r in conn.execute("SELECT business_id FROM businesses")}
    total = 0
    buf   = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)

            bid = r.get("business_id", "")
            if bid not in valid:
                continue

            ds = (r.get("date") or "")[:10]
            try:
                y, m = int(ds[:4]), int(ds[5:7])
            except (ValueError, IndexError):
                continue

            if y < 2015 or y > 2023:
                continue

            buf.append((
                r.get("review_id", ""),
                bid,
                r.get("stars", 3),
                ds,
                y,
                m,
                (r.get("text") or "")[:2000],
            ))

            if len(buf) >= batch:
                conn.executemany(
                    "INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?,?,?)", buf
                )
                conn.commit()
                total += len(buf)
                buf = []
                print(f"    … {total:,} reviews", end="\r")

    if buf:
        conn.executemany(
            "INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?,?,?)", buf
        )
        conn.commit()
        total += len(buf)

    return total


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    data_dir = find_data_dir()
    if data_dir is None:
        print("No data found.")
        print("  Option A: python generate_sample_data.py")
        print("  Option B: download real Yelp dataset → data/raw/")
        sys.exit(1)

    print(f"Data source: {data_dir}")

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)

    n_biz = load_businesses(conn, os.path.join(data_dir, BIZ_FILE))
    n_rev = load_reviews(conn,    os.path.join(data_dir, REV_FILE))

    print(f"\nDatabase ready: {DB_PATH}")
    print(f"  Restaurants : {n_biz:,}")
    print(f"  Reviews     : {n_rev:,}")
    print("\nNext: python 02_sql_analysis.py")

    conn.close()


if __name__ == "__main__":
    main()
