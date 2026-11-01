import time
import os
import sys

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools.systems_tools import get_top_resource_consumers


class SystemSentinel:
    """
    Monitors CPU spikes, RAM thresholds, and identifies top resource hogging processes.
    """

    def __init__(self, notifier, cpu_threshold=85.0, cpu_cooldown=300.0, ram_threshold=92.0, ram_cooldown=600.0):
        self.notifier = notifier
        self._high_cpu_count = 0
        self._last_cpu_alert_time = 0
        self._last_ram_alert_time = 0
        self.cpu_threshold = cpu_threshold
        self.cpu_cooldown = cpu_cooldown  # 5 minutes
        self.ram_threshold = ram_threshold
        self.ram_cooldown = ram_cooldown  # 10 minutes

    def prime(self):
        """Initializes psutil cpu counter to avoid a blocking first call."""
        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

    def check(self):
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=None)
            now = time.time()

            # --- High CPU Usage Detection ---
            if cpu_usage >= self.cpu_threshold:
                self._high_cpu_count += 1
                # Must be sustained for at least 2 cycles (~30 seconds)
                if self._high_cpu_count >= 2 and (now - self._last_cpu_alert_time >= self.cpu_cooldown):
                    self._last_cpu_alert_time = now
                    top_procs = get_top_resource_consumers(2)

                    if top_procs:
                        proc_summary = ", ".join([f"{name} ({load}%)" for name, load in top_procs])
                        msg = f"Sir, your CPU utilization is surging at {int(cpu_usage)} percent. Significant load from {proc_summary}. Would you like me to inspect running processes?"
                    else:
                        msg = f"Sir, CPU utilization has reached {int(cpu_usage)} percent. Some background tasks are heavily utilizing system resources."

                    self.notifier.announce(
                        "High CPU Utilization",
                        f"CPU usage at {int(cpu_usage)}% (Top: {top_procs})",
                        msg,
                        event_type="high_cpu_utilization",
                        details={"cpu_usage": int(cpu_usage), "top_processes": top_procs}
                    )
            else:
                self._high_cpu_count = 0

            # --- High RAM Usage Detection ---
            try:
                ram = psutil.virtual_memory()
                if ram.percent >= self.ram_threshold and (now - self._last_ram_alert_time >= self.ram_cooldown):
                    self._last_ram_alert_time = now
                    self.notifier.announce(
                        "High RAM Utilization",
                        f"Memory usage at {int(ram.percent)}%.",
                        f"Sir, system RAM utilization is at {int(ram.percent)} percent. Available memory is running low.",
                        event_type="high_ram_utilization",
                        details={"ram_percent": int(ram.percent)}
                    )
            except Exception:
                pass

        except Exception as e:
            self.notifier.log_event("System Health Check Error", str(e), level="ERROR")

