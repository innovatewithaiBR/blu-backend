"""
Jira service for Blu.
Fetches assigned issues and sprint status from Jira Cloud REST API.

Authentication: API Token (simplest for server-side).
Generate at: https://id.atlassian.com/manage/api-tokens
"""
from __future__ import annotations

import os
import logging
import base64
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# --- Configuration ---
JIRA_DOMAIN = os.getenv("JIRA_DOMAIN", "")  # e.g. "beamrail.atlassian.net"
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_JQL = os.getenv("JIRA_JQL", 'assignee = currentUser() AND status not in (Done, Closed) ORDER BY priority DESC')
JIRA_MAX_RESULTS = int(os.getenv("JIRA_MAX_RESULTS", "10"))

# --- Auth ---
def _get_auth_header() -> dict[str, str] | None:
    """Build Basic Auth header for Jira REST API."""
    if not (JIRA_EMAIL and JIRA_API_TOKEN and JIRA_DOMAIN):
        logger.warning("JIRA_EMAIL, JIRA_API_TOKEN, or JIRA_DOMAIN not set; Jira disabled.")
        return None
    auth_bytes = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode("utf-8")
    encoded = base64.b64encode(auth_bytes).decode("utf-8")
    return {"Authorization": f"Basic {encoded}"}


def _get_base_url() -> str | None:
    """Build the Jira REST API base URL."""
    if not JIRA_DOMAIN:
        return None
    return f"https://{JIRA_DOMAIN}/rest/api/3"


async def get_assigned_issues(
    max_results: int | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch open/pending issues assigned to the Jira user.
    Returns a list of dicts with: key, summary, status, priority, assignee.
    Falls back to mock data if credentials not configured.
    """
    if max_results is None:
        max_results = JIRA_MAX_RESULTS

    auth_header = _get_auth_header()
    base_url = _get_base_url()

    if not (auth_header and base_url):
        return _fallback_issues()

    url = f"{base_url}/search"
    params = {
        "jql": JIRA_JQL,
        "maxResults": max_results,
        "fields": "summary,status,priority,assignee,issuetype",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=auth_header, params=params)
            resp.raise_for_status()
            data = resp.json()
            issues = data.get("issues", [])

            if not issues:
                return _fallback_issues()

            out: list[dict[str, Any]] = []
            for i in issues:
                sf = i["fields"]
                out.append(
                    {
                        "key": i["key"],
                        "summary": sf.get("summary", "(No summary)"),
                        "status": sf["status"]["name"] if sf.get("status") else "Unknown",
                        "priority": sf["priority"]["name"] if sf.get("priority") else "Normal",
                        "type": sf["issuetype"]["name"] if sf.get("issuetype") else "Issue",
                        "assignee": (
                            sf["assignee"]["displayName"] if sf.get("assignee") else "Unassigned"
                        ),
                    }
                )
            return out

    except httpx.HTTPError as e:
        logger.error("Jira API error: %s (status=%s)", e, getattr(e.response, "status_code", None) if hasattr(e, "response") else None)
        return _fallback_issues()
    except Exception:
        logger.exception("Unexpected error fetching Jira issues.")
        return _fallback_issues()


def _fallback_issues() -> list[dict[str, Any]]:
    """Mock data when Jira API is not configured."""
    return [
        {
            "key": "BR-101",
            "summary": "Integrate Bobo Concierge with Gemini 2.5 Pro",
            "status": "In Progress",
            "priority": "High",
            "type": "Task",
            "assignee": "Matthew Matos (Jira token to replace)",
        },
        {
            "key": "BR-102",
            "summary": "Fix Railway deployment health check",
            "status": "In Review",
            "priority": "Medium",
            "type": "Bug",
            "assignee": "Matthew Matos (Jira token to replace)",
        },
    ]
