"""Solution callbacks for SSE progress streaming."""

import asyncio
import threading
from typing import Optional

from team_formation.team_assignment import SolutionCallback
from team_formation.api.models import ProgressEvent


class SSESolutionCallback(SolutionCallback):
    """Solution callback that sends progress events via an async queue for SSE streaming.

    This callback extends the base SolutionCallback and adds the ability to send
    progress updates to an asyncio queue, which can then be consumed by a FastAPI
    SSE endpoint.
    """

    def __init__(
        self,
        event_queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
        stop_after_seconds: Optional[int] = None
    ):
        """Initialize the SSE solution callback.

        Args:
            event_queue: Async queue to send progress events to
            loop: Event loop for thread-safe queue operations
            stop_after_seconds: Optional time limit for optimization
        """
        super().__init__(stop_after_seconds=stop_after_seconds)
        self.event_queue = event_queue
        self.loop = loop
        self.solution_count = 0
        self._lock = threading.Lock()

    def on_solution_callback(self):
        """Called by the CP-SAT solver when a new solution is found.

        This method is called from the solver thread, so we need to be
        thread-safe when interacting with the asyncio queue.
        """
        with self._lock:
            self.solution_count += 1

            # Create progress event
            event = ProgressEvent(
                event_type="progress",
                solution_count=self.solution_count,
                objective_value=float(self.objective_value),
                wall_time=float(self.wall_time),
                num_conflicts=int(self.num_conflicts),
                message=f"Solution {self.solution_count}: objective={self.objective_value:.2f}, "
                       f"time={self.wall_time:.2f}s, conflicts={self.num_conflicts}"
            )

            # Send event to queue (thread-safe)
            asyncio.run_coroutine_threadsafe(
                self.event_queue.put(event),
                self.loop
            )

        # Check if we should stop based on time limit
        if self.stop_after_seconds and (self.wall_time > self.stop_after_seconds):
            asyncio.run_coroutine_threadsafe(
                self.event_queue.put(
                    ProgressEvent(
                        event_type="progress",
                        solution_count=self.solution_count,
                        objective_value=float(self.objective_value),
                        wall_time=float(self.wall_time),
                        num_conflicts=int(self.num_conflicts),
                        message=f"Time limit reached ({self.stop_after_seconds}s), stopping search..."
                    )
                ),
                self.loop
            )
            self.stop_search()
