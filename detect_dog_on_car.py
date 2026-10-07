#!/usr/bin/env python3
"""
detect_dog_on_car.py

ESP32-CAM — Simple DOG detection
================================
- Sirf DOG detect (car/person ignore for trigger)
- Green box + accuracy % dog ke upar
- Dog detect hote hi Flash + Relay ON (GPIO12)
- No dog → Flash + Relay OFF

Usage:
  python detect_dog_on_car.py --esp32 172.20.10.9
  python detect_dog_on_car.py --esp32 172.20.10.9 --conf 0.25
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2
import requests
from ultralytics import YOLO

DOG_ID = 16
DEFAULT_CONF = 0.25  # low so dog miss kam ho

GREEN = (0, 255, 0)
RED = (0, 0, 255)


def resolve_weights(path: str) -> Path:
    root = Path(__file__).resolve().parent
    for c in (Path(path) if path else None, root / (path or ""), root / "yolov8n.pt"):
        if c and c.exists():
            return c.resolve()
    raise FileNotFoundError("yolov8n.pt project folder me rakho")


def load_model(weights: Path) -> YOLO:
    print(f"[MODEL] Loading {weights} ...")
    model = YOLO(str(weights))
    names = model.names or {}
    for i, n in names.items():
        if str(n).lower() == "dog":
            print(f"[MODEL] dog class OK id={i}")
            break
    print("[MODEL] Ready — DOG ONLY mode")
    return model


def detect_dogs(model: YOLO, frame, conf: float, imgsz: int):
    """Sirf dog class. Raw BGR frame — extra preprocess mat karo."""
    return model.predict(
        source=frame,
        conf=conf,
        iou=0.45,
        imgsz=imgsz,
        classes=[DOG_ID],
        verbose=False,
        max_det=15,
    )[0]


def draw_dogs(frame, results):
    """Green box + accuracy har dog pe. Return (found, best_conf)."""
    found = False
    best = 0.0
    if results.boxes is None or len(results.boxes) == 0:
        return False, 0.0

    for box in results.boxes:
        score = float(box.conf[0])
        cls_id = int(box.cls[0])
        if cls_id != DOG_ID:
            continue

        found = True
        best = max(best, score)
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].cpu().numpy()]

        # Green box
        cv2.rectangle(frame, (x1, y1), (x2, y2), GREEN, 3)

        # Accuracy label upar
        label = f"DOG {score * 100:.0f}%"
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale, thickness = 0.7, 2
        (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
        ty = max(0, y1 - th - 8)
        cv2.rectangle(frame, (x1, ty), (x1 + tw + 8, ty + th + 8), GREEN, -1)
        cv2.putText(frame, label, (x1 + 4, ty + th + 2), font, scale, (0, 0, 0), thickness)

    return found, best


def set_relay(url: str, on: bool, cur: bool) -> bool:
    if not url or on == cur:
        return cur
    try:
        r = requests.get(f"{url}?state={'on' if on else 'off'}", timeout=2)
        if r.status_code == 200:
            print("Dog Detected - Relay ON" if on else "No Dog - Relay OFF")
            return on
        print(f"[RELAY] HTTP {r.status_code}")
    except Exception as e:
        print(f"[RELAY] {e}")
    return cur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--esp32", default="172.20.10.9")
    ap.add_argument("--weights", default="yolov8n.pt")
    ap.add_argument("--conf", type=float, default=DEFAULT_CONF, help="default 0.25")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--image", default="", help="optional still image test")
    args = ap.parse_args()

    model = load_model(resolve_weights(args.weights))

    # Still image test
    if args.image:
        img = Path(args.image)
        frame = cv2.imread(str(img))
        if frame is None:
            print(f"[ERROR] image nahi mili: {img}")
            return
        res = detect_dogs(model, frame, args.conf, args.imgsz)
        found, best = draw_dogs(frame, res)
        print("Dog Detected - Relay ON" if found else "No Dog - Relay OFF")
        if found:
            print(f"[ACCURACY] {best * 100:.1f}%")
        out = img.with_name(img.stem + "_detected.jpg")
        cv2.imwrite(str(out), frame)
        print(f"[SAVE] {out}")
        cv2.imshow("DOG", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return

    # Live ESP32 stream
    ip = args.esp32.strip()
    stream = f"http://{ip}:81/stream"
    relay = f"http://{ip}/relay"
    print("==================================================")
    print("  DOG detect → green box + % → Flash + Relay ON")
    print(f"  Stream: {stream}")
    print(f"  Conf  : {args.conf}")
    print("==================================================")

    cap = cv2.VideoCapture(stream)
    if not cap.isOpened():
        print("[ERROR] Stream open nahi hua. ESP32 IP / WiFi check karo.")
        return

    relay_on = False
    try:
        requests.get(f"{relay}?state=off", timeout=2)
        print("No Dog - Relay OFF")
    except Exception as e:
        print(f"[RELAY] init fail: {e}")

    print("[INFO] Press 'q' to quit\n")
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            time.sleep(0.25)
            cap.release()
            cap = cv2.VideoCapture(stream)
            continue

        res = detect_dogs(model, frame, args.conf, args.imgsz)
        found, best = draw_dogs(frame, res)

        # Dog hote hi turant ON, warna OFF
        if found:
            relay_on = set_relay(relay, True, relay_on)
            status = f"Dog Detected - Relay ON  ({best * 100:.0f}%)"
            color = RED
        else:
            relay_on = set_relay(relay, False, relay_on)
            status = "No Dog - Relay OFF"
            color = GREEN

        cv2.putText(frame, status, (12, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.imshow("ESP32 DOG Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    set_relay(relay, False, True)
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
