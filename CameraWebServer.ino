/**
 * CameraWebServer.ino
 *
 * ESP32-CAM — Dog Detection
 * - Web UI / phone app (optional)
 * - AUTO: every few sec capture → alert server /detect
 *   → Expo push + ntfy (works even if phone app is background/closed)
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include "img_converters.h"
#include "board_config.h"

#ifndef LED_GPIO_NUM
#define LED_GPIO_NUM 4
#endif

// ===========================
// WiFi — iPhone hotspot (2.4 GHz)
// Maximize Compatibility = ON
// ===========================
const char *ssid = "YOUR_WIFI_SSID";
const char *password = "YOUR_WIFI_PASSWORD";

// ===========================
// Alert server (background alerts)
// Railway Live Server: https://esp32-dog-detector-production.up.railway.app
// ===========================
const char *ALERT_SERVER_URL = "https://esp32-dog-detector-production.up.railway.app";
const char *ALERT_SECRET = "YOUR_ALERT_SECRET";
// Free phone alerts (install ntfy app → subscribe to this topic)
const char *NTFY_TOPIC = "YOUR_NTFY_TOPIC";

#define AUTO_DETECT_INTERVAL_MS  6000
#define AUTO_DOG_STREAK_NEED     2
#define AUTO_HOLD_MS             8000
#define AUTO_JPEG_QUALITY        12

void startCameraServer();
void setupLedFlash();
void applyDogAlert(bool on);
bool cameraStreamBusy();

static int dogStreak = 0;
static bool autoAlertOn = false;
static unsigned long holdUntil = 0;
static unsigned long lastDetectMs = 0;
static int captureFailStreak = 0;

static bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  // RGB565 format — frame2jpg converts to JPEG before sending
  config.pixel_format = PIXFORMAT_RGB565;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 10;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;

  if (psramFound()) {
    config.fb_count = 2;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_LATEST;
    config.frame_size = FRAMESIZE_VGA;
    Serial.println("[Camera] PSRAM OK — VGA RGB565");
  } else {
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
    Serial.println("[Camera] no PSRAM — QVGA RGB565");
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[ERROR] Camera init FAILED: 0x%x\n", err);
    return false;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s) {
    if (s->id.PID == OV3660_PID) {
      s->set_vflip(s, 1);
      s->set_brightness(s, 1);
      s->set_saturation(s, -2);
    }
  }

  for (int i = 0; i < 5; i++) {
    camera_fb_t *warm = esp_camera_fb_get();
    if (warm) {
      Serial.printf("[Camera] warm frame %d ok (%u bytes)\n", i + 1, (unsigned)warm->len);
      esp_camera_fb_return(warm);
    } else {
      Serial.printf("[Camera] warm frame %d FAIL\n", i + 1);
    }
    delay(80);
  }

  Serial.println("[Camera] OK");
  return true;
}

static bool connectWifi() {
  WiFi.disconnect(true);
  delay(300);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);

  Serial.println("[WiFi] Scanning...");
  int n = WiFi.scanNetworks();
  Serial.printf("[WiFi] Found %d networks:\n", n);

  String bestSsid = "";
  int bestRssi = -999;
  for (int i = 0; i < n; i++) {
    String name = WiFi.SSID(i);
    Serial.printf("  - \"%s\"  (%d dBm)\n", name.c_str(), WiFi.RSSI(i));
    String lower = name;
    lower.toLowerCase();
    if (lower.indexOf("umesh") >= 0 && lower.indexOf("iphone") >= 0) {
      if (WiFi.RSSI(i) > bestRssi) {
        bestRssi = WiFi.RSSI(i);
        bestSsid = name;
      }
    }
  }

  String useSsid = bestSsid.length() > 0 ? bestSsid : String(ssid);
  Serial.printf("[WiFi] Connecting to \"%s\"...\n", useSsid.c_str());
  WiFi.begin(useSsid.c_str(), password);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 25000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  return WiFi.status() == WL_CONNECTED;
}

static void notifyNtfy(const char *body) {
  if (!NTFY_TOPIC || !NTFY_TOPIC[0]) return;
  WiFiClientSecure client;
  client.setInsecure();
  HTTPClient http;
  String url = String("https://ntfy.sh/") + NTFY_TOPIC;
  if (!http.begin(client, url)) return;
  http.addHeader("Title", "Dog Alert");
  http.addHeader("Priority", "high");
  http.addHeader("Tags", "dog,warning");
  int code = http.POST((uint8_t *)body, strlen(body));
  Serial.printf("[ntfy] HTTP %d\n", code);
  http.end();
}

static bool postFrameForDetect(uint8_t *jpg, size_t len, float *outScore) {
  if (!ALERT_SERVER_URL || !ALERT_SERVER_URL[0]) return false;
  if (outScore) *outScore = 0;

  String url = String(ALERT_SERVER_URL);
  while (url.endsWith("/")) url.remove(url.length() - 1);
  url += "/detect";

  HTTPClient http;
  http.setTimeout(15000);
  bool isHttps = url.startsWith("https://");
  WiFiClientSecure secureClient;
  WiFiClient plainClient;
  bool began = false;

  if (isHttps) {
    secureClient.setInsecure();
    secureClient.setTimeout(12);
    began = http.begin(secureClient, url);
  } else {
    plainClient.setTimeout(12);
    began = http.begin(plainClient, url);
  }
  if (!began) {
    Serial.println("[Auto] http.begin failed");
    return false;
  }

  http.setReuse(false);
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("x-alert-secret", ALERT_SECRET);
  http.addHeader("Connection", "close");
  int code = http.POST(jpg, len);
  String body = http.getString();
  if (code <= 0) {
    Serial.printf("[Auto] /detect FAIL code=%d err=%s url=%s\n",
                  code, http.errorToString(code).c_str(), url.c_str());
  } else {
    Serial.printf("[Auto] /detect HTTP %d %s\n", code, body.c_str());
  }
  http.end();
  if (isHttps) {
    secureClient.stop();
  } else {
    plainClient.stop();
  }
  if (code != 200) return false;

  bool dog = body.indexOf("\"dog\":true") >= 0 || body.indexOf("\"dog\": true") >= 0;
  if (outScore) {
    int p = body.indexOf("\"score\":");
    if (p >= 0) *outScore = body.substring(p + 8).toFloat();
  }
  return dog;
}

static void runAutoDetectOnce() {
  if (!ALERT_SERVER_URL || !ALERT_SERVER_URL[0]) return;
  if (WiFi.status() != WL_CONNECTED) return;

  if (cameraStreamBusy()) {
    Serial.println("[Auto] skip — Live/stream open. Close Live tab.");
    return;
  }

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    delay(30);
    fb = esp_camera_fb_get();
  }
  if (!fb) {
    captureFailStreak++;
    Serial.printf("[Auto] capture fail (%d)\n", captureFailStreak);
    return;
  }
  captureFailStreak = 0;

  bool dog = false;
  float score = 0;
  if (fb->format == PIXFORMAT_JPEG && fb->len > 100) {
    dog = postFrameForDetect(fb->buf, fb->len, &score);
  } else {
    uint8_t *jpg = nullptr;
    size_t jpgLen = 0;
    if (frame2jpg(fb, AUTO_JPEG_QUALITY, &jpg, &jpgLen) && jpg && jpgLen) {
      dog = postFrameForDetect(jpg, jpgLen, &score);
      free(jpg);
    } else {
      Serial.println("[Auto] jpeg encode fail");
    }
  }
  esp_camera_fb_return(fb);

  unsigned long now = millis();
  if (dog) dogStreak++;
  else dogStreak = 0;

  if (dogStreak >= AUTO_DOG_STREAK_NEED) {
    holdUntil = now + AUTO_HOLD_MS;
    if (!autoAlertOn) {
      autoAlertOn = true;
      applyDogAlert(true);
      Serial.println("[Auto] DOG ALERT (server push/ntfy)");
    }
  } else if (autoAlertOn && now >= holdUntil) {
    autoAlertOn = false;
    applyDogAlert(false);
  }
}

void setup() {
  // GPIO12 = strapping pin. HIGH at boot → flash/reboot loop (mmu set spam).
  // Keep floating until WiFi/camera ready, then drive relay.
  pinMode(RELAY_GPIO_NUM, INPUT);

  Serial.begin(115200);
  delay(1500);
  Serial.setDebugOutput(false);
  Serial.println();
  Serial.println("=== ESP32-CAM DOG + BACKGROUND ALERT ===");

  initCamera();
  setupLedFlash();

  if (connectWifi()) {
    Serial.println("[WiFi] Connected!");
    Serial.printf("[WiFi] IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("[WiFi] FAILED — Hotspot + Maximize Compatibility ON");
  }

  pinMode(RELAY_GPIO_NUM, OUTPUT);
  digitalWrite(RELAY_GPIO_NUM, RELAY_PIN_OFF);

  startCameraServer();
  digitalWrite(RELAY_GPIO_NUM, RELAY_PIN_OFF);

  Serial.println();
  Serial.println("=== READY ===");
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf(" UI     : http://%s/\n", WiFi.localIP().toString().c_str());
    Serial.printf(" Stream : http://%s:81/stream\n", WiFi.localIP().toString().c_str());
  }
  if (ALERT_SERVER_URL && ALERT_SERVER_URL[0]) {
    Serial.printf(" Auto   : ON → %s/detect\n", ALERT_SERVER_URL);
    Serial.println(" Background alerts: phone app can be closed.");
  } else {
    Serial.println(" Auto   : OFF — set ALERT_SERVER_URL for background alerts");
  }
  Serial.printf(" ntfy   : topic %s\n", NTFY_TOPIC);
}

void loop() {
  unsigned long now = millis();
  if (autoAlertOn && now >= holdUntil && dogStreak < AUTO_DOG_STREAK_NEED) {
    autoAlertOn = false;
    applyDogAlert(false);
  }
  if (now - lastDetectMs >= AUTO_DETECT_INTERVAL_MS) {
    lastDetectMs = now;
    runAutoDetectOnce();
  }
  delay(40);
}
