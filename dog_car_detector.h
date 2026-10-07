/**
 * dog_car_detector.h
 *
 * Dog-on-Car Detection using Chirale_TensorFlowLite library
 * Library Manager mein: "Chirale_TensorFlowLite" install karo
 *
 * Logic:
 *   1. Camera frame resize → 96x96 RGB
 *   2. TFLite inference → dog + car detect
 *   3. Dog center, Car ke upper 65% mein hai? → RELAY ON
 *   4. Dog hat gaya? → RELAY OFF
 */

#ifndef DOG_CAR_DETECTOR_H
#define DOG_CAR_DETECTOR_H

#include "board_config.h"
#include "model_data.h"

// ─── Chirale_TensorFlowLite Headers ─────────────────────────────────
// Library auto-installed via arduino-cli
// Header name: Chirale_TensorFlowLite.h  (capital F and L)
#include <Chirale_TensorFlowLite.h>
#include <tensorflow/lite/micro/all_ops_resolver.h>
#include <tensorflow/lite/micro/micro_interpreter.h>
#include <tensorflow/lite/schema/schema_generated.h>

// ─── Detection Constants ─────────────────────────────────────────────
#define MAX_DETECTIONS        10
#define CLASS_BACKGROUND       0
#define CLASS_CAR              1
#define CLASS_DOG              2
#define CAR_UPPER_BODY_RATIO   0.65f  // Upar ka 65% = roof + hood area

// ─── Detection Box ───────────────────────────────────────────────────
struct DetectionBox {
  float ymin, xmin, ymax, xmax;
  float score;
  int   classId;
};

// ─── TFLite Globals ──────────────────────────────────────────────────
static const tflite::Model*      s_model      = nullptr;
static tflite::MicroInterpreter* s_interpreter = nullptr;
static TfLiteTensor*             s_input      = nullptr;
static bool                      s_ready      = false;
static bool                      s_relayOn    = false;
static unsigned long             s_lastRelayChangeMs = 0;

// Dynamic Tensor Arena pointer (allocated in PSRAM or Heap to avoid DRAM overflow)
static uint8_t* s_tensor_arena = nullptr;

// ─────────────────────────────────────────────────────────────────────
//  IoU — Intersection over Union
// ─────────────────────────────────────────────────────────────────────
static float computeIoU(const DetectionBox& a, const DetectionBox& b) {
  float iy1 = max(a.ymin, b.ymin);
  float ix1 = max(a.xmin, b.xmin);
  float iy2 = min(a.ymax, b.ymax);
  float ix2 = min(a.xmax, b.xmax);
  if (iy2 <= iy1 || ix2 <= ix1) return 0.0f;
  float inter = (iy2 - iy1) * (ix2 - ix1);
  float aArea = (a.ymax - a.ymin) * (a.xmax - a.xmin);
  float bArea = (b.ymax - b.ymin) * (b.xmax - b.xmin);
  return inter / (aArea + bArea - inter + 1e-6f);
}

// ─────────────────────────────────────────────────────────────────────
//  Dog-on-Car Check
// ─────────────────────────────────────────────────────────────────────
static bool isDogOnCar(const DetectionBox& dog, const DetectionBox& car) {
  float dogCx = (dog.xmin + dog.xmax) / 2.0f;
  float dogCy = (dog.ymin + dog.ymax) / 2.0f;

  // Car ka upper boundary (roof/hood area)
  float carUpperLimit = car.ymin + (car.ymax - car.ymin) * CAR_UPPER_BODY_RATIO;

  bool overCar  = (dogCx >= car.xmin && dogCx <= car.xmax);
  bool onTop    = (dogCy <= carUpperLimit);
  float iou     = computeIoU(dog, car);

  return overCar && onTop && (iou > OVERLAP_THRESHOLD);
}

