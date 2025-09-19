# LAB2 — ESP32 MicroPython Web Server (LED + DHT22 + HC‑SR04 + I²C LCD)

This project hosts a tiny web app on the ESP32 to:
- Toggle the onboard LED (GPIO2)
- Show live sensor values (DHT22 temperature/humidity, HC‑SR04 distance)
- Display **Distance / Temperature / Custom Text** on a 16×2 I²C LCD

> Matches the lab requirements for README, wiring diagram/photo, setup and usage instructions.


## Parts
- ESP32 Dev Board (MicroPython)
- DHT22 (AM2302)
- HC‑SR04 ultrasonic sensor
- 16×2 LCD with I²C backpack (address `0x27` default)
- Breadboard + jumper wires



## Power the board and open the **REPL** to see logs.

> Wi‑Fi credentials are set inside `main.py`:  
> `ssid = 'Robotic WIFI'`, `password = 'rbtWIFI@2025'`  
> Change to your network if needed.


## Run
- The script auto‑connects to Wi‑Fi and starts a web server on port 80.
- Watch the REPL for the **ESP32 IP address** (e.g., `192.168.1.123`).


## Usage (Web App)
Open a browser to `http://<ESP32_IP>/`:

- **LED ON / OFF** — toggles GPIO2.
- **Show Distance** — LCD shows live distance on the first line every ~2s.
- **Show Temp** — LCD shows the temperature on the second line every ~2s.
- **Textbox → LCD** — type any text and press **Send**. If >16 chars, it scrolls.


