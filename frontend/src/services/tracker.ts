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

export async function trackEvent(
  eventType: EventType,
  payload?: Omit<TrackEventPayload, 'event_type' | 'session_id' | 'user_id'>
): Promise<void> {
  try {
    const body: TrackEventPayload = {
      event_type: eventType,
      session_id: getSessionId(),
      user_id: getUserId(),
      ...payload,
    };
    // Non-blocking — we don't await the response for critical path
    api.post('/events', body).catch(() => {
      // Silently swallow — event tracking must never break shopping
    });
  } catch {
    // Silently swallow any error
  }
}
