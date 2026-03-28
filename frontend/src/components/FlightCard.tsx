import type { Flight } from '../types'

interface Props {
  flights: Flight[]
  onAdd?: (flight: Flight) => void
}

export function FlightCard({ flights, onAdd }: Props) {
  if (!flights.length) return null
  return (
    <div className="result-card flight-card">
      <h4>Flights</h4>
      <table>
        <thead>
          <tr>
            <th>Airline</th>
            <th>Depart</th>
            <th>Arrive</th>
            <th>Duration</th>
            <th>Stops</th>
            <th>Price</th>
            {onAdd && <th></th>}
          </tr>
        </thead>
        <tbody>
          {flights.slice(0, 5).map((f, i) => (
            <tr key={i}>
              <td>{f.airline} {f.flight_no}</td>
              <td>{f.departure_time}</td>
              <td>{f.arrival_time}</td>
              <td>{f.duration}</td>
              <td>{f.stops === 0 ? 'Nonstop' : `${f.stops} stop`}</td>
              <td className="price">${f.price}</td>
              {onAdd && (
                <td>
                  <button className="add-btn" onClick={() => onAdd(f)}>+</button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
