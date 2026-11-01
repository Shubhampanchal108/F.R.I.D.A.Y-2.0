"""
F.R.I.D.A.Y Services Package
============================
Modular background watchdog daemon and system sentinel services.
"""

from services.daemon import FridayDaemon, SentinelDaemon, daemon_instance, get_daemon
from services.notifier import NotificationEngine
from services.battery_sentinel import BatterySentinel
from services.system_sentinel import SystemSentinel
from services.email_sentinel import EmailSentinel
from services.care_sentinel import CareSentinel
from services.reminder_sentinel import ReminderSentinel
from services.clipboard_sentinel import ClipboardSentinel
from services.briefing_service import BriefingService

__all__ = [
    "FridayDaemon",
    "SentinelDaemon",
    "daemon_instance",
    "get_daemon",
    "NotificationEngine",
    "BatterySentinel",
    "SystemSentinel",
    "EmailSentinel",
    "CareSentinel",
    "ReminderSentinel",
    "ClipboardSentinel",
    "BriefingService"
]
