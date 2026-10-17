"""
F.R.I.D.A.Y // Background Countdown Timer Tool
Sets asynchronous timers for tasks, tea breaks, pomodoro, or reminders.
Notifies with Windows audio chime, desktop toast, and spoken announcement when complete.
"""

import threading
import time
import re
from datetime import datetime
import winsound

_active_timers = {}
_timer_lock = threading.Lock()


def _timer_worker(timer_id: str, total_seconds: float, label: str):
    time.sleep(total_seconds)

    with _timer_lock:
        if timer_id not in _active_timers:
            # Timer was cancelled
            return
        del _active_timers[timer_id]

    # 1. Audible alert chime
    try:
        for _ in range(3):
            winsound.Beep(1200, 200)
            time.sleep(0.08)
    except Exception:
        pass

    # 2. Desktop Notification
    try:
        from plyer import notification
        notification.notify(
            title="⏰ F.R.I.D.A.Y Timer Complete",
            message=f"Sir, your timer for '{label}' has finished!",
            app_name="F.R.I.D.A.Y",
            timeout=8
        )
    except Exception:
        pass

    # 3. Spoken Announcement via Central Speech Manager
    try:
        from speak import speak
        speak(f"Sir, your timer for {label} has finished.", priority=1, allow_interrupt=True, block=False)
    except Exception:
        pass


def set_timer(duration: str, label: str = "Timer") -> dict:
    """
    Sets a countdown timer for a specified duration.
    duration can be:
    - '5 minutes', '10 mins', '30 seconds', '1 hour', '1.5 hours'
    - or just a number like '5' (defaults to minutes)
    """
    try:
        d_str = str(duration).lower().strip()
        total_seconds = 0.0

        # Parse units
        m_hr = re.search(r'([\d\.]+)\s*(h|hr|hour|hours)', d_str)
        m_min = re.search(r'([\d\.]+)\s*(m|min|minute|minutes)', d_str)
        m_sec = re.search(r'([\d\.]+)\s*(s|sec|second|seconds)', d_str)

        if m_hr:
            total_seconds += float(m_hr.group(1)) * 3600
        if m_min:
            total_seconds += float(m_min.group(1)) * 60
        if m_sec:
            total_seconds += float(m_sec.group(1))

        if total_seconds == 0.0:
            # Try plain number (default to minutes)
            m_num = re.search(r'^([\d\.]+)$', d_str)
            if m_num:
                total_seconds = float(m_num.group(1)) * 60
            else:
                return {
                    "status": "error",
                    "message": f"Could not parse duration from '{duration}'. Example: '5 minutes', '30 seconds', '1 hour'."
                }

        if total_seconds <= 0:
            return {"status": "error", "message": "Timer duration must be greater than zero."}

        timer_id = f"{label.strip().lower()}_{int(time.time())}"
        start_time = datetime.now()
        target_time = datetime.fromtimestamp(time.time() + total_seconds)

        t = threading.Thread(
            target=_timer_worker,
            args=(timer_id, total_seconds, label),
            daemon=True
        )

        with _timer_lock:
            _active_timers[timer_id] = {
                "id": timer_id,
                "label": label,
                "total_seconds": total_seconds,
                "target_time": target_time.strftime("%I:%M:%S %p"),
                "thread": t
            }

        t.start()

        formatted_duration = (
            f"{int(total_seconds // 60)} min" if total_seconds >= 60 else f"{int(total_seconds)} sec"
        )

        return {
            "status": "success",
            "action": "set_timer",
            "message": f"Timer for '{label}' set for {formatted_duration}. Will alert at {target_time.strftime('%I:%M:%S %p')}.",
            "label": label,
            "duration_seconds": total_seconds,
            "finish_time": target_time.strftime("%I:%M:%S %p")
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to set timer: {str(e)}"}


def list_active_timers() -> dict:
    """Lists all currently running countdown timers."""
    with _timer_lock:
        timers = [
            {"label": v["label"], "finishes_at": v["target_time"]}
            for v in _active_timers.values()
        ]
        return {
            "status": "success",
            "count": len(timers),
            "timers": timers
        }


def cancel_timer(label: str = None) -> dict:
    """Cancels a specific timer by label or cancels all active timers if no label is given."""
    with _timer_lock:
        if not _active_timers:
            return {"status": "success", "message": "No active timers to cancel."}

        if not label or label.lower() in ["all", "everything"]:
            count = len(_active_timers)
            _active_timers.clear()
            return {"status": "success", "message": f"Cancelled all {count} active timer(s)."}

        to_del = []
        for tid, v in _active_timers.items():
            if label.lower() in v["label"].lower():
                to_del.append(tid)

        if not to_del:
            return {"status": "error", "message": f"No active timer found matching '{label}'."}

        for tid in to_del:
            del _active_timers[tid]

        return {"status": "success", "message": f"Cancelled timer matching '{label}'."}
