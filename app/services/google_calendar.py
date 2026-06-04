"""
Google Calendar service for Blu.
Fetches upcoming events from Google Calendar using the Google Calendar API.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# --- Configuration ---
# For service account flow (recommended for server-side apps)
# Generate a service account JSON key from Google Cloud Console:
# https://console.cloud.google.com/iam-admin/serviceaccounts
# Then download the JSON and paste it into a GOOGLE_SERVICE_ACCOUNT_JSON env var
# on Railway (one line, minified JSON).
# Scopes needed:
#   https://www.googleapis.com/auth/calendar.readonly

CREDENTIALS_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
USER_EMAIL = os.getenv("GOOGLE_USER_EMAIL", "")  # "impersonate" this account
SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


def _get_credentials() -> service_account.Credentials | None:
    """Build credentials from the service account JSON in env."""
    if not CREDENTIALS_KEY:
        logger.warning("GOOGLE_SERVICE_ACCOUNT_JSON not set; calendar disabled.")
        return None
    try:
        import json
        info = json.loads(CREDENTIALS_KEY)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=[SCOPE]
        )
        if USER_EMAIL:
            creds = creds.with_subject(USER_EMAIL)
        return creds
    except Exception:
        logger.exception("Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON.")
        return None


def _get_service() -> Any | None:
    """Build the Google Calendar API service object."""
    creds = _get_credentials()
    if not creds:
        return None
    try:
        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    except Exception:
        logger.exception("Failed to build calendar service.")
        return None


def get_calendar_events(
    days_ahead: int = 3,
    quiet_hours_start: int = 6,
) -> list[dict[str, Any]]:
    """
    Fetch upcoming calendar events for the next `days_ahead` days.
    Filters to events after `quiet_hours_start` (0-23, 24hr).
    Returns a list of dicts with: time, title, location.
    """
    service = _get_service()
    if not service:
        return _fallback_events()

    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)

    try:
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat() + "Z",
                timeMax=end.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        if not events:
            return _fallback_events()

        out: list[dict[str, Any]] = []
        for e in events:
            start_str = e["start"].get("dateTime", e["start"].get("date"))
            title = e.get("summary", "(No title)")
            location = e.get("location", "")

            # Parse time for human-friendly output
            try:
                # Try RFC3339 datetime
                if "T" in start_str:
                    dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    local_dt = dt.astimezone()
                    time_str = local_dt.strftime("%I:%M %p")
                    if local_dt.hour < quiet_hours_start:
                        continue
                else:
                    # All-day event
                    dt = datetime.strptime(start_str, "%Y-%m-%d")
                    time_str = "All day"
            except Exception:
                time_str = start_str[:10]

            out.append(
                {
                    "time": time_str if time_str != "All day" else f"{time_str} - {title}",
                    "title": title,
                    "location": location,
                }
            )
        return out if out else _fallback_events()

    except Exception:
        logger.exception("Error fetching Google Calendar events.")
        return _fallback_events()


def _fallback_events() -> list[dict[str, Any]]:
    """Mock data used when the API is not configured."""
    return [
        {
            "time": "10:00 AM",
            "title": "Team standup (connect Gmail to replace)",
            "location": "Zoom",
        },
        {
            "time": "2:00 PM",
            "title": "Investor check-in (connect Gmail to replace)",
            "location": "Google Meet",
        },
    ]
