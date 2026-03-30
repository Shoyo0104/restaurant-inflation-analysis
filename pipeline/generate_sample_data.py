"""
Generate synthetic Yelp-like restaurant data for the inflation analysis.

This script creates realistic sample data when the real Yelp Open Dataset
is not available. Price-complaint language in reviews is calibrated to
correlate with historical US CPI for Food Away from Home (2015–2023).

Run: python generate_sample_data.py
Output: data/sample/yelp_academic_dataset_business.json
        data/sample/yelp_academic_dataset_review.json
"""

import json
import random
import string
import os
from datetime import datetime, timedelta

random.seed(42)

# ── Cities (subset of real Yelp Open Dataset cities) ─────────────────────────
CITIES = [
    {"city": "Philadelphia",  "state": "PA", "lat": 39.9526, "lon": -75.1652},
    {"city": "Tampa",         "state": "FL", "lat": 27.9506, "lon": -82.4572},
    {"city": "Nashville",     "state": "TN", "lat": 36.1627, "lon": -86.7816},
    {"city": "Indianapolis",  "state": "IN", "lat": 39.7684, "lon": -86.1581},
    {"city": "Reno",          "state": "NV", "lat": 39.5296, "lon": -119.8138},
    {"city": "Saint Louis",   "state": "MO", "lat": 38.6270, "lon": -90.1994},
    {"city": "Tucson",        "state": "AZ", "lat": 32.2226, "lon": -110.9747},
    {"city": "New Orleans",   "state": "LA", "lat": 29.9511, "lon": -90.0715},
    {"city": "Charlotte",     "state": "NC", "lat": 35.2271, "lon": -80.8431},
    {"city": "Pittsburgh",    "state": "PA", "lat": 40.4406, "lon": -79.9959},
    {"city": "Phoenix",       "state": "AZ", "lat": 33.4484, "lon": -112.0740},
    {"city": "Las Vegas",     "state": "NV", "lat": 36.1699, "lon": -115.1398},
]

CATEGORIES = [
    "Restaurants", "American (Traditional)", "Italian", "Mexican",
    "Chinese", "Japanese", "Pizza", "Burgers", "Sandwiches", "Seafood",
    "BBQ", "Thai", "Indian", "Mediterranean", "Vietnamese",
    "Breakfast & Brunch", "Cafes", "Steakhouses", "Sushi Bars", "Fast Food",
]

# Price tier distribution per city (weights for $, $$, $$$, $$$$)
CITY_PRICE_DIST = {
    "Las Vegas":     [0.32, 0.30, 0.22, 0.16],
    "New Orleans":   [0.36, 0.32, 0.21, 0.11],
    "Nashville":     [0.40, 0.33, 0.19, 0.08],
    "Philadelphia":  [0.40, 0.35, 0.18, 0.07],
    "Charlotte":     [0.42, 0.35, 0.17, 0.06],
    "Tampa":         [0.44, 0.35, 0.15, 0.06],
    "Pittsburgh":    [0.43, 0.36, 0.16, 0.05],
    "Phoenix":       [0.43, 0.36, 0.16, 0.05],
    "Saint Louis":   [0.44, 0.36, 0.15, 0.05],
    "Reno":          [0.43, 0.37, 0.15, 0.05],
    "Indianapolis":  [0.47, 0.35, 0.13, 0.05],
    "Tucson":        [0.47, 0.35, 0.14, 0.04],
}

MEALS  = ["breakfast", "lunch", "dinner", "brunch", "a quick bite", "date night"]
DISHES = ["burger", "pasta", "tacos", "sushi", "pizza", "steak", "salad",
          "wings", "ribs", "noodles", "sandwich", "curry", "fish", "nachos"]

# Review templates — {price_phrase} is injected based on the inflation era
TEMPLATES = [
    "Great food and service. {pp}The staff was friendly and the ambiance was perfect.",
    "Love this place! {pp}Been coming here for years.",
    "Pretty good experience overall. {pp}The food came out quickly.",
    "Decent spot for {meal}. {pp}Nothing extraordinary but solid.",
    "Really enjoyed the {dish}. {pp}Will definitely come back.",
    "Nice atmosphere and great food. {pp}Highly recommend!",
    "The {dish} was delicious. {pp}Service was a bit slow though.",
    "Good food, good service. {pp}Can't ask for more!",
    "This is my go-to spot for {meal}. {pp}Never disappointed.",
    "Fantastic restaurant! {pp}The {dish} is a must-try.",
    "Came here with the family. {pp}Everyone enjoyed their meal.",
    "The portions are generous. {pp}The {dish} is excellent.",
    "Really enjoyed my visit. {pp}Will be back for sure.",
]

