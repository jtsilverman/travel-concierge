import { useState } from 'react'

interface Props {
  date: string
  onAdd: (event: { date: string; title: string; type: string; time: string | null; notes: string | null; source: string }) => void
  onClose: () => void
}

export function AddEventModal({ date, onAdd, onClose }: Props) {
  const [title, setTitle] = useState('')
  const [time, setTime] = useState('')
  const [type, setType] = useState('custom')
  const [notes, setNotes] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    onAdd({
      date,
      title: title.trim(),
      type,
      time: time || null,
      notes: notes || null,
      source: 'manual',
    })
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h3>Add Event - {date}</h3>
        <form onSubmit={handleSubmit}>
          <label>
            Title
            <input type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="Brunch with family" autoFocus />
          </label>
          <label>
            Time (optional)
            <input type="time" value={time} onChange={e => setTime(e.target.value)} />
          </label>
          <label>
            Type
            <select value={type} onChange={e => setType(e.target.value)}>
              <option value="custom">Custom</option>
              <option value="activity">Activity</option>
              <option value="restaurant">Restaurant</option>
              <option value="flight">Flight</option>
              <option value="hotel">Hotel</option>
            </select>
          </label>
          <label>
            Notes (optional)
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} />
          </label>
          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={!title.trim()}>Add</button>
          </div>
        </form>
      </div>
    </div>
  )
}
