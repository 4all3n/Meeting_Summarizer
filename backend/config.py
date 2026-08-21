import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# paths
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'meetings.db'}")

# transcription settings
# set to "local" to use whisper on your machine, or "api" to use groq's api
TRANSCRIPTION_MODE = os.getenv("TRANSCRIPTION_MODE", "local")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")  # "en" for English, or "" for auto-detect
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# gemini llm settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# upload limits
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac", ".aac"}
