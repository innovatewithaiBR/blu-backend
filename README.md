# Blu Backend API

Private FastAPI backend powering **Blu** — Matthew's ElevenLabs AI assistant.

## Architecture

```
ElevenLabs (voice layer)
       ↓  HTTP tool calls
Blu Backend API  ← this repo
       ↓
Gmail / Google Calendar / other services (Phase 2)
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health + version info |
| GET | `/health` | Railway health probe |
| GET | `/briefing/morning` | Morning briefing for Blu |

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

Docs at: http://localhost:8000/docs

## Deploy to Railway

1. Connect this repo in Railway (Deploy from GitHub).
2. Railway detects `Procfile` and `requirements.txt`.
3. After deploy, copy the public URL.
4. In ElevenLabs Tools, point `get_morning_briefing` to `https://YOUR-RAILWAY-URL/briefing/morning`.

## ElevenLabs Tools Config

```json
{
  "name": "get_morning_briefing",
  "description": "Fetches Matthew's morning briefing: calendar, emails, tasks, and weather.",
  "method": "GET",
  "url": "https://YOUR-RAILWAY-URL/briefing/morning"
}
```

## File Structure

```
blu-backend/
  ├── main.py              # FastAPI app entry point
  ├── requirements.txt     # Python dependencies
  ├── Procfile            # Railway process definition
  ├── railway.json        # Railway deploy config
  ├── .gitignore          # Git ignore rules
  ├── README.md           # This file
  └── app/
      ├── __init__.py
      └── routers/
          ├── __init__.py
          └── briefing.py  # /briefing/morning endpoint
```
