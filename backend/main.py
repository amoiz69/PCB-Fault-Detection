"""
backend/main.py
---------------
FastAPI application entry point.

Run with:
    uvicorn main:app --reload --port 8000

The app uses a "lifespan" context manager (FastAPI's modern pattern)
to load the YOLOv8 model once at startup rather than on every request.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.database import create_tables
from routers.inspect import router as inspect_router
from services.inference import load_model

# ── Configuration ─────────────────────────────────────────────────────────────
# Path to your trained weights from Phase 1.
# After training on Colab, download best.pt and place it here.
MODEL_WEIGHTS = str(Path(__file__).resolve().parent / "models" / "best.pt")


# ── Lifespan: startup + shutdown ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Everything before `yield` runs at startup.
    Everything after `yield` runs at shutdown.
    This replaces the old @app.on_event("startup") pattern.
    """
    print("[startup] Creating database tables...")
    create_tables()

    print("[startup] Loading YOLOv8 model...")
    load_model(MODEL_WEIGHTS)

    print("[startup] Ready. API is live.")
    yield

    # Shutdown — nothing to clean up for now
    print("[shutdown] Goodbye.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PCB Defect Inspection API",
    description="Upload PCB images and detect manufacturing defects using YOLOv8.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server (port 5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes — all endpoints live under /api/
app.include_router(inspect_router, prefix="/api")


@app.get("/")
def root():
    return {
        "status": "running",
        "docs": "http://localhost:8000/docs",
        "endpoints": ["/api/inspect", "/api/history", "/api/stats", "/api/image/{id}"],
    }
