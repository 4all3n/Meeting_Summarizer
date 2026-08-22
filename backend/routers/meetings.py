from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB, ALLOWED_EXTENSIONS
from backend.database import SessionLocal, get_db
from backend.models import Meeting
from backend.services.transcription import transcribe_audio
from backend.services.summarization import summarize_transcript

router = APIRouter()


def process_meeting(meeting_id: int, audio_path: str, force_retranscribe: bool = False, target_language: str = None):
    """background task that transcribes audio then summarizes it"""
    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return

        try:
            lang_to_use = target_language if target_language is not None else meeting.language

            if force_retranscribe or not meeting.transcript:
                print(f"[*] Transcribing: {meeting.filename} (lang={lang_to_use or 'auto'})")
                meeting.status = "transcribing"
                meeting.error_message = None
                if target_language is not None:
                    meeting.language = target_language
                db.commit()

                result = transcribe_audio(audio_path, language=lang_to_use)
                meeting.transcript = result["text"]
                meeting.duration = result.get("duration")
                print(f"[+] Transcription done for {meeting.filename}")
            else:
                print(f"[*] Reusing existing transcript for {meeting.filename}")

            # now summarize
            print(f"[*] Summarizing: {meeting.filename}")
            meeting.status = "summarizing"
            meeting.error_message = None
            db.commit()

            summary = summarize_transcript(meeting.transcript)
            meeting.summary = summary["summary"]
            meeting.action_items = summary.get("action_items", "")

            meeting.status = "completed"
            meeting.completed_at = datetime.now(timezone.utc)
            print(f"[+] Done: {meeting.filename}")

        except Exception as e:
            print(f"[!] Error processing {meeting.filename}: {e}")
            meeting.status = "failed"
            meeting.error_message = str(e)

        db.commit()
    finally:
        db.close()


@router.post("/upload")
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("auto"),
    db: Session = Depends(get_db),
):
    # validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Use: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max is {MAX_UPLOAD_SIZE_MB}MB.",
        )

    # save file
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    save_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"
    save_path.write_bytes(contents)

    meeting = Meeting(
        filename=file.filename,
        audio_path=str(save_path),
        language=language if language else "auto",
        status="processing",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    background_tasks.add_task(process_meeting, meeting.id, str(save_path), False, language)

    return {
        "id": meeting.id,
        "filename": meeting.filename,
        "language": meeting.language,
        "status": meeting.status,
        "message": "Upload successful, processing started.",
    }


@router.get("")
def list_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "filename": m.filename,
            "status": m.status,
            "duration": m.duration,
            "language": m.language or "auto",
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in meetings
    ]


@router.get("/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {
        "id": meeting.id,
        "filename": meeting.filename,
        "status": meeting.status,
        "duration": meeting.duration,
        "language": meeting.language or "auto",
        "transcript": meeting.transcript,
        "summary": meeting.summary,
        "action_items": meeting.action_items,
        "error_message": meeting.error_message,
        "audio_path": meeting.audio_path,
        "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
        "completed_at": meeting.completed_at.isoformat() if meeting.completed_at else None,
    }


@router.get("/{meeting_id}/status")
def get_status(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"id": meeting.id, "status": meeting.status}


@router.get("/{meeting_id}/audio")
def get_audio(meeting_id: int, db: Session = Depends(get_db)):
    """serve the uploaded audio file for playback"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    audio_file = Path(meeting.audio_path)
    if not audio_file.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    # figure out the mime type from extension
    ext = audio_file.suffix.lower()
    mime_types = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
        ".aac": "audio/aac",
    }
    media_type = mime_types.get(ext, "application/octet-stream")

    return FileResponse(audio_file, media_type=media_type, filename=meeting.filename)


@router.post("/{meeting_id}/resummarize")
def resummarize_meeting(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """re-run just the summarization on the existing transcript"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    meeting.status = "processing"
    meeting.error_message = None
    db.commit()

    background_tasks.add_task(process_meeting, meeting.id, meeting.audio_path, False, None)
    return {"message": "Re-summarization started.", "status": meeting.status}


@router.post("/{meeting_id}/retranscribe")
def retranscribe_meeting(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    language: str = Form(None),
    db: Session = Depends(get_db),
):
    """re-run whisper from the audio file + re-summarize"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not Path(meeting.audio_path).exists():
        raise HTTPException(status_code=400, detail="Original audio file not found")

    meeting.status = "processing"
    meeting.transcript = None
    meeting.summary = None
    meeting.action_items = None
    meeting.error_message = None
    if language:
        meeting.language = language
    db.commit()

    background_tasks.add_task(process_meeting, meeting.id, meeting.audio_path, True, language or meeting.language)
    return {"message": "Re-transcription started.", "status": meeting.status}


@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # try to clean up the audio file
    try:
        audio = Path(meeting.audio_path)
        if audio.exists():
            audio.unlink()
    except Exception as e:
        print(f"[!] couldn't delete audio file: {e}")

    db.delete(meeting)
    db.commit()
    return {"message": f"Meeting {meeting_id} deleted."}
