#!/usr/bin/env python3
"""
capture_frames.py — Save JPEG frames from ESP32-CAM MJPEG stream for labeling.

Usage:
  python capture_frames.py --esp32 172.20.10.9 --out dataset/images/train --every 15
"""

import argparse
import os
import time
from pathlib import Path

import cv2


def main():
    parser = argparse.ArgumentParser(description="Capture ESP32-CAM frames for dog_on_roof dataset")
    parser.add_argument("--esp32", required=True, help="ESP32-CAM IP address")
    parser.add_argument("--out", default="dataset/images/train", help="Output folder")
    parser.add_argument("--every", type=int, default=15, help="Save every Nth frame")
    parser.add_argument("--max", type=int, default=500, help="Max images to save (0 = unlimited)")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    url = f"http://{args.esp32.strip()}:81/stream"
    print(f"[INFO] Connecting to {url}")
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("[ERROR] Cannot open stream. Is the ESP32 online?")
        return

    n = 0
    saved = 0
    print("[INFO] Press 's' to save now, 'q' to quit. Auto-saves every", args.every, "frames.")

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.3)
            cap = cv2.VideoCapture(url)
            continue

        n += 1
        preview = frame.copy()
        cv2.putText(preview, f"saved={saved} frame={n}", (12, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("capture_frames — dog_on_roof dataset", preview)
        key = cv2.waitKey(1) & 0xFF

        do_save = (key == ord("s")) or (n % args.every == 0)
        if do_save:
            name = out / f"esp32_{int(time.time())}_{saved:04d}.jpg"
            cv2.imwrite(str(name), frame)
            # Create empty label stub (fill in with YOLO tool if positive)
            label_root = Path(str(out).replace("images", "labels"))
            label_root.mkdir(parents=True, exist_ok=True)
            stub = label_root / (name.stem + ".txt")
            if not stub.exists():
                stub.write_text("")
            saved += 1
            print(f"[SAVE] {name}")
            if args.max and saved >= args.max:
                break

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"[DONE] Saved {saved} images → {out}")
    print("Next: label positives only (dog ON roof) using DATASET_GUIDE.md")


if __name__ == "__main__":
    main()
