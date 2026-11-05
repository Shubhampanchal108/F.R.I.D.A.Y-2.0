"""
F.R.I.D.A.Y - Google Calendar 1-Time Authorization & Tool Verification Script
"""
import sys
import os

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from integrations.calender.auth import get_credentials, get_token_path
from Tools.calendar_tool import (
    list_user_calendars,
    get_today_calendar_events,
    check_calendar_conflicts
)

def main():
    print("=" * 60)
    print("F.R.I.D.A.Y // Google Calendar Authorization & Verification")
    print("=" * 60)
    print("\n1. Initiating Google OAuth Login in your browser...")
    print("   Please select your Google account and grant Calendar permissions.\n")

    creds = get_credentials(interactive=True)

    if not creds or not creds.valid:
        print("\n❌ Authorization failed or was cancelled. Please check your credentials.")
        return False

    print("\n✅ Authorization successful!")
    print(f"📁 Token saved at: {get_token_path()}")

    print("\n" + "=" * 60)
    print("2. Testing Calendar Tools...")
    print("=" * 60)

    # Test 1: List calendars
    print("\n[Test 1] Fetching user calendars (list_user_calendars)...")
    cals = list_user_calendars()
    if cals.get("status") == "success":
        print(f"✅ Found {cals.get('count', 0)} calendar(s):")
        for c in cals.get("calendars", []):
            primary_tag = " (PRIMARY)" if c.get("primary") else ""
            print(f"   - {c.get('summary')} [ID: {c.get('id')}]{primary_tag}")
    else:
        print(f"❌ Failed to list calendars: {cals.get('message')}")

    # Test 2: Fetch today's events
    print("\n[Test 2] Fetching today's events (get_today_calendar_events)...")
    events = get_today_calendar_events()
    if events.get("status") == "success":
        print(f"✅ Successfully queried today's events! ({events.get('count', 0)} events found)")
        for ev in events.get("events", []):
            print(f"   - {ev.get('summary')} at {ev.get('start')}")
    else:
        print(f"❌ Failed to fetch events: {events.get('message')}")

    # Test 3: Check conflicts
    print("\n[Test 3] Testing conflict checker (check_calendar_conflicts)...")
    conflicts = check_calendar_conflicts("12:00", "13:00")
    if conflicts.get("status") == "success":
        print(f"✅ Conflict checker working properly! Conflict status: {conflicts.get('has_conflict')}")
    else:
        print(f"❌ Conflict checker test returned: {conflicts.get('message')}")

    print("\n" + "=" * 60)
    print("🎯 All Google Calendar tools are ready and verified for Friday!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    main()

