try:
    import usocket as socket
except:
    import socket

from machine import Pin, SoftI2C, time_pulse_us
from machine_i2c_lcd import I2cLcd
import network
import esp
import gc
import time
import dht
from time import sleep_us

esp.osdebug(None)
gc.collect()

ssid = 'Robotic WIFI'
password = 'rbtWIFI@2025'

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while not station.isconnected():
    pass

print('Connection successful')
print(station.ifconfig())

# --- GPIO, DHT22, Ultrasonic, LCD Setup ---
led = Pin(2, Pin.OUT)

# DHT22
sensor = dht.DHT22(Pin(4))
temperature = "N/A"
humidity = "N/A"

# Ultrasonic
TRIG = Pin(27, Pin.OUT)
ECHO = Pin(26, Pin.IN)
distance = "N/A"

# LCD
I2C_ADDR = 0x27
i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# --- LCD state ---
lcd_mode = None
lcd_text = ""
lcd_scroll_index = 0
last_lcd_update = 0

# --- Helpers ---
def urldecode(s):
    res = ""
    i = 0
    while i < len(s):
        c = s[i]
        if c == '+':
            res += ' '
            i += 1
        elif c == '%' and i + 2 < len(s):
            try:
                res += chr(int(s[i+1:i+3], 16))
                i += 3
            except:
                res += c
                i += 1
        else:
            res += c
            i += 1
    return res

def read_dht():
    global temperature, humidity
    try:
        sensor.measure()
        temperature = "{:.2f}".format(sensor.temperature())
        humidity = "{:.2f}".format(sensor.humidity())
    except OSError:
        temperature = "Error"
        humidity = "Error"

def distance_cm():
    global distance
    TRIG.off()
    sleep_us(5)
    TRIG.on()
    sleep_us(10)
    TRIG.off()

    t = time_pulse_us(ECHO, 1, 30000)  # timeout 30ms
    if t < 0:
        distance = "No Echo"
    else:
        distance = "{:.1f}".format((t * 0.0343) / 2.0)
    return distance

# --- LCD Update ---
def update_lcd_frame():
    global lcd_mode, lcd_text, lcd_scroll_index, last_lcd_update
    now = time.time()

    if lcd_mode == 'dist':
        if now - last_lcd_update >= 2:
            lcd.clear()
            lcd.move_to(0, 0)
            if distance == "No Echo":
                lcd.putstr("Dist: -- cm")
            else:
                lcd.putstr("Dist:{}cm".format(distance))
            last_lcd_update = now

    elif lcd_mode == 'temp':
        if now - last_lcd_update >= 2:
            read_dht()
            lcd.clear()
            lcd.move_to(0, 1)   # second line only
            lcd.putstr("Temp:{}C".format(temperature))
            last_lcd_update = now

    elif lcd_mode == 'text':
        txt = lcd_text or ""
        if len(txt) <= 16:
            lcd.clear()
            lcd.move_to(0, 0)
            lcd.putstr(txt)
        else:
            if lcd_scroll_index > len(txt) - 16:
                lcd_scroll_index = 0
            segment = txt[lcd_scroll_index:lcd_scroll_index + 16]
            lcd.clear()
            lcd.move_to(0, 0)
            lcd.putstr(segment)
            lcd_scroll_index += 1
    # If lcd_mode is None, do nothing

# --- Web Page ---
def web_page():
    html = """<html><head>
    <title>ESP Live Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    html{font-family: Helvetica; text-align: center;}
    h1{color: #0F3376;}
    p{font-size: 1.1rem;}
    .value{font-weight: bold; color: green;}
    button{padding:8px 12px;margin:6px;}
    </style>
    <script>
    async function fetchData(){
        let r = await fetch('/data');
        let j = await r.json();
        document.getElementById("temp").innerHTML = j.temperature + " &deg;C";
        document.getElementById("hum").innerHTML = j.humidity + " %";
        document.getElementById("dist").innerHTML = j.distance + " cm";
        document.getElementById("gpio").innerHTML = j.gpio;
    }
    setInterval(fetchData, 1000);
    </script>
    </head><body onload="fetchData()">
    <h1>ESP Live Sensor Web Server</h1>
    <p>GPIO state: <span id="gpio" class="value">--</span></p>
    <p>Temperature: <span id="temp" class="value">--</span></p>
    <p>Humidity: <span id="hum" class="value">--</span></p>
    <p>Distance: <span id="dist" class="value">--</span></p>

    <p>
      <a href="/?led=on"><button>LED ON</button></a>
      <a href="/?led=off"><button>LED OFF</button></a>
    </p>

    <p>
      <a href="/?lcd=dist"><button>Show Distance</button></a>
      <a href="/?lcd=temp"><button>Show Temp</button></a>
    </p>

    <form action="/" method="get">
      <input type="text" name="lcdtext" placeholder="Enter text for LCD" style="width:200px;">
      <button type="submit">Send</button>
    </form>

    </body></html>"""
    return html

# --- Web Server ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(0.05)
s.bind(('', 80))
s.listen(5)

# --- Main Loop ---
while True:
    read_dht()            # keep DHT fresh
    distance_cm()         # always update global distance (for webpage)
    update_lcd_frame()    # LCD shows only the active mode

    try:
        conn, addr = s.accept()
        request = conn.recv(2048).decode()

        request_line = request.split('\r\n')[0]
        parts = request_line.split()
        path = '/'
        if len(parts) >= 2:
            path = parts[1]

        params = {}
        if path.startswith('/?'):
            qs = path[2:]
            for p in qs.split('&'):
                if '=' in p:
                    k, v = p.split('=', 1)
                    params[k] = urldecode(v)

        if 'led' in params:
            if params['led'] == 'on':
                led.value(1)
            elif params['led'] == 'off':
                led.value(0)

        if 'lcd' in params:
            if params['lcd'] == 'dist':
                lcd_mode = 'dist'
                last_lcd_update = 0
            elif params['lcd'] == 'temp':
                lcd_mode = 'temp'
                last_lcd_update = 0

        if 'lcdtext' in params:
            lcd_text = params['lcdtext']
            lcd_mode = 'text'
            lcd_scroll_index = 0

        if path == '/data':
            state = "ON" if led.value() else "OFF"
            json = '{{"temperature":"{}","humidity":"{}","distance":"{}","gpio":"{}"}}'.format(
                temperature, humidity, distance, state
            )
            conn.sendall('HTTP/1.1 200 OK\r\n'.encode())
            conn.sendall('Content-Type: application/json\r\n'.encode())
            conn.sendall('Connection: close\r\n\r\n'.encode())
            conn.sendall(json.encode())
        else:
            response = web_page()
            conn.sendall('HTTP/1.1 200 OK\r\n'.encode())
            conn.sendall('Content-Type: text/html\r\n'.encode())
            conn.sendall('Connection: close\r\n\r\n'.encode())
            conn.sendall(response.encode())

        conn.close()
    except OSError:
        pass

    time.sleep(0.1)
