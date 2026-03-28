export interface Trip {
  id: string
  name: string
  start_date: string
  end_date: string
  created_at?: string
  events?: ItineraryEvent[]
  messages?: Message[]
}

export interface ItineraryEvent {
  id: string
  trip_id: string
  date: string
  time: string | null
  end_time: string | null
  title: string
  type: 'flight' | 'hotel' | 'restaurant' | 'activity' | 'custom'
  source: 'ai' | 'manual'
  details: Record<string, any> | null
  notes: string | null
  sort_order: number
}

export interface Message {
  id: number
  trip_id: string
  role: 'user' | 'assistant'
  content: string
  tool_calls: ToolCall[] | null
  created_at?: string
}

export interface ToolCall {
  tool: string
  input: Record<string, any>
  result: Record<string, any>
}

export interface Flight {
  rank: number
  airline: string
  flight_no: string
  price: number
  departure_time: string
  arrival_time: string
  duration: string
  stops: number
  from_airport: string
  to_airport: string
  booking_url: string
}

export interface Hotel {
  rank: number
  name: string
  price_per_night: number
  total_price: string
  rating: number
  stars: number
  photo_url: string
  amenities: string[]
  check_in: string
  check_out: string
}

export interface Restaurant {
  rank: number
  name: string
  address: string
  rating: number
  review_count: number
  price_level: string
  cuisine: string
  website: string
  maps_url: string
}

export interface CostData {
  by_service: { service: string; total: number; calls: number }[]
  total_usd: number
}

export interface Profile {
  home_airport: string
  loyalty_programs: string[]
  preferences: Record<string, any>
}

export interface SSEEvent {
  event: 'text' | 'tool_use' | 'tool_result' | 'itinerary_update' | 'done'
  data: any
}
