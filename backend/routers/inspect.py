"""
backend/routers/inspect.py
---------------------------
POST /inspect  — accepts an image, runs inference, saves result to DB.
GET  /history  — returns all past inspections (newest first).
GET  /stats    — aggregate stats: total inspected, pass rate, common defects.
GET  /image/{inspection_id} — serves the original uploaded image.
"""

import json
import shutil
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models.database import Inspection, get_db
from services.inference import run_inference

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


# ── POST /inspect ─────────────────────────────────────────────────────────────

@router.post("/inspect")
async def inspect_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    1. Validate the uploaded file is an image.
    2. Save it to disk with a unique name (avoids overwrite collisions).
    3. Run YOLOv8 inference.
    4. Persist the result to SQLite.
    5. Return the full detection payload to the frontend.
    """
    # Validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Use JPG, PNG, BMP, or WEBP."
        )

    # Save to disk with a UUID prefix so filenames never collide
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    save_path = UPLOAD_DIR / unique_name

    with save_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run inference
    try:
        result = run_inference(str(save_path))
    except Exception as e:
        save_path.unlink(missing_ok=True)   # clean up on failure
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    # Persist to DB
    inspection = Inspection(
        filename      = file.filename,
        timestamp     = datetime.utcnow(),
        passed        = result["passed"],
        defect_count  = result["defect_count"],
        confidence_avg = result["confidence_avg"],
        detections    = json.dumps(result["detections"]),
        image_path    = str(save_path),
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    return {
        "id":            inspection.id,
        "filename":      file.filename,
        "timestamp":     inspection.timestamp.isoformat(),
        "passed":        result["passed"],
        "defect_count":  result["defect_count"],
        "confidence_avg": result["confidence_avg"],
        "image_width":   result["image_width"],
        "image_height":  result["image_height"],
        "detections":    result["detections"],
    }


# ── GET /history ──────────────────────────────────────────────────────────────

@router.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """Return the N most recent inspections, newest first."""
    rows = (
        db.query(Inspection)
        .order_by(Inspection.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id":            r.id,
            "filename":      r.filename,
            "timestamp":     r.timestamp.isoformat(),
            "passed":        r.passed,
            "defect_count":  r.defect_count,
            "confidence_avg": r.confidence_avg,
            "detections":    json.loads(r.detections),
        }
        for r in rows
    ]


# ── GET /stats ────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Aggregate stats for the dashboard summary panel."""
    all_rows = db.query(Inspection).all()

    if not all_rows:
        return {
            "total": 0, "passed": 0, "failed": 0,
            "pass_rate": None, "defect_breakdown": {}
        }

    total  = len(all_rows)
    passed = sum(1 for r in all_rows if r.passed)

    # Count each defect type across all inspections
    defect_breakdown: dict[str, int] = {}
    for row in all_rows:
        for det in json.loads(row.detections):
            name = det["class_name"]
            defect_breakdown[name] = defect_breakdown.get(name, 0) + 1

    return {
        "total":            total,
        "passed":           passed,
        "failed":           total - passed,
        "pass_rate":        round(passed / total * 100, 1),
        "defect_breakdown": defect_breakdown,
    }


# ── GET /image/{id} ───────────────────────────────────────────────────────────

@router.get("/image/{inspection_id}")
def get_image(inspection_id: int, db: Session = Depends(get_db)):
    """Serve the original uploaded PCB image for a given inspection."""
    row = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Inspection not found.")
    path = Path(row.image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk.")
    return FileResponse(str(path))
