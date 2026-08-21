# 🎙️ Meeting Summarizer

A full-stack application to transcribe meeting audio recordings and generate structured, action-oriented summaries powered by **OpenAI Whisper** (ASR) and **Google Gemini** (LLM).

Built with a **FastAPI** backend API and a **Flask + Tailwind CSS** frontend web interface.

---

## ✨ Features

- **High-Accuracy Speech-to-Text**: Powered by OpenAI Whisper (`medium` model by default) with automatic **NVIDIA CUDA GPU acceleration** and CPU fallback.
- **Multilingual Support & Language Selector**: Transcribe in English, Spanish, French, German, Hindi, Japanese, etc., or use Auto-detect.
- **Structured Action-Oriented Summaries**: Generates a clean overview, key decisions made, action item checklist with assignees & deadlines, and unresolved questions using **Google Gemini 3.6 Flash**.
- **Dual ASR Mode**: Run Whisper locally on your GPU/CPU offline, or toggle to **Groq Whisper API** (`whisper-large-v3`) in `.env` if running on low-resource machines.
- **Re-summarize & Re-transcribe**:
  - `Re-generate Summary`: Quickly re-runs LLM summarization on the existing transcript.
  - `Re-transcribe & Summarize`: Re-runs full audio speech recognition with selectable language.
- **Meeting Management & Deletion**: View past meeting history, track processing states, and delete individual recordings & database records with one click.
- **Export & Downloads**: Download complete transcripts as `.txt` and structured meeting summaries as `.md`.
- **Interactive REST API**: Fully documented with auto-generated Swagger UI at `http://localhost:8000/docs`.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Frontend (Flask + Tailwind CSS)              │
│         Upload Audio → View Transcript → Summary         │
│              http://localhost:5000                        │
└──────────────────┬───────────────────────────────────────┘
                   │ HTTP / REST API
