"""
backend/models/database.py
--------------------------
SQLAlchemy setup + Inspection table definition.

The Inspection table stores every PCB image that gets sent
to the /inspect endpoint — filename, timestamp, pass/fail verdict,
and the raw detection JSON so the frontend can redraw boxes any time.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./inspections.db"

# sync engine (fine for SQLite at this scale)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Inspection(Base):
    """One row per PCB image submitted for inspection."""
    __tablename__ = "inspections"

    id          = Column(Integer, primary_key=True, index=True)
    filename    = Column(String,  nullable=False)
    timestamp   = Column(DateTime, default=datetime.utcnow)
    passed      = Column(Boolean,  nullable=False)    # True = no defects found
    defect_count = Column(Integer, nullable=False)
    confidence_avg = Column(Float, nullable=True)     # mean confidence of all detections
    detections  = Column(Text, nullable=False)        # JSON string of all bounding boxes
    image_path  = Column(String, nullable=False)      # path to saved image on disk


def create_tables():
    """Create all tables. Called once at app startup."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency that yields a DB session per request,
    then closes it automatically — even if the request errors.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
