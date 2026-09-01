import asyncio
from typing import Dict, Any

# In-memory dictionary mapping session_id to an asyncio.Queue
_voice_event_queues: Dict[str, asyncio.Queue] = {}

def get_voice_queue(session_id: str) -> asyncio.Queue:
    """Returns the event queue for a given session, creating it if necessary."""
    if session_id not in _voice_event_queues:
        _voice_event_queues[session_id] = asyncio.Queue()
    return _voice_event_queues[session_id]

def cleanup_voice_queue(session_id: str):
    """Removes the event queue for a given session to prevent memory leaks."""
    if session_id in _voice_event_queues:
        del _voice_event_queues[session_id]

async def push_voice_event(session_id: str, event_type: str, data: Any = None):
    """
    Pushes an event asynchronously to the voice session's queue if it exists.
    The voice provider will listen to this queue and forward to Gemini.
    """
    if session_id in _voice_event_queues:
        queue = _voice_event_queues[session_id]
        await queue.put({"event_type": event_type, "data": data})
