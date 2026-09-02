import uuid
import time
import traceback
import asyncio
import logging
from typing import Any, Dict, List
from contextlib import asynccontextmanager
from app.core.database import async_session_maker
from app.models.models import ExecutionTrace

logger = logging.getLogger(__name__)

def mask_secrets(d):
    if isinstance(d, dict):
        res = {}
        for k, v in d.items():
            if any(secret in k.lower() for secret in ["authorization", "password", "token", "api_key", "secret"]):
                res[k] = "********"
            else:
                res[k] = mask_secrets(v)
        return res
    elif isinstance(d, list):
        return [mask_secrets(i) for i in d]
    return d

class TelemetryTracker:
    def __init__(self, component_id: str, component_type: str, session_id: str):
        self.trace_id = str(uuid.uuid4())
        self.session_id = session_id
        self.component_id = component_id
        self.component_type = component_type
        
        self.inputs = {}
        self.outputs = {}
        self.events = []
        self.tool_calls = []
        self.error_details = None
        self.status = "RUNNING"
        self.start_time = time.time()
        self.end_time = None
        
    def set_input(self, data: Any):
        # Handle Pydantic models
        if hasattr(data, "model_dump"):
            self.inputs = data.model_dump()
        else:
            self.inputs = data
        
    def set_output(self, data: Any):
        if hasattr(data, "model_dump"):
            self.outputs = data.model_dump()
        else:
            self.outputs = data
        
    def add_event(self, event_name: str, description: str = ""):
        self.events.append({
            "timestamp": time.time(),
            "event": event_name,
            "description": description
        })
        
    def add_tool_call(self, tool_name: str, function: str, args: Any, start: float, end: float, status: str, result: Any = None, error: str = None):
        self.tool_calls.append({
            "tool_name": tool_name,
            "function": function,
            "args": args,
            "start": start,
            "end": end,
            "duration_ms": (end - start) * 1000,
            "status": status,
            "result": result,
            "error": error
        })
        
    def set_error(self, error: Exception):
        self.status = "FAILED"
        self.error_details = {
            "error_type": type(error).__name__,
            "message": str(error),
            "stack_trace": traceback.format_exc()
        }

    async def save(self):
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        if self.status == "RUNNING":
            self.status = "SUCCESS"
            
        try:
            async with async_session_maker() as db:
                from sqlalchemy.future import select
                res = await db.execute(select(ExecutionTrace).where(ExecutionTrace.id == self.trace_id))
                existing = res.scalar_one_or_none()
                
                if existing:
                    existing.status = self.status
                    existing.end_time = self.end_time
                    existing.duration_ms = duration_ms
                    existing.inputs = mask_secrets(self.inputs)
                    existing.outputs = mask_secrets(self.outputs)
                    existing.events = self.events
                    existing.tool_calls = mask_secrets(self.tool_calls)
                    existing.error_details = self.error_details
                else:
                    trace_record = ExecutionTrace(
                        id=self.trace_id,
                        session_id=self.session_id,
                        component_id=self.component_id,
                        component_type=self.component_type,
                        status="RUNNING" if self.end_time is None else self.status, # Handle intermediate saves
                        start_time=self.start_time,
                        end_time=self.end_time,
                        duration_ms=duration_ms,
                        inputs=mask_secrets(self.inputs),
                        outputs=mask_secrets(self.outputs),
                        events=self.events,
                        tool_calls=mask_secrets(self.tool_calls),
                        error_details=self.error_details
                    )
                    db.add(trace_record)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save telemetry trace: {e}")

@asynccontextmanager
async def trace(component_id: str, component_type: str, session_id: str):
    tracker = TelemetryTracker(component_id, component_type, session_id)
    try:
        # Initial save so UI knows it started
        _bg_tasks = getattr(asyncio, "_telemetry_bg_tasks", set())
        if not hasattr(asyncio, "_telemetry_bg_tasks"):
            asyncio._telemetry_bg_tasks = _bg_tasks
            
        task = asyncio.create_task(tracker.save())
        _bg_tasks.add(task)
        task.add_done_callback(_bg_tasks.discard)
        
        yield tracker
    except Exception as e:
        tracker.set_error(e)
        raise
    finally:
        task = asyncio.create_task(tracker.save())
        _bg_tasks.add(task)
        task.add_done_callback(_bg_tasks.discard)
