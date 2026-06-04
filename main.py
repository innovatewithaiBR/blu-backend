from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import briefing

app = FastAPI(
    title="Blu API",
    description="Private orchestration API for Blu - ElevenLabs AI assistant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(briefing.router)


@app.get("/")
async def root():
    return {"status": "Blu backend is live", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
