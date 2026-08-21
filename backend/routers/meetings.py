from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from backend.config import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB, ALLOWED_EXTENSIONS, DATABASE_URL
from backend.database import get_db
from backend.models import Meeting
from backend.services.transcription import transcribe_audio
from backend.services.summarization import summarize_transcript

router = APIRouter()


def process_meeting(meeting_id: int, audio_path: str, force_retranscribe: bool = False, target_language: str = None):
    """runs in background — transcribes the audio (if needed) then summarizes it"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as DBSession

    eng = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    with DBSession(eng) as db:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return

        try:
            # step 1 — transcribe audio
            lang_to_use = target_language if target_language is not None else meeting.language
            if force_retranscribe or not meeting.transcript:
                print(f"[*] Transcribing: {meeting.filename} (language: {lang_to_use or 'auto'})")
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
                print(f"[*] Using existing transcript for: {meeting.filename}")

            # step 2 — generate summary with gemini
            print(f"[*] Summarizing: {meeting.filename}")
            meeting.status = "summarizing"
            meeting.error_message = None
            db.commit()

            summary = summarize_transcript(meeting.transcript)
            meeting.summary = summary["summary"]
            meeting.action_items = summary.get("action_items", "")

            # mark as done
            meeting.status = "completed"
            meeting.completed_at = datetime.now(timezone.utc)
            print(f"[+] Done processing: {meeting.filename}")

        except Exception as e:
            print(f"[!] Error processing {meeting.filename}: {e}")
            meeting.status = "failed"
            meeting.error_message = str(e)

        db.commit()


@router.post("/upload")
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form("auto"),
    db: Session = Depends(get_db),
):
    """upload an audio file — kicks off transcription + summarization in background"""

    # check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Use: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # read file and check size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max is {MAX_UPLOAD_SIZE_MB}MB.",
        )

    # save to disk with timestamp prefix to avoid name collisions
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    save_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"
    save_path.write_bytes(contents)

    # create db record
    meeting = Meeting(
        filename=file.filename,
        audio_path=str(save_path),
        language=language if language else "auto",
        status="processing",
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # start processing in background so we can return immediately
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
    """get all meetings sorted by newest first"""
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "filename": m.filename,
            "status": m.status,
            "duration": m.duration,
            "language": getattr(m, "language", "auto"),
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in meetings
    ]


@router.get("/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """get full details for a single meeting"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {
        "id": meeting.id,
        "filename": meeting.filename,
        "status": meeting.status,
        "duration": meeting.duration,
        "language": getattr(meeting, "language", "auto"),
        "transcript": meeting.transcript,
        "summary": meeting.summary,
        "action_items": meeting.action_items,
        "error_message": meeting.error_message,
        "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
        "completed_at": meeting.completed_at.isoformat() if meeting.completed_at else None,
    }


@router.get("/{meeting_id}/status")
def get_status(meeting_id: int, db: Session = Depends(get_db)):
    """quick endpoint to poll processing status from the frontend"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"id": meeting.id, "status": meeting.status}


@router.post("/{meeting_id}/resummarize")
def resummarize_meeting(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """re-run summarization only (uses the existing transcript)"""
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
    """re-run full transcription from audio + summarization"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not Path(meeting.audio_path).exists():
        raise HTTPException(status_code=400, detail="Original audio file no longer exists")

    meeting.status = "processing"
    meeting.transcript = None
    meeting.summary = None
    meeting.action_items = None
    meeting.error_message = None
    if language:
        meeting.language = language
    db.commit()

    background_tasks.add_task(process_meeting, meeting.id, meeting.audio_path, True, language or meeting.language)
    return {"message": "Re-transcription and summarization started.", "status": meeting.status}


@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """delete a meeting and its audio file"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # remove the audio file too
    try:
        audio = Path(meeting.audio_path)
        if audio.exists():
            audio.unlink()
    except Exception as e:
        print(f"[!] Error deleting audio file: {e}")

    db.delete(meeting)
    db.commit()
    return {"message": f"Meeting {meeting_id} deleted."}
