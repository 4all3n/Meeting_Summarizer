# Meeting Summarizer

A web app that takes meeting audio recordings, transcribes them using OpenAI Whisper, and generates structured summaries with action items using Google Gemini.

The backend is built with FastAPI and the frontend uses Flask with Tailwind CSS.

## What it does

- Upload audio files (wav, mp3, m4a, webm, ogg, flac)
- Transcribes speech to text using Whisper (runs on GPU if you have one, otherwise CPU)
- Sends the transcript to Gemini which generates a structured summary with key decisions and action items
- You can re-transcribe with a different language or re-generate the summary without re-transcribing
- Listen back to the audio directly in the browser
- Delete old meetings when you don't need them
- Download transcripts as .txt and summaries as .md

## Tech stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Flask + Jinja2 templates + Tailwind CSS (CDN)
- **Speech-to-text**: OpenAI Whisper (local, with CUDA support) or Groq API as fallback
- **Summarization**: Google Gemini 3.6 Flash
- **Audio handling**: FFmpeg (needs to be installed separately)

## Setup

### Prerequisites

- Python 3.10+
- FFmpeg installed on your system
- A Gemini API key (free from [Google AI Studio](https://aistudio.google.com/apikey))
- NVIDIA GPU + CUDA is recommended for fast transcription, but not required

Install FFmpeg:
```bash
# arch / cachyos
sudo pacman -S ffmpeg

# ubuntu / debian
sudo apt install ffmpeg

# mac
brew install ffmpeg
```

### Installation

```bash
git clone https://github.com/4all3n/Meeting_Summarizer.git
cd Meeting_Summarizer

python -m venv venv
source venv/bin/activate  # or: source venv/bin/activate.fish

pip install -r requirements.txt
```

If you have an NVIDIA GPU and want faster transcription:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key. The important settings:

- `GEMINI_API_KEY` — your Google AI Studio key (required)
- `TRANSCRIPTION_MODE` — `local` for Whisper on your machine, `api` for Groq
- `WHISPER_MODEL` — `medium` is a good default (options: tiny, base, small, medium, large)
- `WHISPER_LANGUAGE` — defaults to `en`, the UI also has a language selector

### Running

Start both servers:
```bash
python run.py
```

Then open http://localhost:5000 in your browser.

The API docs are at http://localhost:8000/docs if you want to test endpoints directly.

You can also run the servers separately:
```bash
# terminal 1
python backend/main.py

# terminal 2
python frontend/app.py
```

## API endpoints

| Method | Endpoint | What it does |
|--------|----------|-------------|
| POST | `/api/meetings/upload` | Upload audio file (with optional language param) |
| GET | `/api/meetings` | List all meetings |
| GET | `/api/meetings/{id}` | Get meeting details |
| GET | `/api/meetings/{id}/status` | Poll processing status |
| GET | `/api/meetings/{id}/audio` | Stream audio file for playback |
| POST | `/api/meetings/{id}/resummarize` | Re-run summary on existing transcript |
| POST | `/api/meetings/{id}/retranscribe` | Re-run Whisper + summarize from scratch |
| DELETE | `/api/meetings/{id}` | Delete meeting and audio file |

## How the summarization works

I use two separate prompts to Gemini:

1. **Summary prompt** — tells Gemini to act as a meeting analyst and output a structured summary with sections for overview, key decisions, action items, and unresolved issues. I found that giving it a specific format to follow produces much more consistent results.

2. **Action items prompt** — a separate call that focuses only on extracting actionable tasks with assignees and deadlines. I tried doing both in one prompt but the action items were better when extracted separately.

The prompts ask for markdown output which gets rendered properly in the frontend.

## Project structure

```
Meeting_Summarizer/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py             # env config
│   ├── database.py           # SQLite + SQLAlchemy
│   ├── models.py             # Meeting model
│   ├── routers/
│   │   └── meetings.py       # all the API routes
│   └── services/
│       ├── transcription.py   # Whisper + Groq
│       └── summarization.py   # Gemini prompts
├── frontend/
│   ├── app.py                # Flask server
│   ├── templates/            # Jinja2 HTML
│   └── static/               # JS + CSS
├── run.py                    # starts both servers
├── requirements.txt
└── .env.example
```

## Notes

- Whisper auto-detect language can sometimes get confused by accents (it once detected British English as Welsh). That's why the default is set to English — you can change it in the dropdown when uploading.
- The app stores audio files in `backend/uploads/` and meeting data in `backend/meetings.db`.
- First transcription takes a bit longer because Whisper needs to download the model.

## Author

[4all3n](https://github.com/4all3n)