# Price phrases by inflation era — frequency of negative language increases with CPI
PRICE_PHRASES = {
    # 2015–2019: low, stable inflation (~2% YoY)
    "low": [
        "", "", "", "", "",                          # 50% no mention
        "Prices are reasonable. ",
        "Very affordable for the quality. ",
        "Good value for the money. ",
        "A bit pricey but worth it. ",
        "Prices have gone up a little. ",
    ],
    # 2020: COVID — muted price sensitivity
    "covid": [
        "", "", "", "", "",
        "Reasonable prices. ",
        "Good value. ",
        "Prices held steady, appreciated it. ",
        "Slightly expensive but understandable. ",
        "Prices are a little high for reduced portions. ",
    ],
    # 2021: inflation starting to bite
    "early_inflation": [
        "", "", "",
        "Prices have gone up. ",
        "Getting a bit pricey. ",
        "More expensive than I remember. ",
        "Good food but getting pricey. ",
        "Worth the price for the quality. ",
        "Prices have definitely increased. ",
        "A bit overpriced now. ",
        "Starting to feel expensive. ",
        "The prices have really jumped. ",
    ],
    # 2022: peak inflation (~8% YoY CPI)
    "peak": [
        "", "",
        "Prices are way too high now. ",
        "Getting really expensive. ",
        "Overpriced for what you get. ",
        "The prices have skyrocketed. ",
        "Not worth the price anymore. ",
        "Used to be affordable, not anymore. ",
        "The cost has gone up significantly. ",
        "Really expensive these days. ",
        "Prices have gone through the roof. ",
        "Hard to justify the price. ",
        "Expensive but still decent. ",
        "The price hikes are getting out of hand. ",
        "Way overpriced. ",
    ],
    # 2023: easing but still elevated
    "easing": [
        "", "",
        "Still pricey but stabilising. ",
        "Prices are high but seem to be levelling off. ",
        "Expensive, though service makes up for it. ",
        "A bit overpriced. ",
        "Getting a bit pricey. ",
        "Prices have gone up. ",
        "Good value for the quality. ",
        "Worth the price. ",
    ],
}

# Review volume distribution by year (weights, sums to ~1)
YEAR_WEIGHTS = {
    2015: 0.06, 2016: 0.07, 2017: 0.09, 2018: 0.11,
    2019: 0.13, 2020: 0.08, 2021: 0.15, 2022: 0.18, 2023: 0.13,
}


def _era(year: int) -> str:
    if year < 2020:
        return "low"
    if year == 2020:
        return "covid"
    if year == 2021:
        return "early_inflation"
    if year == 2022:
        return "peak"
    return "easing"


def _random_id(n: int = 22) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def _random_date(year: int, month: int) -> str:
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    days = (end - start).days
    return (start + timedelta(days=random.randint(0, days - 1))).strftime("%Y-%m-%d")


def generate_businesses(n_per_city: int = 2500) -> list:
    businesses = []
    for c in CITIES:
        n = n_per_city + random.randint(-400, 400)
        dist = CITY_PRICE_DIST[c["city"]]
        for _ in range(n):
            cats = random.sample(CATEGORIES, random.randint(1, 3))
            if "Restaurants" not in cats:
                cats.insert(0, "Restaurants")
            tier = random.choices([1, 2, 3, 4], weights=dist)[0]
            businesses.append({
                "business_id": _random_id(),
                "name": f"Restaurant {_random_id(6)}",
                "city": c["city"],
                "state": c["state"],
                "latitude":  round(c["lat"] + random.uniform(-0.12, 0.12), 5),
                "longitude": round(c["lon"] + random.uniform(-0.12, 0.12), 5),
                "stars": round(random.uniform(2.5, 5.0) * 2) / 2,
                "review_count": random.randint(5, 600),
                "categories": ", ".join(cats),
                "attributes": {"RestaurantsPriceRange2": tier},
            })
    return businesses


def generate_reviews(businesses: list) -> list:
    years  = list(YEAR_WEIGHTS.keys())
    wts    = list(YEAR_WEIGHTS.values())
    reviews = []

    for biz in businesses:
        n = max(1, int(biz["review_count"] * random.uniform(0.85, 1.15)))
        for _ in range(n):
            year  = random.choices(years, weights=wts)[0]
            month = random.randint(1, 12)
            era   = _era(year)

            pp   = random.choice(PRICE_PHRASES[era])
            tmpl = random.choice(TEMPLATES)
            text = tmpl.format(pp=pp, meal=random.choice(MEALS), dish=random.choice(DISHES))

            # Stars reflect price negativity
            neg = any(w in pp.lower() for w in
                      ["overpriced", "skyrocketed", "out of hand", "way too high", "way overpriced"])
            pricey = any(w in pp.lower() for w in ["pricey", "expensive", "jumped"])

            if neg:
                stars = random.choices([1, 2, 3, 4, 5], weights=[0.22, 0.30, 0.28, 0.14, 0.06])[0]
            elif pricey:
                stars = random.choices([1, 2, 3, 4, 5], weights=[0.08, 0.15, 0.30, 0.32, 0.15])[0]
            else:
                stars = random.choices([1, 2, 3, 4, 5], weights=[0.04, 0.07, 0.14, 0.36, 0.39])[0]

            reviews.append({
                "review_id":   _random_id(),
                "business_id": biz["business_id"],
                "stars":       stars,
                "date":        _random_date(year, month),
                "text":        text,
            })
    return reviews


def main():
    os.makedirs("data/sample", exist_ok=True)

    print("Generating businesses …")
    businesses = generate_businesses(n_per_city=2500)
    print(f"  {len(businesses):,} restaurants across {len(CITIES)} cities")

    print("Generating reviews …")
    reviews = generate_reviews(businesses)
    print(f"  {len(reviews):,} reviews (2015–2023)")

    biz_path = "data/sample/yelp_academic_dataset_business.json"
    rev_path = "data/sample/yelp_academic_dataset_review.json"

    print("Saving …")
    with open(biz_path, "w", encoding="utf-8") as f:
        for b in businesses:
            f.write(json.dumps(b) + "\n")

    with open(rev_path, "w", encoding="utf-8") as f:
        for r in reviews:
            f.write(json.dumps(r) + "\n")

    print(f"\nDone!")
    print(f"  {biz_path}")
    print(f"  {rev_path}")
    print("\nNext: python 01_load_data.py")


if __name__ == "__main__":
    main()
