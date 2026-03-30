import { useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'

// Tile layer — CartoDB Dark Matter (no API key required)
const TILE_URL = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
const TILE_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'

const tierColor = (avg) => {
  if (avg < 1.7) return '#34d399'
  if (avg < 1.9) return '#60a5fa'
  if (avg < 2.1) return '#f59e0b'
  return '#f87171'
}

const scale = (count, min, max) => {
  const norm = (count - min) / (max - min)
  return 10 + norm * 30  // radius 10–40
}

function FlyTo({ city }) {
  const map = useMap()
  useEffect(() => {
    if (city) map.flyTo([city.lat, city.lon], 9, { duration: 1 })
  }, [city, map])
  return null
}

export default function CityMap({ cities, selected, onSelect }) {
  const counts = cities.map(c => c.restaurant_count)
  const minC   = Math.min(...counts)
  const maxC   = Math.max(...counts)

  return (
    <MapContainer
      center={[37.5, -95]}
      zoom={4}
      style={{ width: '100%', height: '100%', background: '#0f172a' }}
      scrollWheelZoom={true}
    >
      <TileLayer url={TILE_URL} attribution={TILE_ATTR} />

      {selected && <FlyTo city={selected} />}

      {cities.map(city => (
        <CircleMarker
          key={city.city}
          center={[city.lat, city.lon]}
          radius={scale(city.restaurant_count, minC, maxC)}
          pathOptions={{
            fillColor: tierColor(city.avg_price_tier),
            fillOpacity: selected?.city === city.city ? 0.95 : 0.65,
            color: selected?.city === city.city ? '#fff' : tierColor(city.avg_price_tier),
            weight: selected?.city === city.city ? 2 : 0.5,
          }}
          eventHandlers={{ click: () => onSelect(city) }}
        >
          <Popup>
            <div style={{ fontFamily: 'system-ui', fontSize: 12, color: '#e2e8f0', minWidth: 140 }}>
              <strong style={{ fontSize: 13 }}>{city.city}, {city.state}</strong>
              <br />
              Restaurants: {city.restaurant_count.toLocaleString()}
              <br />
              Avg tier: {city.avg_price_tier.toFixed(2)}
              <br />
              Reviews: {(city.total_reviews / 1000).toFixed(1)}K
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
