import { useState } from 'react'
import type { Trip, CostData } from '../types'

interface Props {
  trips: Trip[]
  currentTrip: Trip | null
  onSelect: (tripId: string) => void
  onCreate: (name: string, startDate: string, endDate: string) => void
  onDelete: (tripId: string) => void
  onOpenProfile: () => void
}

export function TripSidebar({ trips, currentTrip, onSelect, onCreate, onDelete, onOpenProfile }: Props) {
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [costs, setCosts] = useState<CostData | null>(null)

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !startDate || !endDate) return
    onCreate(name, startDate, endDate)
    setName('')
    setStartDate('')
    setEndDate('')
    setShowCreate(false)
  }

  const loadCosts = async () => {
    if (!currentTrip) return
    const resp = await fetch(`/api/costs?trip_id=${currentTrip.id}`)
    setCosts(await resp.json())
  }

  return (
    <div className="trip-sidebar">
      <div className="sidebar-header">
        <h2>Trips</h2>
        <div className="sidebar-actions">
          <button onClick={() => setShowCreate(!showCreate)} title="New trip">+</button>
          <button onClick={onOpenProfile} title="Profile">P</button>
        </div>
      </div>

      {showCreate && (
        <form className="create-trip-form" onSubmit={handleCreate}>
          <input type="text" placeholder="Trip name" value={name} onChange={e => setName(e.target.value)} />
          <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} />
          <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} />
          <button type="submit" disabled={!name || !startDate || !endDate}>Create</button>
        </form>
      )}

      <div className="trip-list">
        {trips.map(t => (
          <div
            key={t.id}
            className={`trip-item ${currentTrip?.id === t.id ? 'active' : ''}`}
            onClick={() => onSelect(t.id)}
          >
            <div className="trip-name">{t.name}</div>
            <div className="trip-dates">{t.start_date} to {t.end_date}</div>
            <button className="trip-delete" onClick={e => { e.stopPropagation(); onDelete(t.id) }} title="Delete">x</button>
          </div>
        ))}
        {trips.length === 0 && (
          <div className="no-trips">No trips yet. Create one to start planning.</div>
        )}
      </div>

      {currentTrip && (
        <div className="cost-section">
          <button className="cost-toggle" onClick={loadCosts}>Show API Costs</button>
          {costs && (
            <div className="cost-details">
              <div className="cost-total">Total: ${costs.total_usd.toFixed(4)}</div>
              {costs.by_service.map((s, i) => (
                <div key={i} className="cost-row">
                  {s.service}: ${s.total.toFixed(4)} ({s.calls} calls)
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
