from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/briefing", tags=["briefing"])


@router.get("/morning")
async def morning_briefing():
    """
    Morning briefing endpoint for Blu.
    Phase 1: Returns mock data.
    Phase 2: Connect real Gmail/Calendar.
    """
    now = datetime.now()
    greeting = (
        "Good morning"
        if now.hour < 12
        else "Good afternoon"
        if now.hour < 17
        else "Good evening"
    )

    return {
        "greeting": f"{greeting}, Matthew!",
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M %p"),
        "summary": "Here's what's on your plate today.",
        "calendar": [
            {
                "time": "10:00 AM",
                "title": "Team standup",
                "location": "Zoom",
            },
            {
                "time": "2:00 PM",
                "title": "Investor check-in call",
                "location": "Google Meet",
            },
        ],
        "emails": [
            {
                "from": "Chief Whitmore",
                "subject": "Re: BEAMRaiL demo next week",
                "preview": "Looking forward to seeing the platform...",
            }
        ],
        "tasks": [
            "Review Railway deployment logs",
            "Follow up with UNCG advisor re: thesis draft",
            "Update BEAMRaiL pitch deck Section 3",
        ],
        "weather": {
            "location": "Buies Creek, NC",
            "condition": "Partly cloudy",
            "high": "82F",
            "low": "67F",
        },
        "note": "[MOCK DATA] Replace with real Gmail + Google Calendar integration in Phase 2.",
    }
