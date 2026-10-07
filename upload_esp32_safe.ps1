# Safe ESP32-CAM upload (fixes MD5 / fast-reflash fail)
# 1) Close Arduino Serial Monitor
# 2) Disconnect relay VCC if possible
# 3) Run:  powershell -ExecutionPolicy Bypass -File upload_esp32_safe.ps1

$ErrorActionPreference = "Stop"
$esp = "C:\Users\umesh\AppData\Local\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe"
$build = "C:\Users\umesh\AppData\Local\arduino\sketches\22A5CDE10AC98D7D2C0E87D293513E6F"
$boot0 = "C:\Users\umesh\AppData\Local\Arduino15\packages\esp32\hardware\esp32\3.3.11\tools\partitions\boot_app0.bin"

# Prefer COM8 if present, else COM7
$ports = [System.IO.Ports.SerialPort]::GetPortNames()
$port = $null
if ($ports -contains "COM8") { $port = "COM8" }
elseif ($ports -contains "COM7") { $port = "COM7" }
else { throw "No COM7/COM8 found. Ports: $($ports -join ', ')" }

Write-Host "Using $port (available: $($ports -join ', '))"
Write-Host "Erase..."
& $esp --chip esp32 --port $port --baud 115200 --before default-reset --after hard-reset erase-flash
Write-Host "Flash (115200, --force)..."
& $esp --chip esp32 --port $port --baud 115200 --before default-reset --after hard-reset write-flash --flash-mode dio --flash-freq 40m --flash-size detect --force `
  0x1000 "$build\CameraWebServer.ino.bootloader.bin" `
  0x8000 "$build\CameraWebServer.ino.partitions.bin" `
  0xe000 $boot0 `
  0x10000 "$build\CameraWebServer.ino.bin"

if ($LASTEXITCODE -eq 0) {
  Write-Host "SUCCESS - power cycle board, then open Serial Monitor 115200"
} else {
  Write-Host "FAILED exit=$LASTEXITCODE - close Serial Monitor and retry"
  exit $LASTEXITCODE
}
