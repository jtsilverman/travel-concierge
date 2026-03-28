import type { Message } from '../types'
import { FlightCard } from './FlightCard'
import { HotelCard } from './HotelCard'
import { RestaurantCard } from './RestaurantCard'

interface Props {
  message: Message
  onAddFlight?: (flight: any) => void
  onAddHotel?: (hotel: any) => void
  onAddRestaurant?: (restaurant: any) => void
}

export function MessageBubble({ message, onAddFlight, onAddHotel, onAddRestaurant }: Props) {
  return (
    <div className={`message ${message.role}`}>
      <div className="message-role">{message.role === 'user' ? 'You' : 'Concierge'}</div>
      <div className="message-content">{message.content}</div>
      {message.tool_calls?.map((tc, i) => (
        <div key={i} className="tool-result">
          {tc.tool === 'search_flights' && tc.result?.flights && (
            <FlightCard flights={tc.result.flights} onAdd={onAddFlight} />
          )}
          {tc.tool === 'search_hotels' && tc.result?.hotels && (
            <HotelCard hotels={tc.result.hotels} onAdd={onAddHotel} />
          )}
          {tc.tool === 'search_restaurants' && tc.result?.restaurants && (
            <RestaurantCard restaurants={tc.result.restaurants} onAdd={onAddRestaurant} />
          )}
          {tc.tool === 'add_to_itinerary' && tc.result?.added && (
            <div className="itinerary-added">Added to itinerary: {tc.result.event?.title}</div>
          )}
        </div>
      ))}
    </div>
  )
}
