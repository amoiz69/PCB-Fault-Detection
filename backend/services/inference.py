"""
backend/services/inference.py
------------------------------
Loads YOLOv8 once at startup and exposes run_inference().
Loading the model is expensive (~1–2 seconds), so we do it once
and reuse it for every request — this is the "singleton" pattern.
"""

import json
from pathlib import Path
from typing import Optional

from ultralytics import YOLO
from PIL import Image

# ── Class definitions (must match your training config) ───────────────────────
CLASS_NAMES = [
    "missing_hole",
    "mouse_bite",
    "open_circuit",
    "short",
    "spur",
    "spurious_copper",
]

# One colour per class — used by frontend to colour the bounding boxes
CLASS_COLORS = {
    "missing_hole":    "#ef4444",   # red
    "mouse_bite":      "#f97316",   # orange
    "open_circuit":    "#eab308",   # yellow
    "short":           "#22c55e",   # green
    "spur":            "#a855f7",   # purple
    "spurious_copper": "#3b82f6",   # blue
}

# ── Model singleton ───────────────────────────────────────────────────────────
_model: Optional[YOLO] = None


def load_model(weights_path: str) -> None:
    """
    Called once during FastAPI startup (see main.py lifespan).
    Loads best.pt into memory and keeps it alive for the app's lifetime.
    """
    global _model
    path = Path(weights_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model weights not found at '{weights_path}'. "
            "Train the model in Phase 1 first, then copy best.pt here."
        )
    print(f"[model] Loading weights from {path}...")
    _model = YOLO(str(path))
    print("[model] Ready.")


def run_inference(image_path: str, conf_threshold: float = 0.25) -> dict:
    """
    Run YOLOv8 on a single image.

    Returns a dict:
    {
        "detections": [
            {
                "class_id": 3,
                "class_name": "short",
                "color": "#22c55e",
                "confidence": 0.87,
                "bbox": {          ← pixel coordinates, NOT normalised
                    "x1": 120, "y1": 80,
                    "x2": 145, "y2": 106,
                    "width": 25, "height": 26
                }
            },
            ...
        ],
        "defect_count": 1,
        "passed": false,
        "confidence_avg": 0.87,
        "image_width": 640,
        "image_height": 480
    }
    """
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    # Get image dimensions for the response (frontend needs these to scale boxes)
    img = Image.open(image_path)
    img_w, img_h = img.size

    results = _model.predict(
        source=image_path,
        conf=conf_threshold,
        verbose=False,          # suppress per-image console spam
    )

    detections = []
    for result in results:
        for box in result.boxes:
            cls_id   = int(box.cls.item())
            conf     = round(float(box.conf.item()), 4)
            x1, y1, x2, y2 = [round(float(v)) for v in box.xyxy[0].tolist()]
            cls_name = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else str(cls_id)

            detections.append({
                "class_id":   cls_id,
                "class_name": cls_name,
                "color":      CLASS_COLORS.get(cls_name, "#94a3b8"),
                "confidence": conf,
                "bbox": {
                    "x1": x1, "y1": y1,
                    "x2": x2, "y2": y2,
                    "width":  x2 - x1,
                    "height": y2 - y1,
                },
            })

    conf_avg = (
        round(sum(d["confidence"] for d in detections) / len(detections), 4)
        if detections else None
    )

    return {
        "detections":    detections,
        "defect_count":  len(detections),
        "passed":        len(detections) == 0,
        "confidence_avg": conf_avg,
        "image_width":   img_w,
        "image_height":  img_h,
    }
