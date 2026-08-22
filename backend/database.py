import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import DATABASE_URL, BASE_DIR

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """create tables if they dont exist, and add any missing columns"""
    Base.metadata.create_all(bind=engine)

    # had to add language column later so this handles old databases
    db_file = BASE_DIR / "meetings.db"
    if db_file.exists():
        try:
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(meetings)")
            cols = [row[1] for row in cur.fetchall()]
            if "language" not in cols:
                cur.execute("ALTER TABLE meetings ADD COLUMN language VARCHAR(20) DEFAULT 'auto'")
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] migration warning: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