// ─────────────────────────────────────────────────────────────────────
//  Initialize TFLite
// ─────────────────────────────────────────────────────────────────────
bool detectorInit() {
  Serial.println("[TFLite] Initializing...");

  if (!s_tensor_arena) {
    if (psramFound()) {
      s_tensor_arena = (uint8_t*)ps_malloc(TFLITE_ARENA_SIZE);
      Serial.println("[TFLite] Allocated arena in PSRAM");
    } else {
      s_tensor_arena = (uint8_t*)malloc(TFLITE_ARENA_SIZE);
      Serial.println("[TFLite] Allocated arena in DRAM Heap");
    }
  }
  if (!s_tensor_arena) {
    Serial.println("[TFLite] Memory allocation for arena FAILED!");
    return false;
  }

  s_model = tflite::GetModel(g_model_data);
  if (s_model->version() != TFLITE_SCHEMA_VERSION) {
    Serial.printf("[TFLite] Schema mismatch: got %d, need %d\n",
                  s_model->version(), TFLITE_SCHEMA_VERSION);
    return false;
  }

  static tflite::AllOpsResolver resolver;
  static tflite::MicroInterpreter interp(s_model, resolver,
                                          s_tensor_arena, TFLITE_ARENA_SIZE);
  s_interpreter = &interp;

  if (s_interpreter->AllocateTensors() != kTfLiteOk) {
    Serial.println("[TFLite] AllocateTensors FAILED!");
    Serial.printf("[TFLite] Arena used: %u bytes\n",
                  (unsigned)s_interpreter->arena_used_bytes());
    return false;
  }

  s_input = s_interpreter->input(0);

  Serial.printf("[TFLite] Input: [%d x %d x %d]\n",
                s_input->dims->data[1],
                s_input->dims->data[2],
                s_input->dims->data[3]);
  Serial.printf("[TFLite] Arena used: %u / %u bytes\n",
                (unsigned)s_interpreter->arena_used_bytes(),
                (unsigned)TFLITE_ARENA_SIZE);

  // Relay pin
  pinMode(RELAY_GPIO_NUM, OUTPUT);
  digitalWrite(RELAY_GPIO_NUM, RELAY_PIN_OFF);
  Serial.printf("[Relay] GPIO%d → OFF (active-low)\n", RELAY_GPIO_NUM);

  s_ready = true;
  Serial.println("[TFLite] Ready!");
  return true;
}

// ─────────────────────────────────────────────────────────────────────
//  Frame → TFLite input tensor (RGB565 → 96x96 RGB888)
// ─────────────────────────────────────────────────────────────────────
static void preprocessFrame(camera_fb_t* fb) {
  int   srcW   = fb->width;
  int   srcH   = fb->height;
  float scaleX = (float)srcW / MODEL_INPUT_WIDTH;
  float scaleY = (float)srcH / MODEL_INPUT_HEIGHT;
  uint8_t* dst = s_input->data.uint8;

  for (int y = 0; y < MODEL_INPUT_HEIGHT; y++) {
    for (int x = 0; x < MODEL_INPUT_WIDTH; x++) {
      int sx = (int)(x * scaleX);
      int sy = (int)(y * scaleY);

      int     pi = (sy * srcW + sx) * 2;  // RGB565: 2 bytes/pixel
      uint8_t hi = fb->buf[pi];
      uint8_t lo = fb->buf[pi + 1];

      uint8_t r = (hi & 0xF8);
      uint8_t g = ((hi & 0x07) << 5) | ((lo & 0xE0) >> 3);
      uint8_t b = (lo & 0x1F) << 3;

      int ti = (y * MODEL_INPUT_WIDTH + x) * 3;
      dst[ti + 0] = r;
      dst[ti + 1] = g;
      dst[ti + 2] = b;
    }
  }
}

