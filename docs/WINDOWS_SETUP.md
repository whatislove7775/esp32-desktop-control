# Windows setup and verification

This project has **not yet been tested on the maintainer's Windows PC or ESP32 hardware**. The steps below are for local verification.

1. Install Python 3.10+ from python.org.
2. Download the repository and open PowerShell in its root.
3. Run `powershell -ExecutionPolicy Bypass -File scripts/start-windows.ps1`. The script installs Python dependencies, generates a temporary token if needed, and starts the server on localhost.
4. In a second PowerShell window, set `$token = "YOUR_TOKEN_FROM_FIRST_WINDOW"` and run:

```powershell
curl.exe -H "Authorization: Bearer $token" http://127.0.0.1:8765/status
```

5. To allow ESP32 requests, stop the server and start it again with `$env:DESKTOP_CONTROL_HOST="0.0.0.0"` in the same PowerShell session. Restrict Windows Firewall access to your private LAN and never expose this unauthenticated-over-HTTP protocol to public networks. Note: requests have a bearer token but are not encrypted.
6. Edit `esp32/serial_controller.ino` with Wi-Fi credentials, PC LAN IP, and the same token. Upload via Arduino IDE. Do **not** commit your edited credentials.
7. Open the serial monitor at 115200 and try `status`, `play`, `next`, `prev`, and `mute browser.exe` (substitute the real process name). Try WOL only with a MAC address you own.

**Security note:** Token is generated per session unless explicitly supplied. If you restart without setting `DESKTOP_CONTROL_TOKEN`, update the ESP32 token too. Shutdown is disabled by default.

**Scope:** This is a proof of concept, not a completed touchscreen firmware. Do not claim hardware validation before running the tests on actual devices.
