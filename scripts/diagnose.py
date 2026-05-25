"""
scripts/diagnose.py
--------------------
Run this on your real PCB images to inspect the confidence distribution
of all detections at a very low threshold (0.01) — this reveals everything
the model "sees", including what it normally suppresses.

Usage:
    cd /Users/abdulmoiz/Downloads/pcb-phase2/backend
    python ../scripts/diagnose.py --source path/to/real_pcb_images/

Interpret results:
    - Most false positives at conf 0.25–0.45 → threshold adjustment is enough
    - False positives at conf 0.70+           → model is genuinely confused,
                                                 needs fine-tuning/retraining
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from ultralytics import YOLO

CLASS_NAMES = [
    "missing_hole",
    "mouse_bite",
    "open_circuit",
    "short",
    "spur",
    "spurious_copper",
]

# ── Confidence buckets ────────────────────────────────────────────────────────
BUCKETS = [
    (0.01, 0.25,  "0.01–0.25  (very low — almost certainly noise)"),
    (0.25, 0.45,  "0.25–0.45  (low  — likely false positives, fixable by threshold)"),
    (0.45, 0.60,  "0.45–0.60  (medium — borderline, inspect visually)"),
    (0.60, 0.75,  "0.60–0.75  (high — probably real defects)"),
    (0.75, 1.01,  "0.75–1.00  (very high — model is confident)"),
]


def bucket_label(conf: float) -> str:
    for lo, hi, label in BUCKETS:
        if lo <= conf < hi:
            return label
    return "unknown"


def run(source: str, weights: str):
    source_path = Path(source)
    if not source_path.exists():
        print(f"[ERROR] Source path not found: {source_path}")
        return

    print(f"\n{'='*60}")
    print(f"  PCB Defect Diagnostic")
    print(f"  Model  : {weights}")
    print(f"  Source : {source_path}")
    print(f"{'='*60}\n")

    model = YOLO(weights)

    # Run at conf=0.01 so we see everything the model outputs
    results = model.predict(source=str(source_path), conf=0.01, verbose=False)

    all_detections = []
    per_class = defaultdict(list)
    per_bucket = defaultdict(list)

    for r in results:
        img_name = Path(r.path).name if hasattr(r, "path") else "unknown"
        for box in r.boxes:
            conf     = float(box.conf)
            cls_id   = int(box.cls)
            cls_name = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else str(cls_id)
            label    = bucket_label(conf)

            det = {
                "image":    img_name,
                "class_id": cls_id,
                "class":    cls_name,
                "conf":     round(conf, 4),
                "bucket":   label,
            }
            all_detections.append(det)
            per_class[cls_name].append(conf)
            per_bucket[label].append(conf)

            print(f"  {img_name:<30}  class={cls_name:<18}  conf={conf:.3f}  [{label.split()[0]}]")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  SUMMARY  ({len(all_detections)} total detections across all images)")
    print(f"{'='*60}\n")

    print("  By confidence bucket:")
    for lo, hi, label in BUCKETS:
        dets = per_bucket.get(label, [])
        bar  = "█" * len(dets)
        print(f"    {label}  →  {len(dets):>4} detections  {bar}")

    print("\n  By class:")
    for cls_name in CLASS_NAMES:
        confs = per_class.get(cls_name, [])
        if confs:
            avg = sum(confs) / len(confs)
            print(f"    {cls_name:<18}  {len(confs):>4} detections  avg_conf={avg:.3f}")

    # ── Diagnosis ─────────────────────────────────────────────────────────────
    low_count  = len(per_bucket.get("0.25–0.45  (low  — likely false positives, fixable by threshold)", []))
    high_count = len([d for d in all_detections if d["conf"] >= 0.70])
    total      = len(all_detections)

    print(f"\n{'='*60}")
    print("  DIAGNOSIS")
    print(f"{'='*60}")
    if total == 0:
        print("  No detections at all — model may not be loading correctly.")
    elif total > 0 and high_count / total > 0.5:
        print("  ⚠️  >50% of detections have conf ≥ 0.70.")
        print("      The model is genuinely confused by real PCB images.")
        print("      Recommended fix: FINE-TUNE on real PCB images.")
    elif low_count / max(total, 1) > 0.5:
        print("  ✅ >50% of detections are in the 0.25–0.45 range.")
        print("      False positives are low-confidence noise.")
        print("      Recommended fix: RAISE confidence threshold (e.g. to 0.45–0.55).")
    else:
        print("  Mixed distribution. Inspect visually and consider both")
        print("  threshold tuning AND selective fine-tuning.")

    # ── Save full results to JSON ─────────────────────────────────────────────
    out_path = Path("diagnose_results.json")
    with open(out_path, "w") as f:
        json.dump(all_detections, f, indent=2)
    print(f"\n  Full results saved to: {out_path.resolve()}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PCB false-positive diagnostic")
    parser.add_argument(
        "--source", required=True,
        help="Path to a folder of real PCB images (or a single image)"
    )
    parser.add_argument(
        "--weights", default="models/best.pt",
        help="Path to model weights (default: models/best.pt)"
    )
    args = parser.parse_args()
    run(args.source, args.weights)
