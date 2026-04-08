"""
scripts/evaluate.py
-------------------
Evaluates a trained YOLOv8 model on the test split.
Prints per-class metrics and saves a confusion matrix + PR curves.

Usage:
    python scripts/evaluate.py --weights runs/pcb_defect_v1/weights/best.pt
    python scripts/evaluate.py --weights runs/pcb_defect_v1/weights/best.pt --split val
"""

import argparse
from pathlib import Path

import yaml
from ultralytics import YOLO


CLASS_NAMES = [
    "missing_hole",
    "mouse_bite",
    "open_circuit",
    "short",
    "spur",
    "spurious_copper",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True, help="Path to best.pt")
    parser.add_argument("--data",    default="configs/dataset.yaml")
    parser.add_argument("--split",   default="test", choices=["train", "val", "test"])
    parser.add_argument("--imgsz",   type=int, default=640)
    parser.add_argument("--conf",    type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--iou",     type=float, default=0.5,  help="IoU threshold for mAP")
    parser.add_argument("--device",  default="cpu")
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"[INFO] Loading model from: {args.weights}")
    model = YOLO(args.weights)

    print(f"[INFO] Evaluating on [{args.split}] split...")
    metrics = model.val(
        data=args.data,
        split=args.split,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        device=args.device,
        plots=True,             # saves confusion matrix, PR curve, F1 curve
        save_json=True,
        verbose=True,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "="*55)
    print("  EVALUATION RESULTS")
    print("="*55)
    print(f"  mAP@0.50      : {metrics.box.map50:.4f}")
    print(f"  mAP@0.50:0.95 : {metrics.box.map:.4f}")
    print(f"  Precision     : {metrics.box.mp:.4f}")
    print(f"  Recall        : {metrics.box.mr:.4f}")

    print("\n  Per-class mAP@0.50:")
    print("  " + "-"*40)
    for i, cls in enumerate(CLASS_NAMES):
        if i < len(metrics.box.ap50):
            print(f"  {cls:<20s} {metrics.box.ap50[i]:.4f}")

    print("="*55)
    print(f"\n[INFO] Plots saved to: {metrics.save_dir}")


if __name__ == "__main__":
    main()
