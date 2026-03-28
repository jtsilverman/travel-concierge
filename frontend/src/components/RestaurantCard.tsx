import type { Restaurant } from '../types'

interface Props {
  restaurants: Restaurant[]
  onAdd?: (restaurant: Restaurant) => void
}

export function RestaurantCard({ restaurants, onAdd }: Props) {
  if (!restaurants.length) return null
  return (
    <div className="result-card restaurant-card">
      <h4>Restaurants</h4>
      <div className="restaurant-grid">
        {restaurants.slice(0, 5).map((r, i) => (
          <div key={i} className="restaurant-item">
            <div className="restaurant-info">
              <div className="restaurant-name">{r.name}</div>
              <div className="restaurant-meta">
                {r.cuisine} | {r.price_level} | {r.rating}/5 ({r.review_count} reviews)
              </div>
              <div className="restaurant-address">{r.address}</div>
              {onAdd && (
                <button className="add-btn" onClick={() => onAdd(r)}>Add to itinerary</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
