# Custom Dataset: DOG SITTING ON CAR ROOF

This project uses **one AI class only**:

```text
dog_on_roof
```

There is **no** separate car detector and **no** roof geometry in code.
The model learns the visual pattern “dog sitting on a car roof” from your labels.

---

## 1. What you are teaching the model

| Scene | Label? | Effect |
|-------|--------|--------|
| Dog sitting / standing on car roof or hood-top | **YES** — draw one box around that dog-on-roof | Positive |
| Dog on road / ground | **NO** — do not draw a box | Negative (background) |
| Dog beside car | **NO** | Negative |
| Dog under car | **NO** | Negative |
| Empty car / street / people / bikes | **NO** | Negative |
| Dog partially on roof (clearly on top) | **YES** | Positive |

**Critical rule:** Only label the target behavior. Anything unlabeled is treated as “relay must stay OFF”.

---

## 2. How many images you need

| Split | Minimum | Better |
|-------|---------|--------|
| Train positives (`dog_on_roof`) | 150 | 300–500 |
| Train negatives (no labels) | 200 | 400–800 |
| Val positives | 30 | 50–100 |
| Val negatives | 40 | 80–150 |

Capture with the **same ESP32-CAM** (angle, height, lens, VGA) you will use live.

Vary:

- Indian street cars (hatchback, sedan, SUV)
- Day / shade / evening
- Dog breeds and sizes
- Distances and angles
- Partial occlusion

---

## 3. Folder layout (already created)

```text
ml/dataset/
  images/
    train/     ← put .jpg / .png here
    val/
  labels/
    train/     ← YOLO .txt with SAME basename as image
    val/
```

Example:

```text
images/train/img_001.jpg
labels/train/img_001.txt   ← has a box if dog is on roof
images/train/img_002.jpg
labels/train/img_002.txt   ← EMPTY file if no dog-on-roof
```

---

## 4. Label format (YOLOv8)

Each `.txt` line:

```text
0 <x_center> <y_center> <width> <height>
```

- Class id is always `0` (`dog_on_roof`)
- All values are **normalized 0–1** (divide by image width/height)

Example (dog-on-roof box roughly in upper-middle of frame):

```text
0 0.52 0.31 0.18 0.22
```

Empty file = negative image (correct for dog on ground).

---

## 5. Recommended labeling tools

1. **[Label Studio](https://labelstud.io/)** or **[CVAT](https://www.cvat.ai/)**
2. **[Roboflow](https://roboflow.com/)** (export YOLOv8)
3. **[makesense.ai](https://www.makesense.ai/)** (browser, free)

Export / save as **YOLOv8** TXT + keep the folder layout above.

---

## 6. How to collect frames from your ESP32-CAM

With the camera streaming:

```bash
python ml/capture_frames.py --esp32 192.168.x.x --out ml/dataset/images/train --every 15
```

Then move ~20% of images to `images/val` and create matching label files.

---

## 7. Train

```bash
cd ml
pip install -r requirements.txt
python train_dog_on_roof.py
```

Best weights are saved to:

```text
ml/runs/detect/dog_on_roof/weights/best.pt
```

---

## 8. Run live detection (controls relay)

```bash
python detect_dog_on_roof.py --esp32 192.168.x.x --weights runs/detect/dog_on_roof/weights/best.pt
```

Relay ON **only** when class `dog_on_roof` is detected above confidence threshold.

---

## 9. Why this beats car+dog+roof math

Geometry fails when COCO misses Indian cars or boxes jitter.
A single custom class encodes the full concept in the weights:
**if it looks like “dog on car roof” → fire; otherwise stay off.**
