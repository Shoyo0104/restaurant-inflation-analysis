import Head from 'next/head'
import Link from 'next/link'
import Navbar from '../components/Navbar'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import summaryData from '../public/data/summary.json'
import seriesData  from '../public/data/sentiment_cpi.json'

// Show only Jan of each year for the preview chart
const previewData = seriesData.filter(d => d.month === 1 || d.month === 7)

const StatCard = ({ label, value, sub, highlight }) => (
  <div className="stat-card">
    <p className="text-xs text-slate-400 uppercase tracking-widest">{label}</p>
    <p className={`text-3xl font-bold ${highlight ? 'text-amber-400' : 'text-white'}`}>
      {value}
    </p>
    {sub && <p className="text-xs text-slate-500">{sub}</p>}
  </div>
)

const FeatureCard = ({ href, icon, title, desc }) => (
  <Link href={href} className="card hover:border-amber-500/40 hover:bg-navy-700 transition-all group">
    <div className="text-2xl mb-3">{icon}</div>
    <h3 className="font-semibold text-white group-hover:text-amber-400 transition-colors mb-1">{title}</h3>
    <p className="text-sm text-slate-400">{desc}</p>
  </Link>
)

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-navy-700 border border-navy-600 rounded-lg p-3 text-xs">
      <p className="text-slate-300 mb-1 font-medium">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: <span className="font-bold">{typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</span>
        </p>
      ))}
    </div>
  )
}

export default function Home() {
  const s = summaryData

  return (
    <>
      <Head>
        <title>Restaurant Prices & Inflation</title>
        <meta name="description" content="How restaurant review sentiment tracks US food-away-from-home inflation" />
      </Head>

      <Navbar />

      <main className="max-w-6xl mx-auto px-4 py-12 space-y-16">

        {/* ── Hero ── */}
        <section className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 pill bg-amber-500/10 text-amber-400 border border-amber-500/20 mb-2">
            <span>NLP + SQL + Time Series</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight">
            Restaurant Prices &<br />
            <span className="text-amber-400">Inflation Signals</span>
          </h1>
          <p className="max-w-2xl mx-auto text-slate-400 text-lg">
            Using NLP on {(s.total_reviews / 1000).toFixed(0)}K+ Yelp reviews across {s.total_cities} US cities to
            build a <em className="text-white not-italic font-medium">Price Concern Index</em> — then
            comparing it against the FRED CPI for Food Away from Home.
          </p>
          <div className="flex flex-wrap justify-center gap-3 pt-2">
            <Link href="/analysis" className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-navy-900 font-semibold rounded-lg transition-colors text-sm">
              View Analysis
            </Link>
            <Link href="/map" className="px-5 py-2.5 border border-navy-600 hover:border-amber-500/50 text-slate-300 rounded-lg transition-colors text-sm">
              Explore Map
            </Link>
          </div>
        </section>

        {/* ── Key Stats ── */}
        <section>
          <h2 className="section-title">Key Results</h2>
          <p className="section-sub">Headline numbers from the full pipeline</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard
              label="Pearson r"
              value={s.pearson_r}
              sub="PCI vs CPI level"
              highlight
            />
            <StatCard
              label="Regression R²"
              value={s.regression_r2}
              sub="CPI explains PCI variance"
            />
            <StatCard
              label="PCI 2022 avg"
              value={`${s.pci_avg_2022}%`}
              sub={`vs ${s.pci_avg_pre2020}% pre-2020`}
              highlight
            />
            <StatCard
              label="Peak YoY CPI"
              value={`+${s.cpi_peak_yoy}%`}
              sub="Food Away from Home"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
            <StatCard label="Cities" value={s.total_cities} sub="across 10 US states" />
            <StatCard label="Restaurants" value={(s.total_restaurants / 1000).toFixed(1) + 'K'} sub="from Yelp Open Dataset" />
            <StatCard label="Reviews" value={(s.total_reviews / 1000).toFixed(0) + 'K+'} sub={s.years_covered} />
          </div>
        </section>

        {/* ── Preview Chart ── */}
        <section>
          <h2 className="section-title">Price Concern Index vs CPI</h2>
          <p className="section-sub">
            % of reviews with negative price sentiment (left) alongside CPI for Food Away from Home (right).
            Both series rise sharply from 2021 — Pearson r = <span className="text-amber-400 font-bold">{s.pearson_r}</span>.
          </p>
          <div className="card p-4 sm:p-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={previewData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  tickLine={false}
                />
                <YAxis
                  yAxisId="pci"
                  orientation="left"
                  tick={{ fill: '#fbbf24', fontSize: 11 }}
                  tickLine={false}
                  tickFormatter={v => `${v}%`}
                  domain={[8, 42]}
                />
                <YAxis
                  yAxisId="cpi"
                  orientation="right"
                  tick={{ fill: '#60a5fa', fontSize: 11 }}
                  tickLine={false}
                  domain={[245, 340]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  formatter={v => <span style={{ color: '#94a3b8', fontSize: 12 }}>{v}</span>}
                />
                <Line
                  yAxisId="pci"
                  type="monotone"
                  dataKey="price_concern_index"
                  name="Price Concern Index (%)"
                  stroke="#fbbf24"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
                <Line
                  yAxisId="cpi"
                  type="monotone"
                  dataKey="cpi"
                  name="CPI (Food Away from Home)"
                  stroke="#60a5fa"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* ── Finding callout ── */}
        <section className="card border-amber-500/30 bg-amber-500/5">
          <p className="text-amber-400 font-semibold text-sm uppercase tracking-widest mb-2">Key Finding</p>
          <p className="text-white text-lg leading-relaxed">
            Price-complaint language in Yelp reviews rose from ~16% of reviews before 2020 to
            a peak of ~36% in mid-2022, closely tracking the 8.2% YoY spike in CPI for
            Food Away from Home. The Pearson correlation between the two monthly series is
            <span className="font-bold text-amber-400"> r = {s.pearson_r}</span> (p &lt; 0.001).
          </p>
        </section>

        {/* ── Feature Cards ── */}
        <section>
          <h2 className="section-title">Explore the Project</h2>
          <p className="section-sub">Four sections covering the full pipeline</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <FeatureCard
              href="/analysis"
              icon="📊"
              title="Analysis"
              desc="Interactive charts: PCI vs CPI, price tier distribution by city, correlation scatter, and top price phrases."
            />
            <FeatureCard
              href="/map"
              icon="🗺️"
              title="City Map"
              desc="Bubble map of all 12 cities. Size = restaurant count, colour = avg price tier. Click any city for a breakdown."
            />
            <FeatureCard
              href="/methodology"
              icon="🔬"
              title="Methodology"
              desc="SQL schema, NLP pipeline (VADER sentiment + keyword extraction), CPI data source, and statistical methods."
            />
          </div>
        </section>

        {/* ── Footer ── */}
        <footer className="border-t border-navy-700 pt-8 text-center text-xs text-slate-500 space-y-1">
          <p>
            Data: <a href="https://www.yelp.com/dataset" className="text-amber-400/70 hover:text-amber-400">Yelp Open Dataset</a>
            {' · '}
            <a href="https://fred.stlouisfed.org/series/CUSR0000SEFV" className="text-amber-400/70 hover:text-amber-400">FRED CUSR0000SEFV</a>
          </p>
          <p>Built by Aung Htet Khine · {new Date().getFullYear()}</p>
        </footer>
      </main>
    </>
  )
}