// ─────────────────────────────────────────────────────────────────────
//  Extract SSD detections from output tensors
//  Standard SSD outputs:
//   [0] boxes   [1,N,4] ymin xmin ymax xmax
//   [1] classes [1,N]
//   [2] scores  [1,N]
//   [3] count   [1]
// ─────────────────────────────────────────────────────────────────────
static void extractDetections(DetectionBox* dogs, int* nDogs,
                               DetectionBox* cars, int* nCars) {
  *nDogs = 0; *nCars = 0;

  TfLiteTensor* outBoxes   = s_interpreter->output(0);
  TfLiteTensor* outClasses = s_interpreter->output(1);
  TfLiteTensor* outScores  = s_interpreter->output(2);
  TfLiteTensor* outCount   = s_interpreter->output(3);

  int count = min((int)outCount->data.f[0], MAX_DETECTIONS);

  for (int i = 0; i < count; i++) {
    float score   = outScores->data.f[i];
    int   classId = (int)outClasses->data.f[i] + 1;  // +1 skip background

    if (classId == CLASS_CAR && score >= CAR_CONFIDENCE_THRESHOLD && *nCars < MAX_DETECTIONS) {
      DetectionBox& b = cars[(*nCars)++];
      b.ymin = outBoxes->data.f[i * 4 + 0];
      b.xmin = outBoxes->data.f[i * 4 + 1];
      b.ymax = outBoxes->data.f[i * 4 + 2];
      b.xmax = outBoxes->data.f[i * 4 + 3];
      b.score = score; b.classId = CLASS_CAR;
      Serial.printf("[Det] CAR   %.0f%%  [%.2f %.2f %.2f %.2f]\n",
                    score*100, b.ymin, b.xmin, b.ymax, b.xmax);
    } else if (classId == CLASS_DOG && score >= DOG_CONFIDENCE_THRESHOLD && *nDogs < MAX_DETECTIONS) {
      DetectionBox& b = dogs[(*nDogs)++];
      b.ymin = outBoxes->data.f[i * 4 + 0];
      b.xmin = outBoxes->data.f[i * 4 + 1];
      b.ymax = outBoxes->data.f[i * 4 + 2];
      b.xmax = outBoxes->data.f[i * 4 + 3];
      b.score = score; b.classId = CLASS_DOG;
      Serial.printf("[Det] DOG   %.0f%%  [%.2f %.2f %.2f %.2f]\n",
                    score*100, b.ymin, b.xmin, b.ymax, b.xmax);
    }
  }
}

// ─────────────────────────────────────────────────────────────────────
//  Main: Run detection on one camera frame
// ─────────────────────────────────────────────────────────────────────
bool detectDogOnCar(camera_fb_t* fb) {
  if (!s_ready || !fb) return false;

  preprocessFrame(fb);

  if (s_interpreter->Invoke() != kTfLiteOk) {
    Serial.println("[TFLite] Invoke FAILED");
    return false;
  }

  DetectionBox dogs[MAX_DETECTIONS], cars[MAX_DETECTIONS];
  int nDogs = 0, nCars = 0;
  extractDetections(dogs, &nDogs, cars, &nCars);
  Serial.printf("[Det] Dogs=%d  Cars=%d\n", nDogs, nCars);

  bool dogOnCar = false;
  for (int d = 0; d < nDogs && !dogOnCar; d++) {
    for (int c = 0; c < nCars && !dogOnCar; c++) {
      if (isDogOnCar(dogs[d], cars[c])) {
        dogOnCar = true;
        Serial.printf("[ALERT] DOG ON CAR! Dog=%.0f%% Car=%.0f%%\n",
                      dogs[d].score * 100, cars[c].score * 100);
      }
    }
  }

  // ── Relay Control (2s debounce — AI logic above is untouched) ─────
  unsigned long now = millis();
  bool debounceOk = (s_lastRelayChangeMs == 0) ||
                    ((now - s_lastRelayChangeMs) >= RELAY_DEBOUNCE_MS);

  if (dogOnCar && !s_relayOn && debounceOk) {
    digitalWrite(RELAY_GPIO_NUM, RELAY_PIN_ON);
    s_relayOn = true;
    s_lastRelayChangeMs = now;
    Serial.println("[RELAY] ► ON  — Dog on car body!");
  } else if (!dogOnCar && s_relayOn && debounceOk) {
    digitalWrite(RELAY_GPIO_NUM, RELAY_PIN_OFF);
    s_relayOn = false;
    s_lastRelayChangeMs = now;
    Serial.println("[RELAY] ■ OFF — Dog left car.");
  }

  return dogOnCar;
}

bool isRelayOn() { return s_relayOn; }

#endif // DOG_CAR_DETECTOR_H
