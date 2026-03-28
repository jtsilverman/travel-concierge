import { useState, useCallback } from 'react'
import { useTrip } from './hooks/useTrip'
import { useChat } from './hooks/useChat'
import { ChatPanel } from './components/ChatPanel'
import { Itinerary } from './components/Itinerary'
import { TripSidebar } from './components/TripSidebar'
import { AddEventModal } from './components/AddEventModal'
import { ProfileSetup } from './components/ProfileSetup'
import './App.css'

function App() {
  const trip = useTrip()
  const [showProfile, setShowProfile] = useState(false)
  const [addEventDate, setAddEventDate] = useState<string | null>(null)

  const onItineraryUpdate = useCallback(() => {
    trip.refreshItinerary()
  }, [trip])

  const chatHook = useChat(trip.currentTrip?.id || null, onItineraryUpdate)

  const handleSelectTrip = async (tripId: string) => {
    await trip.fetchTrip(tripId)
    const tripData = await fetch(`/api/trips/${tripId}`).then(r => r.json())
    chatHook.setMessages(tripData.messages || [])
  }

  const handleCreateTrip = async (name: string, startDate: string, endDate: string) => {
    await trip.createTrip(name, startDate, endDate)
    chatHook.setMessages([])
  }

  const handleAddManualEvent = async (event: any) => {
    await trip.addEvent(event)
  }

  const handleAddFlight = async (flight: any) => {
    if (!trip.currentTrip) return
    await trip.addEvent({
      date: trip.currentTrip.start_date,
      time: flight.departure_time,
      title: `${flight.from_airport} to ${flight.to_airport} (${flight.airline})`,
      type: 'flight',
      source: 'ai',
      details: flight,
      notes: null,
      end_time: null,
    })
  }

  const handleAddHotel = async (hotel: any) => {
    if (!trip.currentTrip) return
    await trip.addEvent({
      date: trip.currentTrip.start_date,
      time: '15:00',
      title: hotel.name,
      type: 'hotel',
      source: 'ai',
      details: hotel,
      notes: null,
      end_time: null,
    })
  }

  const handleAddRestaurant = async (restaurant: any) => {
    if (!trip.currentTrip) return
    await trip.addEvent({
      date: trip.currentTrip.start_date,
      time: '19:00',
      title: restaurant.name,
      type: 'restaurant',
      source: 'ai',
      details: restaurant,
      notes: null,
      end_time: null,
    })
  }

  return (
    <div className="app">
      <TripSidebar
        trips={trip.trips}
        currentTrip={trip.currentTrip}
        onSelect={handleSelectTrip}
        onCreate={handleCreateTrip}
        onDelete={trip.deleteTrip}
        onOpenProfile={() => setShowProfile(true)}
      />
      <div className="main-content">
        <div className="chat-section">
          <ChatPanel
            messages={chatHook.messages}
            isStreaming={chatHook.isStreaming}
            streamingText={chatHook.streamingText}
            onSend={chatHook.sendMessage}
            onAddFlight={handleAddFlight}
            onAddHotel={handleAddHotel}
            onAddRestaurant={handleAddRestaurant}
            disabled={!trip.currentTrip}
          />
        </div>
        <div className="itinerary-section">
          <Itinerary
            trip={trip.currentTrip}
            onDeleteEvent={trip.deleteEvent}
            onAddEvent={(date) => setAddEventDate(date)}
          />
        </div>
      </div>

      {addEventDate && (
        <AddEventModal
          date={addEventDate}
          onAdd={handleAddManualEvent}
          onClose={() => setAddEventDate(null)}
        />
      )}

      {showProfile && (
        <ProfileSetup onClose={() => setShowProfile(false)} />
      )}
    </div>
  )
}

export default App
