# ESP32 Desktop Control

An experimental, MIT-licensed starter kit for controlling a Windows PC from an ESP32 over a trusted local network.

**Status:** early prototype. Includes a Python Windows agent, a simple ESP32 Arduino sketch, and unit tests. It is not a finished LilyGO T-Display-Long interface, and hardware integration has not been verified.

## Features
- Read CPU and memory usage (requires optional `psutil`)
- Play/pause, next and previous media using Windows media keys
- Mute/unmute a named Windows application (requires optional `pycaw` and `comtypes`)
- Send Wake-on-LAN magic packets
- Request Windows shutdown (disabled by default)

## Quick start (Windows)
Install Python 3.10+ and run:

```powershell
py -m pip install -r requirements.txt
$env:DESKTOP_CONTROL_TOKEN = "replace-with-a-long-random-secret"
py windows_agent/server.py
```

The server listens on port 8765. Set `DESKTOP_CONTROL_HOST=0.0.0.0` to allow your ESP32 to reach it on your **trusted LAN**. Windows Firewall may require a private-network inbound rule. Never forward this port to the internet.

Try a request (replace token):

```powershell
curl.exe -H "Authorization: Bearer replace-with-a-long-random-secret" http://127.0.0.1:8765/status
```

For ESP32, install the Arduino ESP32 board package, open `esp32/serial_controller.ino`, set Wi-Fi, PC IP and the same token, and upload. Open Serial Monitor at 115200 baud. Enter `status`, `play`, `next`, `prev`, `mute app.exe`, `unmute app.exe`, or `wol AA:BB:CC:DD:EE:FF`. This serial-based sketch demonstrates the protocol; a touchscreen UI is future work.

### Shutdown
Shutdown is disabled by default. Explicitly set `DESKTOP_CONTROL_ALLOW_SHUTDOWN=1` on the Windows PC to enable `POST /shutdown`. A shutdown can cause data loss.

### API
All endpoints require `Authorization: Bearer <token>`.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/status` | CPU/RAM metrics |
| POST | `/media` | JSON: `{"action":"playpause"}` (or `next`, `previous`) |
| POST | `/audio` | JSON: `{"process":"app.exe","mute":true}` |
| POST | `/wol` | JSON: `{"mac":"AA:BB:CC:DD:EE:FF"}` |
| POST | `/shutdown` | Disabled unless explicitly enabled |

The WOL request can also be sent by the ESP32 when the Windows agent is offline; see the sketch's `wol` command.

## Tests
```sh
python -m unittest discover -s tests -v
```

## Roadmap
- LilyGO T-Display-Long touchscreen interface and LVGL integration
- Media metadata and artwork from browser-based players
- Device discovery and safer pairing
- More extensive Windows application audio session support

## Contributing
Bug reports, compatibility reports, and small pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Do not commit credentials or personal data.

## License
MIT. See [LICENSE](LICENSE).