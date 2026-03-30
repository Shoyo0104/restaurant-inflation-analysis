import Head from 'next/head'
import Navbar from '../components/Navbar'
import summary from '../public/data/summary.json'

const Section = ({ title, children }) => (
  <section className="space-y-4">
    <h2 className="text-xl font-bold text-white border-b border-navy-700 pb-2">{title}</h2>
    {children}
  </section>
)

const Code = ({ children }) => (
  <code className="bg-navy-700 text-amber-300 text-xs px-1.5 py-0.5 rounded font-mono">
    {children}
  </code>
)

const Block = ({ children }) => (
  <pre className="bg-navy-800 border border-navy-600 rounded-lg p-4 text-xs text-slate-300 font-mono overflow-x-auto leading-relaxed">
    {children}
  </pre>
)

const Step = ({ n, title, desc }) => (
  <div className="flex gap-4">
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold text-sm">
      {n}
    </div>
    <div>
      <p className="font-medium text-white">{title}</p>
      <p className="text-sm text-slate-400 mt-0.5">{desc}</p>
    </div>
  </div>
)

export default function Methodology() {
  return (
    <>
      <Head>
        <title>Methodology — Restaurant Prices & Inflation</title>
      </Head>
      <Navbar />

      <main className="max-w-3xl mx-auto px-4 py-12 space-y-12">

        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Methodology</h1>
          <p className="text-slate-400">
            End-to-end pipeline: from raw Yelp JSON to statistical conclusions.
          </p>
        </div>

        {/* ── Pipeline overview ── */}
        <Section title="Pipeline Overview">
          <div className="card space-y-5">
            <Step n="1" title="Data Ingestion (01_load_data.py)"
              desc="Parse Yelp Open Dataset NDJSON files, filter to restaurant businesses, extract price tier from business attributes, load into SQLite." />
            <Step n="2" title="SQL Analysis (02_sql_analysis.py)"
              desc="Run structured queries for price tier distribution by city, review volume over time, and category breakdowns. Export CSVs." />
            <Step n="3" title="NLP Analysis (03_nlp_analysis.py)"
              desc="For each review: detect price keywords, extract price-bearing sentences, score with VADER sentiment, aggregate monthly." />
            <Step n="4" title="CPI Data (04_cpi_analysis.py)"
              desc="Fetch FRED series CUSR0000SEFV (CPI for Food Away from Home). Calculate YoY% change for each month." />
            <Step n="5" title="Export (05_combine_export.py)"
              desc="Merge PCI + CPI time series, compute Pearson correlation + linear regression, export JSON files to the web app." />
          </div>
        </Section>

        {/* ── SQL Schema ── */}
        <Section title="SQL Schema">
          <p className="text-sm text-slate-400">
            Two tables loaded into SQLite with foreign-key relationship and indexes on city, price tier, year, and month.
          </p>
          <Block>{`CREATE TABLE businesses (
    business_id  TEXT PRIMARY KEY,
    name         TEXT,
    city         TEXT,
    state        TEXT,
    latitude     REAL,
    longitude    REAL,
    stars        REAL,
    review_count INTEGER,
    categories   TEXT,
    price_tier   INTEGER   -- 1=$, 2=$$, 3=$$$, 4=$$$$
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

CREATE INDEX idx_biz_city  ON businesses(city);
CREATE INDEX idx_biz_price ON businesses(price_tier);
CREATE INDEX idx_rev_ym    ON reviews(year, month);
CREATE INDEX idx_rev_biz   ON reviews(business_id);`}</Block>

          <p className="text-sm text-slate-400">
            Example query — price tier distribution by city:
          </p>
          <Block>{`SELECT
    city, state, price_tier,
    COUNT(*) AS restaurant_count,
    AVG(stars) AS avg_stars
FROM businesses
WHERE price_tier IS NOT NULL
GROUP BY city, state, price_tier
ORDER BY city, price_tier;`}</Block>
        </Section>

        {/* ── NLP methodology ── */}
        <Section title="NLP: Price Concern Index">
          <p className="text-sm text-slate-400 leading-relaxed">
            For each review we apply a two-stage process:
          </p>

          <div className="space-y-3">
            <div className="card">
              <p className="text-white font-medium text-sm mb-1">Stage 1 — Keyword detection</p>
              <p className="text-slate-400 text-sm mb-2">
                A regex pattern matches 26 price-related tokens:
              </p>
              <Block>{`PRICE_KEYWORDS = [
    r"\\bexpensive\\b", r"\\bpricey\\b", r"\\boverpriced\\b",
    r"\\bcheap\\b",     r"\\baffordable\\b", r"\\breasonable\\b",
    r"\\bprice\\b",     r"\\bprices\\b",    r"\\bpricing\\b",
    r"\\bvalue\\b",     r"\\bworth\\b",     r"\\$\\d+",  # dollar amounts
    ...
]`}</Block>
            </div>

            <div className="card">
              <p className="text-white font-medium text-sm mb-1">Stage 2 — VADER sentiment on price sentences</p>
              <p className="text-slate-400 text-sm">
                We extract only the sentences containing a keyword, then score each with
                VADER. A compound score &lt; −0.05 classifies the sentence as a
                <span className="text-red-400 font-medium"> price complaint</span>.
              </p>
            </div>

            <div className="card">
              <p className="text-white font-medium text-sm mb-2">Price Concern Index formula</p>
              <Block>{`PCI_t = (reviews with negative price sentiment in month t)
        ─────────────────────────────────────────────────── × 100
                (total reviews in month t)`}</Block>
              <p className="text-xs text-slate-500 mt-2">
                This gives a single 0–100 index per month that rises when price complaints increase.
              </p>
            </div>
          </div>

          <p className="text-sm text-slate-400 leading-relaxed">
            VADER (Valence Aware Dictionary and sEntiment Reasoner) is a rule-based model
            pre-trained on social media text — appropriate for informal review language.
            It runs without any external API or model download.
          </p>
        </Section>

        {/* ── CPI Data ── */}
        <Section title="CPI Data Source">
          <div className="card space-y-2">
            <div className="flex items-start gap-3">
              <span className="text-amber-400 text-lg mt-0.5">📈</span>
              <div>
                <p className="font-medium text-white text-sm">FRED Series: CUSR0000SEFV</p>
                <p className="text-slate-400 text-sm">Consumer Price Index — Food Away from Home</p>
                <p className="text-slate-500 text-xs mt-0.5">
                  Published by the US Bureau of Labor Statistics · Base period: 1982–84 = 100
                </p>
              </div>
            </div>
          </div>
          <p className="text-sm text-slate-400 leading-relaxed">
            We use the year-over-year percentage change (YoY%) as the inflation signal when
            computing the YoY correlation, and the raw index level for the scatter plot.
            The pipeline fetches live data if a <Code>FRED_API_KEY</Code> is set; otherwise it
            uses built-in approximate values from the BLS website.
          </p>
        </Section>

        {/* ── Statistical methods ── */}
        <Section title="Statistical Methods">
          <div className="space-y-3 text-sm">
            <div className="card">
              <p className="text-white font-medium mb-1">Pearson Correlation</p>
              <p className="text-slate-400">
                Measures linear association between monthly PCI and CPI level.
                Result: <span className="text-amber-400 font-bold">r = {summary.pearson_r}</span>,
                p = {summary.pearson_p} (n = {summary.n_months} months).
              </p>
            </div>
            <div className="card">
              <p className="text-white font-medium mb-1">Linear Regression</p>
              <p className="text-slate-400">
                OLS regression of PCI on CPI. Slope = {summary.regression_slope},
                R² = <span className="text-amber-400 font-bold">{summary.regression_r2}</span>.
                CPI explains {(summary.regression_r2 * 100).toFixed(0)}% of variance in the PCI.
              </p>
            </div>
            <div className="card">
              <p className="text-white font-medium mb-1">Limitations</p>
              <ul className="text-slate-400 space-y-1 list-disc list-inside text-sm">
                <li>Sample data (synthetic) — run with real Yelp dataset for production results</li>
                <li>Correlation does not imply causation — both series share a common time trend</li>
                <li>VADER is a general-purpose tool; domain fine-tuning could improve precision</li>
                <li>Yelp users are not a random sample of all restaurant diners</li>
              </ul>
            </div>
          </div>
        </Section>

        {/* ── Tech stack ── */}
        <Section title="Technology Stack">
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              { cat: 'Data', items: ['Yelp Open Dataset', 'FRED API (BLS/FRED)'] },
              { cat: 'Storage', items: ['SQLite 3', 'pandas DataFrames'] },
              { cat: 'NLP', items: ['VADER Sentiment', 'Python re (regex)'] },
              { cat: 'Statistics', items: ['scipy.stats', 'numpy'] },
              { cat: 'Web', items: ['Next.js 14', 'Recharts', 'react-leaflet'] },
              { cat: 'Deployment', items: ['Vercel', 'Static JSON export'] },
            ].map(({ cat, items }) => (
              <div key={cat} className="card">
                <p className="text-xs text-amber-400 font-medium mb-1.5">{cat}</p>
                {items.map(item => (
                  <p key={item} className="text-slate-300 text-xs">{item}</p>
                ))}
              </div>
            ))}
          </div>
        </Section>

      </main>
    </>
  )
}
