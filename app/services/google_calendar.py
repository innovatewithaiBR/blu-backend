"""
Google Calendar service for Blu.
Fetches upcoming events from Google Calendar using the Google Calendar API.
Uses OAuth2 Client Credentials flow (Desktop app type).
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any

import requests as http_requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# --- Configuration ---
# For OAuth2 Desktop app flow:
# 1. Create OAuth2 client in Google Cloud Console (Desktop app type)
# 2. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars on Railway
# 3. For server-side use: generate a refresh token once, store in GOOGLE_REFRESH_TOKEN
# Scopes needed:
#   https://www.googleapis.com/auth/calendar.readonly

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")
USER_EMAIL = os.getenv("GOOGLE_USER_EMAIL", "")
SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


def _get_credentials() -> Credentials | None:
    """Build credentials from refresh token."""
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.warning("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set; calendar disabled.")
        return None

    if REFRESH_TOKEN:
        logger.info("Using refresh token for Google Calendar credentials.")
        try:
            creds = Credentials(
                token=None,
                refresh_token=REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                scopes=[SCOPE],
            )
            # Refresh to get a fresh access token
            creds.refresh(Request())
            return creds
        except Exception:
            logger.exception("Failed to refresh token.")
            return None

    logger.info("No refresh token; calendar will use fallback data.")
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
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
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
            try:
                if "T" in start_str:
                    dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    local_dt = dt.astimezone(ZoneInfo("America/New_York"))
                time_str = local_dt.strftime("%I:%M %p %Z")
                    if local_dt.hour < quiet_hours_start:
                        continue
                else:
                    dt = datetime.strptime(start_str, "%Y-%m-%d")
                    time_str = "All day"
            except Exception:
                time_str = start_str[:10]
            out.append(
                {
                    "time": time_str,
                    "title": title,
                    "location": location,
                }
            )
        return out if out else _fallback_events()
    except Exception:
        logger.exception("Error fetching Google Calendar events.")
        return _fallback_events()


def _fallback_events() -> list[dict[str, Any]]:
    """Mock data used when the API is not configured or fails."""
    return [
        {
            "time": "10:00 AM",
            "title": "Team standup (connect Google Calendar to replace)",
            "location": "Zoom",
        },
        {
            "time": "2:00 PM",
            "title": "Investor check-in (connect Google Calendar to replace)",
            "location": "Google Meet",
        },
    ]
