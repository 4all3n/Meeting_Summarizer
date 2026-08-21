# 🎙️ Meeting Summarizer

Transcribe meeting audio and generate action-oriented summaries powered by **OpenAI Whisper** (ASR) and **Google Gemini** (LLM).

Upload a meeting recording → get a full transcript, structured summary, key decisions, and action items — all in seconds.

---

## ✨ Features

- **Accurate Transcription** — Whisper `medium` model with NVIDIA CUDA GPU acceleration
- **Smart Summaries** — Gemini 2.0 Flash extracts key decisions, action items, and unresolved issues
- **Dual ASR Mode** — Local Whisper (GPU) or Groq API (cloud fallback for users without GPU)
- **Drag & Drop Upload** — Clean, modern UI with real-time processing status
- **Multiple Audio Formats** — WAV, MP3, M4A, WebM, OGG, FLAC, AAC
- **Download Results** — Export transcript (.txt) and summary (.md)
- **Meeting History** — Browse and revisit past meeting summaries
- **Auto-Generated API Docs** — Interactive Swagger UI at `/docs`

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Frontend (Flask + Tailwind CSS)              │
│         Upload Audio → View Transcript → Summary         │
│              http://localhost:5000                        │
└──────────────────┬───────────────────────────────────────┘
                   │ REST API
┌──────────────────▼───────────────────────────────────────┐
│              Backend API (FastAPI)                        │
│              http://localhost:8000                        │
│              Swagger: http://localhost:8000/docs          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Whisper ASR  │  │  Gemini LLM  │  │   SQLite DB   │  │
│  │  (CUDA GPU)   │  │  (2.0 Flash) │  │  (SQLAlchemy) │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend API | FastAPI | Async REST API with auto-generated Swagger docs |
| Frontend | Flask + Jinja2 | Server-rendered HTML templates |
| Styling | Tailwind CSS | Utility-first CSS framework |
| ASR | OpenAI Whisper | Speech-to-text transcription (local, CUDA accelerated) |
| ASR Fallback | Groq API | Cloud-based Whisper for users without GPU |
| LLM | Google Gemini 2.0 Flash | Meeting summarization and action item extraction |
| Database | SQLite + SQLAlchemy | Meeting storage with ORM |
| Audio Processing | FFmpeg + Pydub | Audio format conversion |

---

## 📁 Project Structure

```
Meeting_Summarizer/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Environment-based configuration
│   ├── database.py           # SQLAlchemy setup
│   ├── models.py             # Database models
│   ├── routers/
│   │   └── meetings.py       # API endpoints
│   └── services/
│       ├── transcription.py  # Whisper + Groq ASR
│       └── summarization.py  # Gemini LLM prompts
├── frontend/
│   ├── app.py                # Flask app
│   ├── templates/            # Jinja2 HTML templates
│   └── static/               # JS, CSS assets
├── tests/
├── requirements.txt
├── .env.example
├── run.py                    # Start both servers
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg (`sudo pacman -S ffmpeg` on Arch / `sudo apt install ffmpeg` on Ubuntu)
- NVIDIA GPU + CUDA (optional but recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Meeting_Summarizer.git
cd Meeting_Summarizer
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
# venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**With CUDA support (recommended if you have NVIDIA GPU):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GEMINI_API_KEY=your_gemini_key          # Required — get from https://aistudio.google.com/apikey
TRANSCRIPTION_MODE=local                 # "local" for GPU Whisper, "api" for Groq
WHISPER_MODEL=medium                     # tiny/base/small/medium/large
GROQ_API_KEY=your_groq_key              # Optional — get from https://console.groq.com/keys
```

### 5. Run the Application

```bash
python run.py
```

This starts both servers:
- **Frontend:** http://localhost:5000
- **API Docs:** http://localhost:8000/docs

Or start them separately:
```bash
# Terminal 1 — Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
python frontend/app.py
```

---

## 📖 Usage

1. Open http://localhost:5000 in your browser
2. **Upload** a meeting audio file (drag & drop or click to browse)
3. **Wait** for processing (transcription → summarization)
4. **View** the structured summary with:
   - Meeting overview
   - Key decisions
   - Action items with assignees
   - Unresolved issues
5. **Download** the transcript or summary as files

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/meetings/upload` | Upload audio file for processing |
| `GET` | `/api/meetings` | List all meetings |
| `GET` | `/api/meetings/{id}` | Get meeting details (transcript + summary) |
| `GET` | `/api/meetings/{id}/status` | Poll processing status |
| `DELETE` | `/api/meetings/{id}` | Delete a meeting |

Full interactive API documentation available at http://localhost:8000/docs

---

## 🧠 Prompt Engineering

The LLM summarization uses carefully crafted prompts to produce structured, actionable output:

- **Role assignment** — "expert meeting analyst" for domain-focused responses
- **Explicit output format** — ensures consistent, parseable results
- **Dual-prompt strategy** — separate prompts for summary and action items for higher quality
- **Structured sections** — Summary, Key Decisions, Action Items, Unresolved Issues

---

## ⚙️ Configuration

All settings are managed via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key (required) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `TRANSCRIPTION_MODE` | `local` | `local` (Whisper) or `api` (Groq) |
| `WHISPER_MODEL` | `medium` | Whisper model size |
| `GROQ_API_KEY` | — | Groq API key (for API mode) |
| `MAX_UPLOAD_SIZE_MB` | `100` | Maximum upload file size |

---

## 🖥️ CUDA / GPU Setup

For faster transcription with NVIDIA GPUs:

```bash
# Arch Linux / CachyOS
sudo pacman -S cuda cudnn

# Ubuntu / Debian
sudo apt install nvidia-cuda-toolkit

# Verify GPU detection
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}')"
```

| Whisper Model | VRAM | Speed (GPU) | Accuracy |
|---------------|------|-------------|----------|
| `base` | ~1 GB | Fast | Good |
| `small` | ~2 GB | Fast | Better |
| `medium` | ~5 GB | Medium | Great ✅ |
| `large` | ~10 GB | Slower | Best |

---

## 📝 License

This project is for assessment/educational purposes.