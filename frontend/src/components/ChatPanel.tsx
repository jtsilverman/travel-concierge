import { useState, useRef, useEffect } from 'react'
import type { Message } from '../types'
import { MessageBubble } from './MessageBubble'

interface Props {
  messages: Message[]
  isStreaming: boolean
  streamingText: string
  onSend: (text: string) => void
  onAddFlight?: (flight: any) => void
  onAddHotel?: (hotel: any) => void
  onAddRestaurant?: (restaurant: any) => void
  disabled?: boolean
}

export function ChatPanel({ messages, isStreaming, streamingText, onSend, onAddFlight, onAddHotel, onAddRestaurant, disabled }: Props) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming || disabled) return
    onSend(input.trim())
    setInput('')
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            Start planning your trip. Ask about flights, hotels, or restaurants.
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onAddFlight={onAddFlight}
            onAddHotel={onAddHotel}
            onAddRestaurant={onAddRestaurant}
          />
        ))}
        {isStreaming && streamingText && (
          <div className="message assistant">
            <div className="message-role">Concierge</div>
            <div className="message-content">{streamingText}<span className="cursor">|</span></div>
          </div>
        )}
        {isStreaming && !streamingText && (
          <div className="message assistant">
            <div className="message-role">Concierge</div>
            <div className="message-content thinking">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={disabled ? 'Create or select a trip first' : 'Ask about flights, hotels, restaurants...'}
          disabled={isStreaming || disabled}
        />
        <button type="submit" disabled={isStreaming || disabled || !input.trim()}>Send</button>
      </form>
    </div>
  )
}
