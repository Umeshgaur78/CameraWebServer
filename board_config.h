#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

//
// WARNING!!! PSRAM IC required for UXGA resolution and high JPEG quality
//            Ensure ESP32 Wrover Module or other board with PSRAM is selected
//            Partial images will be transmitted if image exceeds buffer size
//
//            You must select partition scheme from the board menu that has at least 3MB APP space.

// ===================
// Select camera model
// ===================
//#define CAMERA_MODEL_WROVER_KIT // Has PSRAM
//#define CAMERA_MODEL_ESP_EYE  // Has PSRAM
//#define CAMERA_MODEL_ESP32S3_EYE // Has PSRAM
//#define CAMERA_MODEL_M5STACK_PSRAM // Has PSRAM
//#define CAMERA_MODEL_M5STACK_V2_PSRAM // M5Camera version B Has PSRAM
//#define CAMERA_MODEL_M5STACK_WIDE // Has PSRAM
//#define CAMERA_MODEL_M5STACK_ESP32CAM // No PSRAM
//#define CAMERA_MODEL_M5STACK_UNITCAM // No PSRAM
//#define CAMERA_MODEL_M5STACK_CAMS3_UNIT  // Has PSRAM
#define CAMERA_MODEL_AI_THINKER // Has PSRAM
//#define CAMERA_MODEL_TTGO_T_JOURNAL // No PSRAM
//#define CAMERA_MODEL_XIAO_ESP32S3 // Has PSRAM
// ** Espressif Internal Boards **
//#define CAMERA_MODEL_ESP32_CAM_BOARD
//#define CAMERA_MODEL_ESP32S2_CAM_BOARD
//#define CAMERA_MODEL_ESP32S3_CAM_LCD
//#define CAMERA_MODEL_DFRobot_FireBeetle2_ESP32S3 // Has PSRAM
//#define CAMERA_MODEL_DFRobot_Romeo_ESP32S3 // Has PSRAM
// ===================
// Relay GPIO Pin Setup
// ===================
// Relay IN1 soldered to this GPIO (AI-Thinker header IO12)
#define RELAY_GPIO_NUM     12
#define RELAY_DEBOUNCE_MS  300   // Fast response; still avoids relay chatter
// HW-383 / most optocoupler relay modules: IN LOW = ON, IN HIGH = OFF
#define RELAY_ACTIVE_LOW   1
#if RELAY_ACTIVE_LOW
  #define RELAY_PIN_ON     LOW
  #define RELAY_PIN_OFF    HIGH
#else
  #define RELAY_PIN_ON     HIGH
  #define RELAY_PIN_OFF    LOW
#endif

// Detection Thresholds
#define DOG_CONFIDENCE_THRESHOLD   0.55f   // 55% confidence for dog
#define CAR_CONFIDENCE_THRESHOLD   0.55f   // 55% confidence for car
#define OVERLAP_THRESHOLD          0.25f   // Min overlap ratio

// TFLite Arena Size (bytes) — 200KB in internal RAM
#define TFLITE_ARENA_SIZE  (200 * 1024)

// Input image size for the TFLite model
#define MODEL_INPUT_WIDTH   96
#define MODEL_INPUT_HEIGHT  96

#include "camera_pins.h"

#endif  // BOARD_CONFIG_H
