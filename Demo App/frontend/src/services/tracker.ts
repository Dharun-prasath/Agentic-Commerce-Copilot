/**
 * Event tracker — fire-and-forget.
 * Event failures NEVER block shopping operations.
 * Sends events to the backend which stores them for Copilot consumption.
 */
import api, { getSessionId } from './api';
import type { EventType, TrackEventPayload } from '@/types';

// Get current user id from localStorage if available
function getUserId(): string | undefined {
  try {
    const user = localStorage.getItem('user');
    if (user) return JSON.parse(user).id;
  } catch {
    // ignore
  }
  return undefined;
}

// Get current user name from localStorage if available
function getUserName(): string | undefined {
  try {
    const user = localStorage.getItem('user');
    if (user) return JSON.parse(user).name;
  } catch {
    // ignore
  }
  return undefined;
}

export async function trackEvent(
  eventType: EventType,
  payload?: Omit<TrackEventPayload, 'event_type' | 'session_id' | 'user_id'>
): Promise<void> {
  const userId = getUserId();
  if (!userId) return; // Do not track anonymous sessions

  try {
    const event_metadata = payload?.event_metadata || {};
    const uName = getUserName();
    if (uName) {
      event_metadata.user_name = uName;
    }

    const body: TrackEventPayload = {
      event_type: eventType,
      session_id: getSessionId(),
      user_id: getUserId(),
      ...payload,
      event_metadata,
    };
    // Non-blocking — send event to Agentic Copilot
    fetch('http://localhost:8000/api/v1/integration/events', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    }).catch(() => {
      // Silently swallow — event tracking must never break shopping
    });
  } catch {
    // Silently swallow any error
  }
}

export function terminateSession(explicitSessionId?: string) {
  try {
    const sessionId = explicitSessionId || getSessionId();
    if (sessionId) {
      const url = `http://localhost:8000/api/v1/integration/events/terminate/${sessionId}`;
      if (navigator.sendBeacon) {
          navigator.sendBeacon(url);
      } else {
          fetch(url, { method: 'POST', keepalive: true }).catch(() => {});
      }
    }
  } catch {
    // Ignore
  }
}

// Attach listener to terminate session when tab is closed
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    terminateSession();
  });
}
