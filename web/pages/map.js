import Head from 'next/head'
import dynamic from 'next/dynamic'
import { useState } from 'react'
import Navbar from '../components/Navbar'
import cityData from '../public/data/city_stats.json'

// Leaflet requires the browser — disable SSR
const CityMap = dynamic(() => import('../components/CityMap'), { ssr: false })

const tierColor = (avg) => {
  if (avg < 1.7) return '#34d399'  // green  = mostly $
  if (avg < 1.9) return '#60a5fa'  // blue   = $$
  if (avg < 2.1) return '#f59e0b'  // amber  = $$ / $$$
  return '#f87171'                  // red    = higher tier
}

export default function MapPage() {
  const [selected, setSelected] = useState(null)

  return (
    <>
      <Head>
        <title>City Map — Restaurant Prices & Inflation</title>
      </Head>
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 py-12 space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">City Map</h1>
          <p className="text-slate-400">
            Bubble size = restaurant count · Colour = average price tier · Click any city for details
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Map */}
          <div className="lg:col-span-2 card p-0 overflow-hidden rounded-xl" style={{ height: 480 }}>
            <CityMap
              cities={cityData}
              selected={selected}
              onSelect={setSelected}
            />
          </div>

          {/* Side panel */}
          <div className="space-y-4">
            {/* Legend */}
            <div className="card">
              <p className="text-xs text-slate-400 uppercase tracking-widest mb-3">Avg Price Tier</p>
              {[
                { color: '#34d399', label: '< 1.7  (mostly $)' },
                { color: '#60a5fa', label: '1.7 – 1.9  ($$)' },
                { color: '#f59e0b', label: '1.9 – 2.1  ($$ / $$$)' },
                { color: '#f87171', label: '> 2.1  (higher)' },
              ].map(({ color, label }) => (
                <div key={label} className="flex items-center gap-2 mb-1.5">
                  <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: color }} />
                  <span className="text-xs text-slate-300">{label}</span>
                </div>
              ))}
            </div>

            {/* City detail card */}
            {selected ? (
              <div className="card space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-white">{selected.city}</h3>
                    <p className="text-xs text-slate-400">{selected.state}</p>
                  </div>
                  <button
                    onClick={() => setSelected(null)}
                    className="text-slate-500 hover:text-white text-xs"
                  >
                    ✕
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2 text-center">
                  {[
                    { label: 'Restaurants', value: selected.restaurant_count.toLocaleString() },
                    { label: 'Reviews',     value: (selected.total_reviews / 1000).toFixed(1) + 'K' },
                    { label: 'Avg Tier',    value: selected.avg_price_tier.toFixed(2) },
                    { label: 'Avg Stars',   value: selected.avg_stars.toFixed(2) },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-navy-600 rounded-lg p-2">
                      <p className="text-xs text-slate-400">{label}</p>
                      <p className="font-bold text-white text-sm">{value}</p>
                    </div>
                  ))}
                </div>

                <div>
                  <p className="text-xs text-slate-400 mb-2">Price tier mix</p>
                  {[
                    { tier: '$',    pct: selected.tier1_pct, color: '#34d399' },
                    { tier: '$$',   pct: selected.tier2_pct, color: '#60a5fa' },
                    { tier: '$$$',  pct: selected.tier3_pct, color: '#f59e0b' },
                    { tier: '$$$$', pct: selected.tier4_pct, color: '#f87171' },
                  ].map(({ tier, pct, color }) => (
                    <div key={tier} className="flex items-center gap-2 mb-1">
                      <span className="text-xs w-7 text-slate-300">{tier}</span>
                      <div className="flex-1 h-2 bg-navy-600 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${pct}%`, background: color }}
                        />
                      </div>
                      <span className="text-xs text-slate-400 w-8 text-right">{pct}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="card text-center text-slate-500 text-sm py-8">
                Click a city bubble on the map to see its stats
              </div>
            )}

            {/* City list */}
            <div className="card">
              <p className="text-xs text-slate-400 uppercase tracking-widest mb-3">All Cities</p>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {cityData.map(c => (
                  <button
                    key={c.city}
                    onClick={() => setSelected(c)}
                    className={`w-full flex items-center justify-between px-2 py-1.5 rounded text-xs transition-colors ${
                      selected?.city === c.city
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'hover:bg-navy-600 text-slate-300'
                    }`}
                  >
                    <span>{c.city}, {c.state}</span>
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: tierColor(c.avg_price_tier) }}
                    />
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
