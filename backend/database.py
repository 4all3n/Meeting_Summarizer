import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import DATABASE_URL, BASE_DIR

# sqlite needs this arg to work with fastapi threads
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """create tables and ensure all columns exist"""
    Base.metadata.create_all(bind=engine)

    # auto-migration for sqlite: ensure language column exists
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
            print(f"[!] DB migration note: {e}")


# dependency injection for db sessions in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
