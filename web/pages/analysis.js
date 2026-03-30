import Head from 'next/head'
import { useState } from 'react'
import Navbar from '../components/Navbar'
import {
  LineChart, Line, BarChart, Bar, ScatterChart, Scatter,
  XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'

import seriesData  from '../public/data/sentiment_cpi.json'
import tiersData   from '../public/data/price_tiers.json'
import scatterData from '../public/data/scatter.json'
import phrasesData from '../public/data/phrases.json'
import summary     from '../public/data/summary.json'

const TABS = ['PCI vs CPI', 'Price Tiers', 'Correlation', 'Price Phrases']

const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-navy-700 border border-navy-600 rounded-lg p-3 text-xs min-w-[160px]">
      <p className="text-slate-300 font-medium mb-1.5">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }} className="flex justify-between gap-3">
          <span>{p.name}</span>
          <span className="font-bold">
            {typeof p.value === 'number' ? p.value.toFixed(2) : p.value}
          </span>
        </p>
      ))}
    </div>
  )
}

// ── Tab 1: PCI vs CPI over time ───────────────────────────────────────────────
function PCIChart() {
  const [showYoY, setShowYoY] = useState(false)

  const data = seriesData.filter(d => d.month % 2 === 1) // every other month for clarity

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h3 className="text-white font-semibold">Price Concern Index vs CPI</h3>
          <p className="text-slate-400 text-sm">Monthly series 2015–2023</p>
        </div>
        <button
          onClick={() => setShowYoY(v => !v)}
          className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
            showYoY
              ? 'bg-amber-500/20 border-amber-500/40 text-amber-400'
              : 'border-navy-600 text-slate-400 hover:border-slate-500'
          }`}
        >
          {showYoY ? 'YoY CPI %' : 'CPI Level'} ↕
        </button>
      </div>

      <div className="card p-4">
        <ResponsiveContainer width="100%" height={380}>
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              tickLine={false}
              interval={5}
            />
            <YAxis
              yAxisId="pci"
              orientation="left"
              tick={{ fill: '#fbbf24', fontSize: 11 }}
              tickLine={false}
              tickFormatter={v => `${v}%`}
              domain={[8, 42]}
              label={{ value: 'Price Concern Index (%)', angle: -90, position: 'insideLeft', fill: '#fbbf24', fontSize: 11, dx: -4 }}
            />
            <YAxis
              yAxisId="cpi"
              orientation="right"
              tick={{ fill: '#60a5fa', fontSize: 11 }}
              tickLine={false}
              tickFormatter={v => showYoY ? `${v}%` : v}
              domain={showYoY ? [-1, 10] : [245, 340]}
            />
            <Tooltip content={<ChartTooltip />} />
            <Legend
              formatter={v => <span style={{ color: '#94a3b8', fontSize: 11 }}>{v}</span>}
            />
            <ReferenceLine yAxisId="pci" x="2020-03" stroke="#ef4444" strokeDasharray="4 4"
              label={{ value: 'COVID', fill: '#ef4444', fontSize: 10, dy: -8 }} />
            <ReferenceLine yAxisId="pci" x="2021-03" stroke="#f97316" strokeDasharray="4 4"
              label={{ value: 'Inflation', fill: '#f97316', fontSize: 10, dy: -8 }} />
            <Line
              yAxisId="pci"
              type="monotone"
              dataKey="price_concern_index"
              name="Price Concern Index (%)"
              stroke="#fbbf24"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0 }}
            />
            <Line
              yAxisId="cpi"
              type="monotone"
              dataKey={showYoY ? 'cpi_yoy_pct' : 'cpi'}
              name={showYoY ? 'CPI YoY (%)' : 'CPI Level'}
              stroke="#60a5fa"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Pearson r',   value: summary.pearson_r,      color: 'text-amber-400' },
          { label: 'Reg. R²',     value: summary.regression_r2,  color: 'text-amber-400' },
          { label: 'PCI pre-2020',value: `${summary.pci_avg_pre2020}%`, color: 'text-slate-300' },
          { label: 'PCI 2022',    value: `${summary.pci_avg_2022}%`,    color: 'text-red-400' },
        ].map(m => (
          <div key={m.label} className="bg-navy-700 rounded-lg p-3 text-center">
            <p className="text-xs text-slate-500">{m.label}</p>
            <p className={`text-xl font-bold ${m.color}`}>{m.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Tab 2: Price tier distribution by city ────────────────────────────────────
function TierChart() {
  const data = tiersData.cities.map((city, i) => ({
    city: city.replace('Saint ', 'St. '),
    '$':    tiersData.tier1[i],
    '$$':   tiersData.tier2[i],
    '$$$':  tiersData.tier3[i],
    '$$$$': tiersData.tier4[i],
  }))

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-white font-semibold">Price Tier Distribution by City</h3>
        <p className="text-slate-400 text-sm">Restaurant counts by Yelp price tier ($–$$$$)</p>
      </div>
      <div className="card p-4">
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="city"
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              tickLine={false}
              angle={-35}
              textAnchor="end"
              interval={0}
            />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickLine={false} />
            <Tooltip content={<ChartTooltip />} cursor={{ fill: '#334155' }} />
            <Legend
              formatter={v => <span style={{ color: '#94a3b8', fontSize: 11 }}>{v}</span>}
            />
            <Bar dataKey="$"    stackId="a" fill="#34d399" radius={[0,0,0,0]} />
            <Bar dataKey="$$"   stackId="a" fill="#60a5fa" />
            <Bar dataKey="$$$"  stackId="a" fill="#f59e0b" />
            <Bar dataKey="$$$$" stackId="a" fill="#f87171" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-slate-500">
        Las Vegas and New Orleans skew toward higher price tiers, while Tucson and Indianapolis are predominantly budget ($ / $$) markets.
      </p>
    </div>
  )
}

// ── Tab 3: Correlation scatter ────────────────────────────────────────────────
function CorrelationChart() {
  const data = scatterData.map(d => ({
    ...d,
    era: d.year < 2020 ? 'Pre-2020' : d.year <= 2020 ? 'COVID-2020' : d.year === 2021 ? '2021' : '2022+',
  }))

  const pre2020 = data.filter(d => d.era === 'Pre-2020')
  const covid   = data.filter(d => d.era === 'COVID-2020')
  const y2021   = data.filter(d => d.era === '2021')
  const y2022p  = data.filter(d => d.era === '2022+')

  const groups = [
    { data: pre2020, fill: '#60a5fa', name: 'Pre-2020' },
    { data: covid,   fill: '#a78bfa', name: 'COVID-2020' },
    { data: y2021,   fill: '#f59e0b', name: '2021' },
    { data: y2022p,  fill: '#f87171', name: '2022+' },
  ]

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-white font-semibold">Correlation: PCI vs CPI Level</h3>
        <p className="text-slate-400 text-sm">Each dot = one month. Pearson r = {summary.pearson_r}</p>
      </div>
      <div className="card p-4">
        <ResponsiveContainer width="100%" height={380}>
          <ScatterChart margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              type="number"
              dataKey="cpi"
              name="CPI (Food Away from Home)"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={false}
              label={{ value: 'CPI (Food Away from Home)', position: 'insideBottom', fill: '#60a5fa', fontSize: 11, dy: 12 }}
              domain={[248, 335]}
            />
            <YAxis
              type="number"
              dataKey="price_concern_index"
              name="Price Concern Index (%)"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={false}
              tickFormatter={v => `${v}%`}
              label={{ value: 'PCI (%)', angle: -90, position: 'insideLeft', fill: '#fbbf24', fontSize: 11, dx: -4 }}
            />
            <ZAxis range={[30, 30]} />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const d = payload[0].payload
                return (
                  <div className="bg-navy-700 border border-navy-600 rounded-lg p-3 text-xs">
                    <p className="text-slate-300 font-medium">{d.date}</p>
                    <p className="text-amber-400">PCI: {d.price_concern_index}%</p>
                    <p className="text-blue-400">CPI: {d.cpi}</p>
                  </div>
                )
              }}
            />
            <Legend formatter={v => <span style={{ color: '#94a3b8', fontSize: 11 }}>{v}</span>} />
            {groups.map(g => (
              <Scatter
                key={g.name}
                name={g.name}
                data={g.data}
                fill={g.fill}
                fillOpacity={0.8}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="card bg-amber-500/5 border-amber-500/20 text-sm text-slate-300">
        <strong className="text-amber-400">Interpretation:</strong> The strong positive trend
        (r = {summary.pearson_r}, R² = {summary.regression_r2}) shows that higher CPI levels
        consistently predict more price complaints. The 2022+ cluster (red) sits distinctly
        higher than pre-2020 observations (blue) at any given CPI level.
      </div>
    </div>
  )
}

// ── Tab 4: Top price phrases ──────────────────────────────────────────────────
function PhrasesChart() {
  const data = [...phrasesData].sort((a, b) => b.count - a.count)
  const max  = data[0]?.count || 1

  const isNeg = p => ['expensive', 'pricey', 'overpriced', 'rip-off', 'not worth',
    'too expensive', 'prices have gone up', 'price hike'].includes(p)

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-white font-semibold">Top Price-Related Phrases in Reviews</h3>
        <p className="text-slate-400 text-sm">Extracted via keyword matching across all reviews</p>
      </div>
      <div className="card space-y-3">
        {data.map(({ phrase, count }) => {
          const pct  = (count / max * 100).toFixed(0)
          const neg  = isNeg(phrase)
          return (
            <div key={phrase}>
              <div className="flex justify-between text-xs mb-1">
                <span className={neg ? 'text-red-400' : 'text-emerald-400'}>
                  {neg ? '↑' : '↓'} "{phrase}"
                </span>
                <span className="text-slate-400">{count.toLocaleString()}</span>
              </div>
              <div className="h-2 bg-navy-600 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${neg ? 'bg-red-500' : 'bg-emerald-500'}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
      <p className="text-xs text-slate-500">
        Red = negative price sentiment (concern) · Green = positive price sentiment (value)
      </p>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Analysis() {
  const [tab, setTab] = useState(0)

  const panels = [<PCIChart key={0} />, <TierChart key={1} />, <CorrelationChart key={2} />, <PhrasesChart key={3} />]

  return (
    <>
      <Head>
        <title>Analysis — Restaurant Prices & Inflation</title>
      </Head>
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-1">Analysis</h1>
          <p className="text-slate-400">Four views across the full dataset</p>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-1 border-b border-navy-700 mb-8 overflow-x-auto">
          {TABS.map((label, i) => (
            <button
              key={label}
              onClick={() => setTab(i)}
              className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors -mb-px ${
                tab === i
                  ? 'border-amber-400 text-amber-400'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {panels[tab]}
      </main>
    </>
  )
}
