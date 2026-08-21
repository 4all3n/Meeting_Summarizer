import sys
from pathlib import Path

# add project root to python path so running `python main.py` from inside backend/ works
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.database import init_db
from backend.routers import meetings

# initialize tables & columns on startup
init_db()

app = FastAPI(
    title="Meeting Summarizer API",
    description="API for transcribing meetings and generating summaries",
    version="1.0.0",
)

# need CORS so the flask frontend can talk to this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router, prefix="/api/meetings", tags=["meetings"])


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "service": "Meeting Summarizer API"}


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
