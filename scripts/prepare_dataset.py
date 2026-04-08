"""
scripts/prepare_dataset.py
--------------------------
Downloads the DeepPCB dataset from GitHub and converts it to
YOLO format (txt annotations + train/val/test splits).

Usage:
    python scripts/prepare_dataset.py

Output structure:
    data/splits/
        train/images/  train/labels/
        val/images/    val/labels/
        test/images/   test/labels/
"""

import os
import shutil
import random
import subprocess
from pathlib import Path

import cv2
import yaml

# ── Config ────────────────────────────────────────────────────────────────────
REPO_URL   = "https://github.com/tangsanli5201/DeepPCB.git"
RAW_DIR    = Path("data/raw/DeepPCB")
SPLITS_DIR = Path("data/splits")
SEED       = 42
TRAIN_FRAC = 0.75
VAL_FRAC   = 0.15
# remainder → test

CLASS_MAP = {
    "1": 0,  # missing_hole
    "2": 1,  # mouse_bite
    "3": 2,  # open_circuit
    "4": 3,  # short
    "5": 4,  # spur
    "6": 5,  # spurious_copper
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def clone_dataset():
    if RAW_DIR.exists():
        print(f"[INFO] Dataset already exists at {RAW_DIR}, skipping clone.")
        return
    print("[INFO] Cloning DeepPCB dataset (this may take a minute)...")
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(RAW_DIR)], check=True)
    print("[INFO] Clone complete.")


def parse_annotation(ann_path: Path, img_w: int, img_h: int) -> list[str]:
    """
    DeepPCB annotation format per line:
        x1 y1 x2 y2 class_id
    Convert to YOLO normalised format:
        class_id cx cy w h   (all 0-1)
    """
    lines = []
    for raw in ann_path.read_text().strip().splitlines():
        parts = raw.strip().split()
        if len(parts) != 5:
            continue
        x1, y1, x2, y2, cls = parts
        x1, y1, x2, y2 = map(float, [x1, y1, x2, y2])
        cls_id = CLASS_MAP.get(cls, None)
        if cls_id is None:
            continue
        cx = ((x1 + x2) / 2) / img_w
        cy = ((y1 + y2) / 2) / img_h
        w  = (x2 - x1) / img_w
        h  = (y2 - y1) / img_h
        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    return lines


def collect_samples() -> list[tuple[Path, Path]]:
    """
    Return list of (image_path, annotation_path) pairs.

    DeepPCB actual layout:
        PCBData/
          groupXXXXX/
            XXXXX/          <- *_test.jpg images live here
            XXXXX_not/      <- annotation .txt files live here
                               (named XXXXXXX.txt, no _test/_temp suffix)
    """
    samples = []
    pcb_data = RAW_DIR / "PCBData"
    if not pcb_data.exists():
        raise FileNotFoundError(f"Expected {pcb_data} — check the repo structure.")

    for group_dir in sorted(pcb_data.iterdir()):
        if not group_dir.is_dir():
            continue
        for img_dir in sorted(group_dir.iterdir()):
            # Skip the *_not annotation folders; only process image folders
            if not img_dir.is_dir() or img_dir.name.endswith("_not"):
                continue
            # The sibling annotation directory is named <img_dir.name>_not
            ann_dir = img_dir.parent / (img_dir.name + "_not")
            if not ann_dir.is_dir():
                continue
            for img_file in sorted(img_dir.glob("*_test.jpg")):
                # Annotation filename: stem without _test suffix + .txt
                base = img_file.stem.replace("_test", "")
                ann_file = ann_dir / (base + ".txt")
                if ann_file.exists():
                    samples.append((img_file, ann_file))

    print(f"[INFO] Found {len(samples)} annotated samples.")
    return samples


def make_splits(samples):
    random.seed(SEED)
    random.shuffle(samples)
    n = len(samples)
    n_train = int(n * TRAIN_FRAC)
    n_val   = int(n * VAL_FRAC)
    return {
        "train": samples[:n_train],
        "val":   samples[n_train:n_train + n_val],
        "test":  samples[n_train + n_val:],
    }


def write_split(split_name: str, samples: list):
    img_dir = SPLITS_DIR / split_name / "images"
    lbl_dir = SPLITS_DIR / split_name / "labels"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    skipped = 0
    for img_path, ann_path in samples:
        img = cv2.imread(str(img_path))
        if img is None:
            skipped += 1
            continue
        h, w = img.shape[:2]

        yolo_lines = parse_annotation(ann_path, w, h)
        if not yolo_lines:          # skip unannotated
            skipped += 1
            continue

        dest_img = img_dir / img_path.name
        dest_lbl = lbl_dir / (img_path.stem + ".txt")

        shutil.copy(img_path, dest_img)
        dest_lbl.write_text("\n".join(yolo_lines))

    kept = len(samples) - skipped
    print(f"  [{split_name}] {kept} samples written, {skipped} skipped.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    clone_dataset()

    samples = collect_samples()
    if not samples:
        print("[ERROR] No samples found. Check dataset structure.")
        return

    splits = make_splits(samples)
    for name, data in splits.items():
        print(f"[INFO] Writing {name} split ({len(data)} samples)...")
        write_split(name, data)

    # Confirm dataset.yaml path is correct
    cfg = Path("configs/dataset.yaml")
    print(f"\n[DONE] Dataset ready at {SPLITS_DIR}/")
    print(f"       Update 'path' in {cfg} if you run training from a different directory.")

    # Print class distribution
    for split_name in ["train", "val", "test"]:
        lbl_dir = SPLITS_DIR / split_name / "labels"
        count = len(list(lbl_dir.glob("*.txt")))
        print(f"       {split_name}: {count} labeled images")


if __name__ == "__main__":
    main()
