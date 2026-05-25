"""
backend/services/severity.py
-----------------------------
Defect severity classification and board quality scoring.

Each detection is enriched with:
  - severity        : "critical" | "major" | "minor"
  - severity_color  : hex color for the badge
  - severity_score  : numeric penalty contributed by this detection
  - area_pct        : bounding-box area as % of total image area

Board-level output:
  - quality_score   : float 0–100 (100 = perfect board)
  - grade           : "A" | "B" | "C" | "D" | "F"
  - severity_summary: {"critical": N, "major": N, "minor": N}
  - recommendation  : human-readable string
"""

from typing import List, Dict, Any

# ── Per-class severity definition ─────────────────────────────────────────────
# Base penalty (0-100 scale) reflects engineering impact on board functionality.
# short / open_circuit → functional failure → highest penalty
# missing_hole / mouse_bite → reliability risk → medium penalty
# spur / spurious_copper → cosmetic / marginal → low penalty

CLASS_SEVERITY: Dict[str, Dict[str, Any]] = {
    "short": {
        "level":        "critical",
        "base_penalty": 30,
        "color":        "#dc2626",   # red-600
    },
    "open_circuit": {
        "level":        "critical",
        "base_penalty": 25,
        "color":        "#dc2626",
    },
    "missing_hole": {
        "level":        "major",
        "base_penalty": 20,
        "color":        "#ea580c",   # orange-600
    },
    "mouse_bite": {
        "level":        "major",
        "base_penalty": 15,
        "color":        "#ea580c",
    },
    "spurious_copper": {
        "level":        "minor",
        "base_penalty": 10,
        "color":        "#ca8a04",   # yellow-600
    },
    "spur": {
        "level":        "minor",
        "base_penalty": 8,
        "color":        "#ca8a04",
    },
}

_DEFAULT_SEVERITY = {
    "level":        "minor",
    "base_penalty": 5,
    "color":        "#ca8a04",
}

# ── Grade thresholds ──────────────────────────────────────────────────────────
_GRADE_THRESHOLDS = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
    (0,  "F"),
]

_RECOMMENDATIONS = {
    "A": "Board is in excellent condition. Approved for assembly.",
    "B": "Board is acceptable. Minor review recommended before assembly.",
    "C": "Board is marginal. Rework advised before assembly.",
    "D": "Board has significant defects. Rework required.",
    "F": "Board is rejected. Critical defects detected — do not assemble.",
}


# ── Size modifier ─────────────────────────────────────────────────────────────

def _size_modifier(area_pct: float) -> float:
    """
    Scale the penalty based on defect size relative to the image.
    Larger defects are more dangerous.
    """
    if area_pct > 2.0:
        return 1.5
    if area_pct >= 0.5:
        return 1.0
    return 0.7


# ── Main scoring function ─────────────────────────────────────────────────────

def score_detections(
    detections: List[Dict[str, Any]],
    image_width: int,
    image_height: int,
) -> Dict[str, Any]:
    """
    Enrich each detection dict in-place with severity info,
    then compute the board-level quality score.

    Args:
        detections:    List of detection dicts from run_inference().
                       Each dict is mutated to add severity fields.
        image_width:   Image pixel width (for area_pct calculation).
        image_height:  Image pixel height.

    Returns a dict with board-level scores:
    {
        "quality_score":    float,   # 0–100
        "grade":            str,     # A–F
        "severity_summary": dict,    # {"critical": N, "major": N, "minor": N}
        "recommendation":   str,
    }
    """
    image_area = max(image_width * image_height, 1)   # avoid division by zero
    total_penalty = 0.0
    summary = {"critical": 0, "major": 0, "minor": 0}

    for det in detections:
        cls_name = det.get("class_name", "")
        sev_def  = CLASS_SEVERITY.get(cls_name, _DEFAULT_SEVERITY)

        # Bounding-box area as percentage of image
        bbox    = det.get("bbox", {})
        w       = bbox.get("width",  0)
        h       = bbox.get("height", 0)
        area_pct = round((w * h) / image_area * 100, 4)

        # Penalty for this detection
        conf     = det.get("confidence", 1.0)
        modifier = _size_modifier(area_pct)
        penalty  = sev_def["base_penalty"] * modifier * conf

        # Enrich the detection dict in-place
        det["severity"]       = sev_def["level"]
        det["severity_color"] = sev_def["color"]
        det["severity_score"] = round(penalty, 2)
        det["area_pct"]       = area_pct

        total_penalty              += penalty
        summary[sev_def["level"]] += 1

    # Board-level quality score (clamped 0–100)
    quality_score = round(max(0.0, 100.0 - total_penalty), 1)

    # Letter grade
    grade = "F"
    for threshold, letter in _GRADE_THRESHOLDS:
        if quality_score >= threshold:
            grade = letter
            break

    return {
        "quality_score":    quality_score,
        "grade":            grade,
        "severity_summary": summary,
        "recommendation":   _RECOMMENDATIONS[grade],
    }
