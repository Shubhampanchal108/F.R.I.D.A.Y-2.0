import time
from datetime import datetime
import os
import sys

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class CareSentinel:
    """
    Autonomous Personal Secretary Care & Idle Check-ins (Jarvis Style).
    Monitors user working sessions, posture, hydration, and late night health.
    """

    def __init__(self, notifier, care_interval=2700.0):
        self.notifier = notifier
        self.last_user_activity = time.time()
        self.last_care_checkin = time.time()
        self.care_interval = care_interval  # 45 minutes
        self._care_prompt_index = 0

    def record_user_activity(self):
        """Call this whenever the user interacts with Friday via voice, text, or GUI."""
        self.last_user_activity = time.time()

    def check(self):
        now = time.time()
        time_since_activity = now - self.last_user_activity
        time_since_checkin = now - self.last_care_checkin

        # Trigger proactive care after ~45 minutes of active session without user interaction
        if time_since_checkin >= self.care_interval and time_since_activity >= self.care_interval:
            self.last_care_checkin = now
            current_hour = datetime.now().hour

            if current_hour >= 23 or current_hour <= 4:
                # Late night care
                msg = "Sir, it is getting quite late into the night. Remember that adequate rest is essential. I will keep watch over all system tasks if you wish to sleep."
                self.notifier.announce(
                    "Secretary Care Check-in",
                    msg,
                    msg,
                    event_type="late_night_care",
                    details={"hour": current_hour, "context": "Late night working session"}
                )
            else:
                care_prompts = [
                    "Sir, you have been working steadily for a while now. A quick glass of water and taking a moment to relax your eyes would be great.",
                    "Sir, just a gentle reminder: check your posture and take a brief stretch to stay refreshed.",
                    "Sir, just checking in to let you know all system operations and notifications are clear. I am standing by if you need anything."
                ]
                msg = care_prompts[self._care_prompt_index % len(care_prompts)]
                self._care_prompt_index += 1
                self.notifier.announce(
                    "Secretary Care Check-in",
                    msg,
                    msg,
                    event_type="health_and_posture_care",
                    details={"context": "Continuous working session check-in"}
                )

