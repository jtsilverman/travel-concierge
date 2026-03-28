import type { Trip } from '../types'
import { DayColumn } from './DayColumn'

interface Props {
  trip: Trip | null
  onDeleteEvent?: (id: string) => void
  onAddEvent?: (date: string) => void
}

function getDatesInRange(start: string, end: string): string[] {
  const dates: string[] = []
  const current = new Date(start + 'T12:00:00')
  const last = new Date(end + 'T12:00:00')
  while (current <= last) {
    dates.push(current.toISOString().split('T')[0])
    current.setDate(current.getDate() + 1)
  }
  return dates
}

export function Itinerary({ trip, onDeleteEvent, onAddEvent }: Props) {
  if (!trip) {
    return (
      <div className="itinerary empty-state">
        <h3>No trip selected</h3>
        <p>Create or select a trip to see the itinerary.</p>
      </div>
    )
  }

  const dates = getDatesInRange(trip.start_date, trip.end_date)
  const events = trip.events || []

  return (
    <div className="itinerary">
      <div className="itinerary-header">
        <h3>{trip.name}</h3>
        <span className="itinerary-dates">{trip.start_date} to {trip.end_date}</span>
      </div>
      <div className="itinerary-days">
        {dates.map(date => (
          <DayColumn
            key={date}
            date={date}
            events={events.filter(e => e.date === date)}
            onDeleteEvent={onDeleteEvent}
            onAddEvent={onAddEvent}
          />
        ))}
      </div>
    </div>
  )
}
