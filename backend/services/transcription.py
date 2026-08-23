from pathlib import Path
from backend.config import TRANSCRIPTION_MODE, WHISPER_MODEL, WHISPER_LANGUAGE, GROQ_API_KEY


def transcribe_local(audio_path, language=None):
    """run whisper locally on GPU if available"""
    import whisper
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"loading whisper '{WHISPER_MODEL}' on {device}")

    model = whisper.load_model(WHISPER_MODEL, device=device)

    lang = language if language is not None else WHISPER_LANGUAGE
    if lang in ("auto", ""):
        lang = None

    kwargs = {"audio": str(audio_path)}
    if lang:
        print(f"language: {lang}")
        kwargs["language"] = lang
    else:
        print("auto-detecting language")

    result = model.transcribe(**kwargs)

    duration = 0.0
    if result.get("segments"):
        duration = result["segments"][-1].get("end", 0.0)

    return {"text": result["text"].strip(), "duration": duration}


def transcribe_groq(audio_path, language=None):
    """use groq whisper api instead of running locally"""
    from groq import Groq

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")

    client = Groq(api_key=GROQ_API_KEY)

    lang = language if language is not None else WHISPER_LANGUAGE
    if lang in ("auto", ""):
        lang = None

    kwargs = {
        "model": "whisper-large-v3",
        "response_format": "verbose_json",
    }
    if lang:
        kwargs["language"] = lang

    with open(audio_path, "rb") as f:
        kwargs["file"] = f
        result = client.audio.transcriptions.create(**kwargs)

    return {"text": result.text.strip(), "duration": result.duration}


def transcribe_audio(audio_path, language=None):
    """pick between local whisper and groq api based on config"""
    if TRANSCRIPTION_MODE == "api":
        print("using groq api for transcription")
        return transcribe_groq(audio_path, language=language)
    else:
        print("using local whisper")
        return transcribe_local(audio_path, language=language)
