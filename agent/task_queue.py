"""
=============================================================================
F.R.I.D.A.Y 2.0 // AUTONOMOUS MISSION TASK QUEUE
=============================================================================
Prioritized asynchronous background task queue for multi-step agent goals.
Enables non-blocking task submission, progress tracking, and mission cancellation.
=============================================================================
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any


class TaskStatus(Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    HIGH   = 1
    NORMAL = 2
    LOW    = 3


@dataclass(order=True)
class AgentTask:
    priority: int
    created_at: float = field(compare=False)
    task_id: str = field(compare=False)
    goal: str = field(compare=False)
    status: TaskStatus = field(compare=False, default=TaskStatus.PENDING)
    result: Any = field(compare=False, default=None)
    error: str = field(compare=False, default="")
    speak: Any = field(compare=False, default=None)
    on_complete: Any = field(compare=False, default=None)
    cancel_flag: threading.Event = field(compare=False, default_factory=threading.Event)


class TaskQueue:
    """
    Thread-safe, priority-ordered background task queue.
    """

    def __init__(self, max_concurrent: int = 1):
        self._queue: list[AgentTask] = []
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._tasks: dict[str, AgentTask] = {}
        self._running = False
        self._worker_thread: threading.Thread | None = None
        self._max_concurrent = max_concurrent
        self._executor = None

    def _get_executor(self):
        if self._executor is None:
            from agent.executor import FridayAgentExecutor
            self._executor = FridayAgentExecutor()
        return self._executor

    def start(self) -> None:
        """Starts background worker thread."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="FridayTaskQueueWorker"
        )
        self._worker_thread.start()
        print("[TaskQueue] ✅ Autonomous Task Queue Worker started.")

    def stop(self) -> None:
        """Gracefully halts worker thread."""
        self._running = False
        with self._condition:
            self._condition.notify_all()
        print("[TaskQueue] 🔴 Task Queue Worker stopped.")

    def submit(
        self,
        goal: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        speak: Callable | None = None,
        on_complete: Callable | None = None,
    ) -> str:
        """
        Submits a high-level goal to the prioritized queue.
        Returns a short task_id.
        """
        self.start()

        task_id = str(uuid.uuid4())[:8]
        task = AgentTask(
            priority=priority.value,
            created_at=time.time(),
            task_id=task_id,
            goal=goal,
            speak=speak,
            on_complete=on_complete,
        )

        with self._condition:
            self._queue.append(task)
            self._queue.sort(key=lambda t: (t.priority, t.created_at))
            self._tasks[task_id] = task
            self._condition.notify()

        print(f"[TaskQueue] 📥 Task [{task_id}] queued: '{goal[:60]}'")
        return task_id

    def cancel(self, task_id: str) -> bool:
        """Signals cancellation of a pending or active task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            task.cancel_flag.set()
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                self._queue = [t for t in self._queue if t.task_id != task_id]
                print(f"[TaskQueue] 🛑 Pending task [{task_id}] cancelled.")
                return True
            elif task.status == TaskStatus.RUNNING:
                print(f"[TaskQueue] 🛑 Running task [{task_id}] flagged for abort.")
                return True
            return False

    def get_status(self, task_id: str) -> dict | None:
        """Queries status and results of a task."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            return {
                "task_id": task.task_id,
                "goal": task.goal,
                "status": task.status.value,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at,
            }

    def _worker_loop(self) -> None:
        while self._running:
            task = None
            with self._condition:
                while not self._queue and self._running:
                    self._condition.wait(timeout=1.0)
                if not self._running:
                    break
                if self._queue:
                    task = self._queue.pop(0)

            if not task or task.cancel_flag.is_set():
                if task:
                    task.status = TaskStatus.CANCELLED
                continue

            # Execute task
            task.status = TaskStatus.RUNNING
            try:
                executor = self._get_executor()
                result = executor.execute(
                    goal=task.goal,
                    speak=task.speak,
                    cancel_flag=task.cancel_flag,
                )
                task.result = result
                task.status = TaskStatus.COMPLETED if not task.cancel_flag.is_set() else TaskStatus.CANCELLED
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED

            # Callback
            if task.on_complete:
                try:
                    task.on_complete(task.task_id, task.status.value, task.result or task.error)
                except Exception as cb_err:
                    print(f"[TaskQueue] ⚠️ on_complete callback note: {cb_err}")


_GLOBAL_QUEUE: TaskQueue | None = None
_GLOBAL_QUEUE_LOCK = threading.Lock()


def get_task_queue() -> TaskQueue:
    """Returns singleton TaskQueue instance."""
    global _GLOBAL_QUEUE
    with _GLOBAL_QUEUE_LOCK:
        if _GLOBAL_QUEUE is None:
            _GLOBAL_QUEUE = TaskQueue()
            _GLOBAL_QUEUE.start()
        return _GLOBAL_QUEUE


get_queue = get_task_queue

