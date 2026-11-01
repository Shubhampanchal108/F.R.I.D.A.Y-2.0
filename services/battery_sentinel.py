import os
import sys

# Ensure parent path imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Tools.systems_tools import get_battery_status


class BatterySentinel:
    """
    Monitors laptop battery charging status, discharge levels,
    and proactively dims screen brightness on critical power.
    """

    def __init__(self, notifier):
        self.notifier = notifier
        self._last_plugged = None
        self._last_battery_pct = None
        self._battery_alert_state = None  # None | "low" | "critical"
        self._full_battery_alerted = False

    def check(self):
        try:
            batt = get_battery_status()
            if not isinstance(batt, dict) or "error" in batt:
                return

            pct = batt.get("battery_percentage")
            plugged = batt.get("charging")

            if pct is None:
                return

            # --- Power Connection State Change ---
            if self._last_plugged is not None and plugged != self._last_plugged:
                if plugged:
                    # Charger just plugged in
                    self._battery_alert_state = None
                    self.notifier.announce(
                        "Power Connected",
                        f"Charger connected. Current level: {pct}%.",
                        f"Power source connected, Sir. Charging initialized at {pct} percent.",
                        event_type="power_connected",
                        details={"percentage": pct, "charging": True}
                    )
                else:
                    # Charger unplugged
                    self._full_battery_alerted = False
                    if pct <= 25:
                        self.notifier.announce(
                            "Charger Disconnected",
                            f"Charger disconnected. Battery at {pct}%.",
                            f"Sir, charger has been disconnected and battery is currently at {pct} percent.",
                            event_type="charger_disconnected",
                            details={"percentage": pct, "charging": False}
                        )

            # --- Battery Level Checks (when running on battery) ---
            if not plugged:
                if pct <= 12:
                    if self._battery_alert_state != "critical":
                        self._battery_alert_state = "critical"
                        try:
                            from Tools.systems_tools import brightness_down
                            brightness_down(20)
                        except Exception:
                            pass
                        self.notifier.announce(
                            "Critical Battery Warning",
                            f"Battery at {pct}%! Plug in charger immediately. Screen brightness dimmed to save power.",
                            f"Warning Sir! Battery is critically low at {pct} percent. I have proactively reduced screen brightness to conserve power. Please connect your charger immediately.",
                            event_type="battery_critical",
                            details={"percentage": pct, "charging": False, "brightness_dimmed": True}
                        )
                elif pct <= 20:
                    if self._battery_alert_state not in ["low", "critical"]:
                        self._battery_alert_state = "low"
                        self.notifier.announce(
                            "Low Battery Alert",
                            f"Battery level is at {pct}%. Consider charging.",
                            f"Sir, your battery level is down to {pct} percent. Please consider plugging in your charger so your workflow is not interrupted.",
                            event_type="battery_low",
                            details={"percentage": pct, "charging": False}
                        )
                else:
                    # Battery recovered above 20%
                    self._battery_alert_state = None

            # --- Battery Full Check (when plugged in) ---
            if plugged:
                if pct >= 98:
                    if not self._full_battery_alerted:
                        self._full_battery_alerted = True
                        self.notifier.announce(
                            "Battery Fully Charged",
                            f"Battery is charged to {pct}%. You can unplug the charger.",
                            f"Sir, your battery is fully charged at {pct} percent. You can disconnect the charger now to preserve battery health.",
                            event_type="battery_fully_charged",
                            details={"percentage": pct, "charging": True}
                        )
                elif pct < 95:
                    self._full_battery_alerted = False

            self._last_plugged = plugged
            self._last_battery_pct = pct

        except Exception as e:
            self.notifier.log_event("Battery Check Error", str(e), level="ERROR")

