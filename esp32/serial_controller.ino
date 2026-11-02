// Minimal ESP32 serial-to-LAN control example. Not a LilyGO touchscreen firmware.
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiUdp.h>

const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* PC_HOST = "192.168.1.100";
const char* API_TOKEN = "REPLACE_WITH_LONG_RANDOM_TOKEN";
const int PC_PORT = 8765;

void request(const String& path, const String& json, bool post = true) {
  if (WiFi.status() != WL_CONNECTED) { Serial.println("WiFi disconnected"); return; }
  HTTPClient http;
  String url = String("http://") + PC_HOST + ":" + String(PC_PORT) + path;
  http.begin(url);
  http.setTimeout(3000);
  http.addHeader("Authorization", String("Bearer ") + API_TOKEN);
  int code;
  if (post) {
    http.addHeader("Content-Type", "application/json");
    code = http.POST(json);
  } else {
    code = http.GET();
  }
  Serial.printf("HTTP %d: %s\n", code, http.getString().c_str());
  http.end();
}

void wol(String mac) {
  mac.replace(":", "");
  if (mac.length() != 12) { Serial.println("MAC must contain 12 hex digits"); return; }
  uint8_t addr[6];
  for (int i = 0; i < 6; ++i) {
    String part = mac.substring(i * 2, i * 2 + 2);
    for (int j = 0; j < 2; ++j) {
      char c = part[j];
      if (!isxdigit((unsigned char)c)) { Serial.println("Invalid MAC"); return; }
    }
    addr[i] = (uint8_t)strtoul(part.c_str(), nullptr, 16);
  }
  uint8_t packet[102];
  memset(packet, 0xFF, 6);
  for (int i = 0; i < 16; ++i) memcpy(packet + 6 + i * 6, addr, 6);
  WiFiUDP udp;
  udp.begin(0);
  udp.beginPacket(IPAddress(255,255,255,255), 9);
  udp.write(packet, sizeof(packet));
  udp.endPacket();
  udp.stop();
  Serial.println("WOL packet sent");
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting");
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; ++i) {
    delay(500); Serial.print(".");
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? "\nConnected" : "\nWiFi unavailable");
  Serial.println("Commands: status, play, next, prev, mute app.exe, unmute app.exe, wol AA:BB:CC:DD:EE:FF");
}

void loop() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd == "status") request("/status", "", false);
  else if (cmd == "play") request("/media", "{\"action\":\"playpause\"}");
  else if (cmd == "next") request("/media", "{\"action\":\"next\"}");
  else if (cmd == "prev") request("/media", "{\"action\":\"previous\"}");
  else if (cmd.startsWith("mute ") || cmd.startsWith("unmute ")) {
    bool mute = cmd.startsWith("mute ");
    String process = cmd.substring(mute ? 5 : 7);
    process.trim();
    request("/audio", String("{\"process\":\"") + process + "\",\"mute\":" + (mute ? "true" : "false") + "}");
  } else if (cmd.startsWith("wol ")) wol(cmd.substring(4));
  else Serial.println("Unknown command");
}