┌──────────────────▼───────────────────────────────────────┐
│              Backend API (FastAPI)                        │
│              http://localhost:8000                        │
│              Swagger Docs: http://localhost:8000/docs     │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Whisper ASR  │  │  Gemini LLM  │  │   SQLite DB   │  │
│  │  (CUDA / CPU) │  │  (3.6 Flash) │  │  (SQLAlchemy) │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Description |
|-------|-----------|-------------|
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) | Async REST API with background task workers & OpenAPI Swagger |
| **Frontend UI** | [Flask](https://flask.palletsprojects.com/) + Jinja2 | Server-rendered HTML templates |
| **Styling** | [Tailwind CSS](https://tailwindcss.com/) | Responsive UI components |
| **ASR (Primary)** | [OpenAI Whisper](https://github.com/openai/whisper) | Local offline speech recognition with CUDA acceleration |
| **ASR (Fallback)** | [Groq API](https://groq.com/) | Cloud-based Whisper-large-v3 inference |
| **LLM Summarization**| [Google Gemini 3.6 Flash](https://ai.google.dev/) | Structured summary & action item extraction |
| **Database** | SQLite + [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Persistent storage with auto-schema migration |
| **Audio Processing** | FFmpeg | Audio conversion & multi-format support |

---

## 📁 Project Structure

```
Meeting_Summarizer/
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry & CORS config
│   ├── config.py                # Environment variable loader
│   ├── database.py              # SQLite engine & auto-migration
│   ├── models.py                # SQLAlchemy Meeting model
│   ├── routers/
│   │   └── meetings.py          # API endpoints (upload, status, retranscribe, delete)
│   └── services/
│       ├── transcription.py     # Whisper CUDA + Groq fallback + language selector
│       └── summarization.py     # Gemini LLM prompts & smart model fallback
│
├── frontend/
│   ├── app.py                  # Flask web server
│   ├── templates/
│   │   ├── base.html            # Base layout with Tailwind
│   │   ├── index.html           # Home page, drag-drop upload & history
│   │   └── meeting.html         # Meeting detail view (summary, transcript, actions)
│   └── static/
│       ├── js/app.js            # Upload progress, status polling & deletion
│       └── css/custom.css       # Prose styling
│
├── sample_audio/                # Audio files for testing
├── .env.example                 # Environment configuration template
├── requirements.txt             # Python dependencies
├── run.py                       # Unified startup script
└── README.md                    # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (tested on 3.10 – 3.14)
- **FFmpeg** installed on your system:
  - **Arch Linux / CachyOS**: `sudo pacman -S ffmpeg`
  - **Ubuntu / Debian**: `sudo apt update && sudo apt install ffmpeg`
  - **macOS**: `brew install ffmpeg`
  - **Windows**: `winget install Gyan.FFmpeg`
- **NVIDIA GPU & CUDA** (optional, recommended for fast Whisper transcription)

---

### 1. Clone the Repository

```bash
git clone https://github.com/4all3n/Meeting_Summarizer.git
cd Meeting_Summarizer
```

### 2. Set Up Virtual Environment

**On Linux / macOS (Bash / Zsh):**
```bash
python -m venv venv
source venv/bin/activate
```

**On Fish Shell:**
```fish
python -m venv venv
source venv/bin/activate.fish
```

**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

*(Optional) Install PyTorch with CUDA if you have an NVIDIA GPU:*
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Configure Environment Variables

Copy the sample environment file:
```bash
cp .env.example .env
```

Open `.env` and add your **Gemini API key** (get one free at [Google AI Studio](https://aistudio.google.com/apikey)):

```env
# Gemini API Key (Required)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash

# Transcription Settings
TRANSCRIPTION_MODE=local
WHISPER_MODEL=medium
WHISPER_LANGUAGE=en

# Groq API Key (Optional for cloud fallback)
GROQ_API_KEY=your_groq_api_key_here
```

---

### 5. Run the Application

Start both the FastAPI backend and Flask frontend together:

```bash
python run.py
```

- **Frontend UI**: [http://localhost:5000](http://localhost:5000)
- **API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

*Or start them in separate terminals:*
```bash
# Terminal 1 — FastAPI Backend (Port 8000)
python backend/main.py

# Terminal 2 — Flask Frontend (Port 5000)
python frontend/app.py
```

---

## 📖 How to Use

1. Open **[http://localhost:5000](http://localhost:5000)** in your web browser.
2. **Upload Audio**: Drag & drop or browse your meeting audio file (`.wav`, `.mp3`, `.m4a`, `.webm`, `.flac`, `.ogg`).
3. **Select Language**: Pick the audio language from the dropdown (or leave as **Auto-detect**).
4. Click **Upload & Process**.
5. The page polls the backend in real time as it transcribes and summarizes the recording.
6. **Review Results**:
   - 📝 **Meeting Summary**: High-level discussion overview.
   - 📌 **Key Decisions**: Explicit decisions confirmed in the meeting.
   - ✅ **Action Items**: Checklist with assignees and deadlines.
   - ❓ **Unresolved Issues**: Items flagged for follow-up.
   - 🎙️ **Full Transcript**: Expandable text with download options.
7. **Actions**:
   - Click **🔄 Re-generate Summary** to re-prompt Gemini on the saved transcript.
   - Click **🎙️ Re-transcribe & Summarize** to re-run Whisper with a new language setting.
   - Click **🗑️ Delete** to remove the meeting and its audio recording.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/meetings/upload` | Upload audio file with language selection |
| `GET` | `/api/meetings` | List all processed meetings (newest first) |
| `GET` | `/api/meetings/{id}` | Get full meeting data (transcript + summary) |
| `GET` | `/api/meetings/{id}/status` | Poll meeting processing state (`transcribing`, `summarizing`, `completed`, `failed`) |
| `POST` | `/api/meetings/{id}/resummarize` | Re-run Gemini summarization on existing transcript |
| `POST` | `/api/meetings/{id}/retranscribe` | Re-run Whisper transcription from original audio + summarize |
| `DELETE`| `/api/meetings/{id}` | Delete meeting record and delete audio file from disk |

Full interactive testing is available at the Swagger UI: `http://localhost:8000/docs`.

---

## 🧠 Prompt Engineering Strategy

To ensure high-quality, actionable meeting summaries, a **dual-prompt strategy** is used:

1. **Role-Grounded Summarization**:
   Assigns the persona of an *"expert meeting analyst"* and enforces a strict structured markdown layout with distinct sections:
   - `### Meeting Summary`
   - `### Key Decisions`
   - `### Action Items`
   - `### Unresolved Issues`

2. **Dedicated Action Item Extraction**:
   A secondary targeted prompt extracts actionable tasks with explicit fields:
   `- [ ] [Task] — Assigned to: [Person] — Deadline: [Date]`

3. **Resilient Model Fallback**:
   The service includes smart fallback logic across Gemini Flash model versions (`gemini-3.6-flash`, `gemini-3.5-flash`, etc.) to ensure zero downtime if API aliases change.

---

## 📊 Sample Output

### Audio Transcript:
> *"of the research company we contracted to carry out the work. Now Ms Reyes will arrive at 11.30 so I plan to break at about 11.15 to give her time to set up. It may also mean that we need to interrupt the first few agenda items but we'll come back to those. And lastly I'd like to leave a little bit of time under any other business to discuss whatever might come out of the presentation. Okay so item one is relocation and plans for flexible working. Now as you know Paul and his team have been working on plans to extend flexible working hours across the company. So Paul perhaps I can begin by asking you to fill us in on your progress. Sure."*

### Generated Summary:
> **Meeting Summary**  
> The meeting opened with logistical announcements regarding the overall schedule and agenda adjustments. The chairperson noted that Ms. Reyes, representing the contracted research company, is scheduled to arrive at 11:30 AM. To allow for presentation setup, a break was planned for 11:15 AM, with remaining agenda items to be revisited afterward. The discussion then transitioned to the primary agenda topic: company-wide relocation and flexible working arrangements.  
>  
> **Key Decisions**  
> - Break the meeting at 11:15 AM for presentation setup before Ms. Reyes arrives at 11:30 AM.  
> - Reserve time under Any Other Business (AOB) to address presentation takeaways.  
>  
> **Action Items**  
> - [ ] Present and update the team on flexible working plans across the company — Assigned to: Paul and team — Deadline: Not specified  
>  
> **Unresolved Issues**  
> - Agenda topics interrupted by the presentation break will be resumed following the presentation.

---

## ⚙️ Configuration Reference (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(Required)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Gemini model name |
| `TRANSCRIPTION_MODE` | `local` | `local` (offline Whisper) or `api` (Groq API) |
| `WHISPER_MODEL` | `medium` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `WHISPER_LANGUAGE` | `en` | Default Whisper language code (`en`, `auto`, etc.) |
| `GROQ_API_KEY` | `""` | Optional Groq API key for cloud ASR fallback |
| `API_BASE_URL` | `http://localhost:8000/api` | API URL for Flask frontend |
| `MAX_UPLOAD_SIZE_MB` | `100` | Max file upload limit in megabytes |

---

## 👤 Author

Developed by **[4all3n](https://github.com/4all3n)**  
GitHub: [https://github.com/4all3n](https://github.com/4all3n)