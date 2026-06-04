"""
Morning briefing endpoint for Blu.
Phase 2: Connects to real Google Calendar and Jira Cloud.
Falls back to mock data if env vars are not set.
"""
import asyncio
from fastapi import APIRouter

from app.services.google_calendar import get_calendar_events
from app.services.jira import get_assigned_issues

router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.get("/morning")
async def morning_briefing():
    """Fetch Matthew's calendar events and Jira tasks.
    Runs both service calls in parallel using asyncio.gather.
    Falls back to mock data if credentials are not configured.
    """
    calendar, tasks = await asyncio.gather(
        asyncio.get_event_loop().run_in_executor(
            None, lambda: get_calendar_events(days_ahead=3, quiet_hours_start=6)
        ),
        get_assigned_issues(max_results=10),
    )

    return {
        "greeting": "Good morning, Matthew!",
        "summary": "Here's what's on your plate today.",
        "calendar": calendar,
        "tasks": [
            f"{t['key']}: {t['summary']} [{t['status']}, {t['priority']}]"
            for t in tasks
        ],
    }
