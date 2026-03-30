#!/usr/bin/env bash
# Full pipeline runner for restaurant-inflation-analysis
# Run from the /pipeline directory
#
# Usage:
#   ./run_pipeline.sh             # uses synthetic sample data
#   ./run_pipeline.sh --real      # expects data in data/raw/
#   FRED_API_KEY=xxx ./run_pipeline.sh

set -e
cd "$(dirname "$0")"

echo "====================================="
echo "  Restaurant Prices + Inflation"
echo "  Data Pipeline"
echo "====================================="

# Create virtual env if it doesn't exist
if [ ! -d ".venv" ]; then
  echo ""
  echo "Creating virtual environment ..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo ""
echo "Installing dependencies ..."
pip install -q -r requirements.txt

# Generate sample data unless --real flag is passed
if [[ "$1" != "--real" ]]; then
  echo ""
  echo "Step 0: Generating synthetic sample data ..."
  python generate_sample_data.py
fi

echo ""
echo "Step 1: Loading data into SQLite ..."
python 01_load_data.py

echo ""
echo "Step 2: SQL analysis ..."
python 02_sql_analysis.py

echo ""
echo "Step 3: NLP price-sentiment analysis ..."
python 03_nlp_analysis.py

echo ""
echo "Step 4: Fetching CPI data ..."
python 04_cpi_analysis.py

echo ""
echo "Step 5: Combining results + exporting JSON ..."
python 05_combine_export.py

echo ""
echo "====================================="
echo "  Pipeline complete!"
echo "  JSON files written to ../web/public/data/"
echo ""
echo "  To start the web app:"
echo "    cd ../web"
echo "    npm install"
echo "    npm run dev"
echo "====================================="
