import type { Hotel } from '../types'

interface Props {
  hotels: Hotel[]
  onAdd?: (hotel: Hotel) => void
}

export function HotelCard({ hotels, onAdd }: Props) {
  if (!hotels.length) return null
  return (
    <div className="result-card hotel-card">
      <h4>Hotels</h4>
      <div className="hotel-grid">
        {hotels.slice(0, 4).map((h, i) => (
          <div key={i} className="hotel-item">
            {h.photo_url && <img src={h.photo_url} alt={h.name} className="hotel-photo" />}
            <div className="hotel-info">
              <div className="hotel-name">{h.name}</div>
              <div className="hotel-meta">
                {'*'.repeat(h.stars)} | {h.rating}/5
              </div>
              <div className="hotel-price">${h.price_per_night}/night</div>
              <div className="hotel-amenities">
                {h.amenities.slice(0, 4).map((a, j) => (
                  <span key={j} className="amenity-pill">{a}</span>
                ))}
              </div>
              {onAdd && (
                <button className="add-btn" onClick={() => onAdd(h)}>Add to itinerary</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
