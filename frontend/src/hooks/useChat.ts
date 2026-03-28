import { useState, useCallback } from 'react'
import type { Message, ToolCall } from '../types'

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  streamingText: string
}

export function useChat(tripId: string | null, onItineraryUpdate: () => void) {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isStreaming: false,
    streamingText: '',
  })

  const setMessages = useCallback((msgs: Message[]) => {
    setState(prev => ({ ...prev, messages: msgs }))
  }, [])

  const sendMessage = useCallback(async (text: string) => {
    if (!tripId || !text.trim()) return

    const userMsg: Message = {
      id: Date.now(),
      trip_id: tripId,
      role: 'user',
      content: text,
      tool_calls: null,
    }

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMsg],
      isStreaming: true,
      streamingText: '',
    }))

    const toolCalls: ToolCall[] = []
    let fullText = ''

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trip_id: tripId, message: text }),
      })

      const reader = resp.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let eventType = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))
            if (eventType === 'text') {
              fullText += data.content
              setState(prev => ({ ...prev, streamingText: fullText }))
            } else if (eventType === 'tool_use') {
              toolCalls.push({ tool: data.tool, input: data.input, result: {} })
            } else if (eventType === 'tool_result') {
              const last = toolCalls[toolCalls.length - 1]
              if (last) last.result = data.result
              setState(prev => ({
                ...prev,
                messages: [...prev.messages.filter(m => m.role !== 'assistant' || m.id !== -1), {
                  id: -1,
                  trip_id: tripId,
                  role: 'assistant',
                  content: fullText,
                  tool_calls: [...toolCalls],
                }],
              }))
            } else if (eventType === 'itinerary_update') {
              onItineraryUpdate()
            }
          }
        }
      }
    } catch (err) {
      fullText += '\n\n[Error communicating with server]'
    }

    const assistantMsg: Message = {
      id: Date.now() + 1,
      trip_id: tripId,
      role: 'assistant',
      content: fullText,
      tool_calls: toolCalls.length > 0 ? toolCalls : null,
    }

    setState(prev => ({
      ...prev,
      messages: [...prev.messages.filter(m => m.id !== -1), assistantMsg],
      isStreaming: false,
      streamingText: '',
    }))
  }, [tripId, onItineraryUpdate])

  return { ...state, sendMessage, setMessages }
}
