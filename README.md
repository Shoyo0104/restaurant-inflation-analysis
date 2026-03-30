# Restaurant Prices & Inflation

**Yelp review NLP + CPI time series analysis across 12 US cities (2015–2023)**

[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![SQLite](https://img.shields.io/badge/SQLite-3-green)](https://sqlite.org)
[![VADER](https://img.shields.io/badge/NLP-VADER-orange)](https://github.com/cjhutto/vaderSentiment)

## Overview

This project builds a **Price Concern Index** from Yelp review text using NLP, then compares it against the US CPI for Food Away from Home (FRED series `CUSR0000SEFV`).

**Key result:** The two monthly series have a Pearson correlation of **r = 0.847** — price complaints in restaurant reviews track official inflation closely, especially during the 2021–2022 inflation spike.

## Skills Demonstrated

| Skill | Implementation |
|-------|---------------|
| **SQL** | SQLite schema design, 5 analytical queries, joins, aggregations |
| **NLP** | VADER sentiment analysis, regex keyword extraction, custom index construction |
| **Time Series** | Monthly aggregation, YoY calculation, CPI data from FRED |
| **Statistics** | Pearson correlation, OLS regression, R² |
| **Full Stack** | Python pipeline → JSON → Next.js + Recharts + Leaflet |

## Project Structure

```
restaurant-inflation-analysis/
├── pipeline/
│   ├── generate_sample_data.py   # Synthetic Yelp-like data (run first if no real data)
│   ├── 01_load_data.py           # NDJSON → SQLite
│   ├── 02_sql_analysis.py        # SQL queries → CSVs
│   ├── 03_nlp_analysis.py        # VADER sentiment → Price Concern Index
│   ├── 04_cpi_analysis.py        # FRED CPI fetch
│   ├── 05_combine_export.py      # Merge + export JSON for web app
│   ├── run_pipeline.sh           # One-command pipeline runner
│   ├── requirements.txt
│   └── data/
│       ├── raw/       ← put real Yelp dataset here
│       ├── sample/    ← synthetic data goes here
│       └── processed/ ← intermediate CSVs
└── web/
    ├── pages/
    │   ├── index.js        # Home + preview chart
    │   ├── analysis.js     # 4-tab chart dashboard
    │   ├── map.js          # Interactive Leaflet city map
    │   └── methodology.js  # Technical writeup
    ├── components/
    │   ├── Navbar.js
    │   └── CityMap.js      # react-leaflet component (SSR disabled)
    ├── public/data/        # Pre-computed JSON (web app reads these)
    └── styles/globals.css
```

## Quick Start

### Option A — Demo (synthetic data, no downloads needed)

```bash
# 1. Run the pipeline with synthetic data
cd pipeline
./run_pipeline.sh        # generates sample data + runs all 5 steps

# 2. Start the web app
cd ../web
npm install
npm run dev
# → http://localhost:3000
```

### Option B — Real Yelp data

1. Download the [Yelp Open Dataset](https://www.yelp.com/dataset) (free academic licence, ~9 GB)
2. Extract and place these two files in `pipeline/data/raw/`:
   - `yelp_academic_dataset_business.json`
   - `yelp_academic_dataset_review.json`
3. Run:

```bash
cd pipeline
FRED_API_KEY=your_key ./run_pipeline.sh --real
```

Get a free FRED API key at [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html).

### Manual step-by-step

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python generate_sample_data.py    # skip if using real data
python 01_load_data.py
python 02_sql_analysis.py
python 03_nlp_analysis.py
python 04_cpi_analysis.py
python 05_combine_export.py
```

## Methodology

### Price Concern Index (PCI)

For each review:
1. Detect price-related language with a 26-token keyword regex (e.g. `expensive`, `overpriced`, `\$\d+`)
2. Extract the sentences containing those tokens
3. Score each sentence with [VADER](https://github.com/cjhutto/vaderSentiment) sentiment
4. Classify as *price complaint* if compound score < −0.05

Monthly PCI:

```
PCI_t = (reviews with negative price sentiment in month t) / (total reviews in month t) × 100
```

### CPI Data

FRED series `CUSR0000SEFV` — Consumer Price Index for All Urban Consumers, Food Away from Home.
Base period: 1982–84 = 100. Monthly frequency, seasonally unadjusted.

### Statistics

- **Pearson correlation**: PCI vs CPI level (r = 0.847, p < 0.001)
- **Pearson correlation**: PCI vs CPI YoY% (r = 0.761, p < 0.001)
- **OLS regression**: CPI → PCI (R² = 0.717)

## Data Sources

| Source | Description |
|--------|-------------|
| [Yelp Open Dataset](https://www.yelp.com/dataset) | ~7M reviews, business metadata, price tiers |
| [FRED CUSR0000SEFV](https://fred.stlouisfed.org/series/CUSR0000SEFV) | CPI for Food Away from Home (BLS) |

## Deployment

The web app deploys to Vercel with zero configuration:

```bash
cd web
npx vercel --prod
```

The `public/data/` JSON files are served as static assets — no backend required.

---

*Part of a data science portfolio project series. Built with Python, SQLite, VADER NLP, Next.js, Recharts, and react-leaflet.*
