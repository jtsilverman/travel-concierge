import { useState, useEffect } from 'react'
import type { Profile } from '../types'

interface Props {
  onClose: () => void
}

const LOYALTY_OPTIONS = [
  'Amex Membership Rewards',
  'Delta SkyMiles',
  'United MileagePlus',
  'American AAdvantage',
  'Marriott Bonvoy',
  'Hilton Honors',
  'Hyatt World of Hyatt',
  'IHG One Rewards',
  'Southwest Rapid Rewards',
  'Chase Ultimate Rewards',
]

export function ProfileSetup({ onClose }: Props) {
  const [profile, setProfile] = useState<Profile>({
    home_airport: 'ORD',
    loyalty_programs: [],
    preferences: {},
  })

  useEffect(() => {
    fetch('/api/profile').then(r => r.json()).then(setProfile)
  }, [])

  const toggleProgram = (program: string) => {
    setProfile(prev => ({
      ...prev,
      loyalty_programs: prev.loyalty_programs.includes(program)
        ? prev.loyalty_programs.filter(p => p !== program)
        : [...prev.loyalty_programs, program],
    }))
  }

  const handleSave = async () => {
    await fetch('/api/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal profile-modal" onClick={e => e.stopPropagation()}>
        <h3>Traveler Profile</h3>
        <label>
          Home Airport
          <input
            type="text"
            value={profile.home_airport}
            onChange={e => setProfile(prev => ({ ...prev, home_airport: e.target.value.toUpperCase() }))}
            placeholder="ORD"
            maxLength={4}
          />
        </label>
        <div className="loyalty-section">
          <label>Loyalty Programs</label>
          <div className="loyalty-grid">
            {LOYALTY_OPTIONS.map(p => (
              <label key={p} className="loyalty-item">
                <input
                  type="checkbox"
                  checked={profile.loyalty_programs.includes(p)}
                  onChange={() => toggleProgram(p)}
                />
                {p}
              </label>
            ))}
          </div>
        </div>
        <div className="modal-actions">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSave}>Save</button>
        </div>
      </div>
    </div>
  )
}
