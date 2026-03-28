import type { ItineraryEvent } from '../types'

const TYPE_ICONS: Record<string, string> = {
  flight: '\u2708\uFE0F',
  hotel: '\uD83C\uDFE8',
  restaurant: '\uD83C\uDF7D\uFE0F',
  activity: '\u2B50',
  custom: '\uD83D\uDCC5',
}

interface Props {
  event: ItineraryEvent
  onDelete?: (id: string) => void
}

export function EventCard({ event, onDelete }: Props) {
  const icon = TYPE_ICONS[event.type] || TYPE_ICONS.custom
  const price = event.details?.price || event.details?.price_per_night

  return (
    <div className={`event-card ${event.source === 'ai' ? 'ai-sourced' : 'manual-sourced'}`}>
      <div className="event-icon">{icon}</div>
      <div className="event-body">
        <div className="event-title">{event.title}</div>
        <div className="event-meta">
          {event.time && <span className="event-time">{event.time}</span>}
          {price && <span className="event-price">${price}</span>}
          {event.notes && <span className="event-notes">{event.notes}</span>}
        </div>
      </div>
      {onDelete && (
        <button className="event-delete" onClick={() => onDelete(event.id)} title="Remove">x</button>
      )}
    </div>
  )
}
