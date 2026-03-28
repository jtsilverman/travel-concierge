import { useState, useCallback, useEffect } from 'react'
import type { Trip, ItineraryEvent } from '../types'

export function useTrip() {
  const [trips, setTrips] = useState<Trip[]>([])
  const [currentTrip, setCurrentTrip] = useState<Trip | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchTrips = useCallback(async () => {
    const resp = await fetch('/api/trips')
    const data = await resp.json()
    setTrips(data)
  }, [])

  const fetchTrip = useCallback(async (tripId: string) => {
    setLoading(true)
    const resp = await fetch(`/api/trips/${tripId}`)
    const data = await resp.json()
    setCurrentTrip(data)
    setLoading(false)
  }, [])

  const createTrip = useCallback(async (name: string, startDate: string, endDate: string) => {
    const resp = await fetch('/api/trips', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, start_date: startDate, end_date: endDate }),
    })
    const trip = await resp.json()
    await fetchTrips()
    await fetchTrip(trip.id)
    return trip
  }, [fetchTrips, fetchTrip])

  const deleteTrip = useCallback(async (tripId: string) => {
    await fetch(`/api/trips/${tripId}`, { method: 'DELETE' })
    if (currentTrip?.id === tripId) setCurrentTrip(null)
    await fetchTrips()
  }, [currentTrip, fetchTrips])

  const addEvent = useCallback(async (event: Omit<ItineraryEvent, 'id' | 'trip_id' | 'sort_order'>) => {
    if (!currentTrip) return
    await fetch(`/api/trips/${currentTrip.id}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event),
    })
    await fetchTrip(currentTrip.id)
  }, [currentTrip, fetchTrip])

  const deleteEvent = useCallback(async (eventId: string) => {
    if (!currentTrip) return
    await fetch(`/api/trips/${currentTrip.id}/events/${eventId}`, { method: 'DELETE' })
    await fetchTrip(currentTrip.id)
  }, [currentTrip, fetchTrip])

  const refreshItinerary = useCallback(async () => {
    if (currentTrip) await fetchTrip(currentTrip.id)
  }, [currentTrip, fetchTrip])

  useEffect(() => { fetchTrips() }, [fetchTrips])

  return {
    trips, currentTrip, loading,
    fetchTrip, createTrip, deleteTrip,
    addEvent, deleteEvent, refreshItinerary,
  }
}
