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

    id             = Column(Integer, primary_key=True, index=True)
    filename       = Column(String,  nullable=False)
    timestamp      = Column(DateTime, default=datetime.utcnow)
    passed         = Column(Boolean,  nullable=False)    # True = no defects found
    defect_count   = Column(Integer,  nullable=False)
    confidence_avg = Column(Float,    nullable=True)     # mean confidence of all detections
    detections     = Column(Text,     nullable=False)    # JSON string of all bounding boxes
    image_path     = Column(String,   nullable=False)    # path to saved image on disk
    # Severity scoring (added in Phase 2.1)
    quality_score    = Column(Float,  nullable=True)     # 0–100 board quality score
    grade            = Column(String, nullable=True)     # A / B / C / D / F
    severity_summary = Column(Text,   nullable=True)     # JSON: {critical, major, minor}


def create_tables():
    """Create all tables and run lightweight column migrations for existing DBs."""
    Base.metadata.create_all(bind=engine)
    # Migrate existing DB: add new columns if they don't exist yet
    _migrate_add_severity_columns()


def _migrate_add_severity_columns():
    """
    SQLite doesn't support adding multiple columns in one ALTER TABLE.
    We check and add each new column individually — safe to run on every startup.
    """
    from sqlalchemy import text, inspect as sa_inspect
    with engine.connect() as conn:
        inspector = sa_inspect(engine)
        existing = {col["name"] for col in inspector.get_columns("inspections")}
        migrations = [
            ("quality_score",    "ALTER TABLE inspections ADD COLUMN quality_score REAL"),
            ("grade",            "ALTER TABLE inspections ADD COLUMN grade TEXT"),
            ("severity_summary", "ALTER TABLE inspections ADD COLUMN severity_summary TEXT"),
        ]
        for col_name, sql in migrations:
            if col_name not in existing:
                conn.execute(text(sql))
                print(f"[db] Migrated: added column '{col_name}' to inspections table.")
        conn.commit()


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
