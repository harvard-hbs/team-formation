import { fetchEventSource } from '@microsoft/fetch-event-source'
import type {
  TeamAssignmentRequest,
  ProgressEvent,
  CompleteEvent,
  ErrorEvent
} from '@/types'

// Get API base URL from environment or default
const API_BASE_URL = (window as any).__API_BASE_URL__ || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Callbacks for SSE events
export interface AssignTeamsCallbacks {
  onProgress?: (event: ProgressEvent) => void
  onComplete?: (event: CompleteEvent) => void
  onError?: (event: ErrorEvent) => void
  onConnectionError?: (error: Error) => void
}

// AbortController for cancelling requests
let currentController: AbortController | null = null

/**
 * Call the /api/assign_teams endpoint with SSE streaming
 */
export async function assignTeams(
  request: TeamAssignmentRequest,
  callbacks: AssignTeamsCallbacks
): Promise<void> {
  // Cancel any existing request
  if (currentController) {
    currentController.abort()
  }

  currentController = new AbortController()

  try {
    await fetchEventSource(`${API_BASE_URL}/api/assign_teams`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: currentController.signal,

      // Handle incoming messages
      onmessage(event) {
        try {
          // Skip empty messages (keep-alive pings)
          if (!event.data || event.data.trim() === '') {
            return
          }

          // Debug logging - log raw event first
          console.log('SSE raw event:', {
            event: event.event,
            data: event.data,
            id: event.id
          })

          const data = JSON.parse(event.data)
          console.log('SSE parsed data:', data)

          // Route to appropriate callback based on event type
          // Handle both explicit event types and event_type in data
          const eventType = event.event || data.event_type

          if (eventType === 'progress' && callbacks.onProgress) {
            callbacks.onProgress(data as ProgressEvent)
          } else if (eventType === 'complete' && callbacks.onComplete) {
            callbacks.onComplete(data as CompleteEvent)
            // Connection will close automatically
          } else if (eventType === 'error' && callbacks.onError) {
            callbacks.onError(data as ErrorEvent)
          } else {
            console.warn('Unknown event type:', eventType, data)
          }
        } catch (error) {
          console.error('Failed to parse SSE message:', error, 'Raw event:', {
            event: event.event,
            data: event.data,
            id: event.id
          })
          if (callbacks.onConnectionError) {
            callbacks.onConnectionError(new Error('Failed to parse server message'))
          }
        }
      },

      // Handle errors
      onerror(error) {
        console.error('SSE connection error:', error)

        // Check if this is just a normal connection close (not an actual error)
        // The fetch-event-source library sometimes reports normal closes as errors
        if (error && typeof error === 'object' && 'message' in error) {
          const message = String(error.message)
          // Ignore normal connection closure
          if (message.includes('aborted') || message.includes('closed')) {
            console.log('SSE connection closed normally')
            return
          }
        }

        if (callbacks.onConnectionError) {
          // Provide user-friendly error message
          const userError = new Error('Cannot reach team formation service')
          callbacks.onConnectionError(userError)
        }
        // Stop retrying by throwing
        throw error
      },

      // Don't retry on error - let the user initiate retry
      openWhenHidden: true
    })
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.log('Request cancelled')
    } else {
      console.error('Request failed:', error)
      // Transform "Failed to fetch" into a user-friendly message
      if (error instanceof Error && error.message.includes('Failed to fetch')) {
        throw new Error('Cannot reach team formation service')
      }
      throw error
    }
  } finally {
    currentController = null
  }
}

/**
 * Cancel the current streaming request
 */
export function cancelAssignment(): void {
  if (currentController) {
    currentController.abort()
    currentController = null
  }
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    return response.ok
  } catch (error) {
    console.error('Health check failed:', error)
    return false
  }
}

/**
 * Get API info
 */
export async function getApiInfo(): Promise<any> {
  try {
    const response = await fetch(`${API_BASE_URL}/api`)
    if (!response.ok) {
      throw new Error('Failed to get API info')
    }
    return await response.json()
  } catch (error) {
    console.error('Failed to get API info:', error)
    throw error
  }
}
