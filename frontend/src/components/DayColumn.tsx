import type { ItineraryEvent } from '../types'
import { EventCard } from './EventCard'

interface Props {
  date: string
  events: ItineraryEvent[]
  onDeleteEvent?: (id: string) => void
  onAddEvent?: (date: string) => void
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function formatDate(dateStr: string) {
  const d = new Date(dateStr + 'T12:00:00')
  return `${DAYS[d.getDay()]}, ${MONTHS[d.getMonth()]} ${d.getDate()}`
}

export function DayColumn({ date, events, onDeleteEvent, onAddEvent }: Props) {
  const sorted = [...events].sort((a, b) => (a.time || '99:99').localeCompare(b.time || '99:99'))

  return (
    <div className="day-column">
      <div className="day-header">
        <span className="day-date">{formatDate(date)}</span>
        {onAddEvent && (
          <button className="day-add" onClick={() => onAddEvent(date)} title="Add event">+</button>
        )}
      </div>
      <div className="day-events">
        {sorted.map(e => (
          <EventCard key={e.id} event={e} onDelete={onDeleteEvent} />
        ))}
        {sorted.length === 0 && (
          <div className="day-empty">No events</div>
        )}
      </div>
    </div>
  )
}
