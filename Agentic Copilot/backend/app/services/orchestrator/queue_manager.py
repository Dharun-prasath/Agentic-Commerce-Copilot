import asyncio
import logging
import time
from sqlalchemy.future import select
from app.core.database import async_session_maker
from app.models.models import OrchestratorJob

logger = logging.getLogger(__name__)

class QueueManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = QueueManager()
        return cls._instance

    def __init__(self):
        self.delay_seconds = 5
        self.is_paused = False
        self.countdown_start_time = 0
        self.countdown_remaining = 0
        self.is_counting_down = False
        self._skip_delay_event = asyncio.Event()
        self._task = None

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self.run_loop())
            logger.info("QueueManager loop started.")

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def skip_delay(self):
        self._skip_delay_event.set()

    def set_delay(self, seconds: int):
        self.delay_seconds = seconds

    def get_status(self):
        return {
            "delay_seconds": self.delay_seconds,
            "is_paused": self.is_paused,
            "is_counting_down": self.is_counting_down,
            "countdown_remaining": self.countdown_remaining
        }

    async def run_loop(self):
        while True:
            try:
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue

                async with async_session_maker() as db:
                    # Check for active jobs
                    active_res = await db.execute(
                        select(OrchestratorJob)
                        .where(OrchestratorJob.status.not_in(["QUEUED", "COMPLETED", "FAILED", "CUSTOMER_NOT_INTERESTED"]))
                    )
                    active_jobs = active_res.scalars().all()
                    
                    if active_jobs:
                        # Session is actively processing
                        self.is_counting_down = False
                        await asyncio.sleep(1)
                        continue

                    # No active jobs. Get the next queued job.
                    queued_res = await db.execute(
                        select(OrchestratorJob)
                        .where(OrchestratorJob.status == "QUEUED")
                        .order_by(OrchestratorJob.created_at)
                    )
                    next_job = queued_res.scalars().first()

                    if next_job:
                        # Start countdown
                        self.is_counting_down = True
                        self.countdown_start_time = time.time()
                        self._skip_delay_event.clear()
                        
                        while True:
                            elapsed = time.time() - self.countdown_start_time
                            remaining = max(0, self.delay_seconds - int(elapsed))
                            self.countdown_remaining = remaining
                            
                            if remaining <= 0 or self._skip_delay_event.is_set():
                                break
                            
                            if self.is_paused:
                                # Pause countdown timer? For now, we'll just freeze the remaining time logic 
                                # by not incrementing elapsed if paused, but time.time() keeps moving.
                                # Let's just wait out the pause.
                                await asyncio.sleep(1)
                                continue
                                
                            await asyncio.sleep(0.5)
                            
                        # Countdown complete. Process the job.
                        if not self.is_paused:
                            self.is_counting_down = False
                            next_job.status = "TRIGGERING_INTENT_AGENT"
                            await db.commit()
                            
                            # Trigger async
                            from app.services.orchestrator.service import OrchestratorService
                            orchestrator = OrchestratorService()
                            asyncio.create_task(orchestrator._trigger_intent_agent(next_job.session_id, next_job.id))
                    else:
                        self.is_counting_down = False
                        await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"QueueManager error: {e}")
                await asyncio.sleep(5)
