"""
scripts/infer.py
----------------
Run inference on a single image or a directory of images.
Saves annotated output images with bounding boxes.

Usage:
    # Single image
    python scripts/infer.py --weights runs/pcb_defect_v1/weights/best.pt --source path/to/image.jpg

    # Directory of images
    python scripts/infer.py --weights runs/pcb_defect_v1/weights/best.pt --source path/to/images/

    # Show live window (requires display)
    python scripts/infer.py --weights best.pt --source image.jpg --show
"""

import argparse
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

# Colour per class (BGR)
COLORS = {
    "missing_hole":    (0,   0,   255),
    "mouse_bite":      (0,   165, 255),
    "open_circuit":    (0,   255, 255),
    "short":           (0,   255, 0  ),
    "spur":            (255, 0,   255),
    "spurious_copper": (255, 0,   0  ),
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights",  required=True, help="Path to best.pt")
    parser.add_argument("--source",   required=True, help="Image file or directory")
    parser.add_argument("--conf",     type=float, default=0.25)
    parser.add_argument("--iou",      type=float, default=0.45)
    parser.add_argument("--imgsz",    type=int,   default=640)
    parser.add_argument("--device",   default="cpu")
    parser.add_argument("--save-dir", default="runs/inference")
    parser.add_argument("--show",     action="store_true", help="Display results window")
    return parser.parse_args()


def print_detections(results):
    """Pretty-print detection results for each image."""
    for r in results:
        path = Path(r.path).name
        boxes = r.boxes
        if boxes is None or len(boxes) == 0:
            print(f"  [{path}] No defects detected ✅")
            continue

        print(f"  [{path}] {len(boxes)} defect(s) found:")
        for box in boxes:
            cls_id = int(box.cls.item())
            conf   = box.conf.item()
            xyxy   = box.xyxy[0].tolist()
            name   = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else str(cls_id)
            print(f"    • {name:<20s}  conf={conf:.2f}  bbox=[{xyxy[0]:.0f},{xyxy[1]:.0f},{xyxy[2]:.0f},{xyxy[3]:.0f}]")


def main():
    args = parse_args()

    model = YOLO(args.weights)

    print(f"[INFO] Running inference on: {args.source}")
    results = model.predict(
        source=args.source,
        conf=args.conf,
        iou=args.iou,
        imgsz=args.imgsz,
        device=args.device,
        save=True,
        save_txt=True,
        project=args.save_dir,
        name="predict",
        show=args.show,
        line_width=2,
        verbose=False,
    )

    print("\n[RESULTS]")
    print_detections(results)

    print(f"\n[INFO] Annotated images saved to: {args.save_dir}/predict/")


if __name__ == "__main__":
    main()
