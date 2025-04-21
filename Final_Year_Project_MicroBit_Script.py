#COMBINED GPS/BPM SCRIPT -> SIGFOX -> THINGSPEAK
#Commented version
from microbit import *
import time
import math

# ----------------- HEART RATE SENSOR SETUP ----------------- #

MAX30102_I2C_ADDR = 0x57
# Register addresses for MAX30102 configuration and data access
REG_INTR_ENABLE_1 = 0x02
REG_INTR_ENABLE_2 = 0x03
REG_FIFO_WR_PTR = 0x04
REG_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_FIFO_DATA = 0x07
REG_FIFO_CONFIG = 0x08
REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A
REG_LED1_PA = 0x0C

def write_register(register, value):
    i2c.write(MAX30102_I2C_ADDR, bytes([register, value]))

def reset_sensor():
    write_register(REG_MODE_CONFIG, 0x40)
    sleep(100)

def configure_sensor():
    # Enables interrupts, sets sampling modes, and LED power
    write_register(REG_INTR_ENABLE_1, 0xC0)
    write_register(REG_INTR_ENABLE_2, 0x00)
    write_register(REG_FIFO_WR_PTR, 0x00)
    write_register(REG_OVF_COUNTER, 0x00)
    write_register(REG_FIFO_RD_PTR, 0x00)
    write_register(REG_FIFO_CONFIG, 0x0F)
    write_register(REG_MODE_CONFIG, 0x02)
    write_register(REG_SPO2_CONFIG, 0x27)
    write_register(REG_LED1_PA, 0x1F)

def read_fifo_sample():
    # Reads raw IR value from sensor FIFO 
    i2c.write(MAX30102_I2C_ADDR, bytes([REG_FIFO_DATA]))
    raw = i2c.read(MAX30102_I2C_ADDR, 3)
    value = (raw[0] << 16 | raw[1] << 8 | raw[2]) & 0x3FFFF
    return value

def moving_average(data, window=4):
    # Simple moving average filter to reduce noise
    return [sum(data[max(0, i-window+1):i+1]) / len(data[max(0, i-window+1):i+1]) for i in range(len(data))]

def detect_peaks(data, timestamps, threshold, min_interval_ms=300, max_interval_ms=1500):
    # Finds peaks that exceed the threshold and are separated by valid time intervals
    peaks = []
    peak_times = []
    for i in range(1, len(data) - 1):
        if data[i] > threshold and data[i] > data[i - 1] and data[i] > data[i + 1]:
            if not peak_times or (timestamps[i] - peak_times[-1] > min_interval_ms):
                peaks.append(i)
                peak_times.append(timestamps[i])
    return peak_times

reset_sensor()
configure_sensor()

SAMPLE_RATE = 25
BUFFER_SECONDS = 6
BUFFER_SIZE = SAMPLE_RATE * BUFFER_SECONDS

samples = []
timestamps = []
bpm_history = []
ema_bpm = None  # Exponential Moving Average of BPM
alpha = 0.2
latest_stable_bpm = 0  # Used in Sigfox payload

# ----------------- GPS AND SIGFOX ----------------- #

uart.init(baudrate=9600, tx=pin1, rx=pin0)

buffer = ""
gps_found = False
last_sent_time = running_time()

# Define geofence center and safe radius
SAFE_LAT = 54.953160
SAFE_LON = -7.722004
SAFE_RADIUS_METERS = 200

def haversine(lat1, lon1, lat2, lon2):
    # Calculates distance between two GPS coordinates in meters
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def convert_nmea_to_decimal(coord, direction):
    # Converts GPS coordinate from NMEA format to decimal degrees
    if not coord:
        return None
    try:
        degrees = int(float(coord) / 100)
        minutes = float(coord) % 100
        decimal = degrees + (minutes / 60)
        if direction in ['S', 'W']:
            decimal *= -1
        return round(decimal, 6)
    except ValueError:
        return None

# ----------------- MAIN LOOP ----------------- #

while True:
    # --- Heartbeat Monitoring --- #
    sample = read_fifo_sample()
    timestamp = running_time()
    samples.append(sample)
    timestamps.append(timestamp)

    # Maintain fixed-size buffer
    if len(samples) > BUFFER_SIZE:
        samples.pop(0)
        timestamps.pop(0)

    if len(samples) == BUFFER_SIZE:
        filtered = moving_average(samples)
        dynamic_threshold = sum(filtered) / len(filtered)
        peak_times = detect_peaks(filtered, timestamps, dynamic_threshold)

        if len(peak_times) >= 2:
            # Calculate time between peaks (beat intervals)
            intervals = []
            for i in range(1, len(peak_times)):
                interval = peak_times[i] - peak_times[i - 1]
                if 300 < interval < 1500:  # Valid beat duration range
                    intervals.append(interval)

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                bpm = 60000 / avg_interval  # Convert ms interval to BPM

                if 40 < bpm < 180:  # Filter out unrealistic values
                    bpm_history.append(bpm)
                    if len(bpm_history) > 5:
                        bpm_history.pop(0)

                    rolling_bpm = sum(bpm_history) / len(bpm_history)

                    # Apply exponential moving average
                    if ema_bpm is None:
                        ema_bpm = rolling_bpm
                    else:
                        ema_bpm = (1 - alpha) * ema_bpm + alpha * rolling_bpm

                    latest_stable_bpm = int(ema_bpm)
                    print("Stable BPM:", latest_stable_bpm)
                else:
                    print("Ignored outlier BPM:", int(bpm))
            else:
                print("Not enough clean intervals")
        else:
            print("Not enough peaks")

    # --- GPS Processing --- #
    lat, lon = None, None

    if uart.any():
        data = uart.read()
        if data:
            try:
                buffer += data.decode('utf-8')
                lines = buffer.split("\n")
                buffer = lines.pop()  # Keep incomplete line for next loop

                for line in lines:
                    line = line.strip() # Remove leading/trailing whitespace
                    if line.startswith("$GPGGA"): # Check for the GPGGA sentence which contains GPS fix data
                        parts = line.split(",")  # Split the sentence into components by comma
                            
                        if len(parts) > 5 and parts[2] and parts[4]: # Make sure lat and long fields are present before trying to convert
                            lat = convert_nmea_to_decimal(parts[2], parts[3]) # Convert lat from NMEA to decimal
                            lon = convert_nmea_to_decimal(parts[4], parts[5]) # Convert lon from NMEA to decimal

                            if lat is None or lon is None:
                                continue

                            # Basic bounds check (approximate Ireland area)
                            if not (50.0 <= lat <= 55.0 and -8.5 <= lon <= -7.0):
                                display.scroll("GPS Error")
                                continue

                            coord_text = "{} , {}".format(lat, lon)
                            display.scroll(coord_text)

                            # Check if outside the safe zone
                            distance = haversine(lat, lon, SAFE_LAT, SAFE_LON)

                            if distance > SAFE_RADIUS_METERS:
                                display.scroll("ALERT")
                            else:
                                display.scroll("SAFE")

                            display.scroll("BPM: {}".format(latest_stable_bpm))

                            gps_found = True
                            break

            except Exception:
                pass

 
    if gps_found and running_time() - last_sent_time >= 30000:
        last_sent_time = running_time()

        if lat is not None and lon is not None:
            distance = haversine(lat, lon, SAFE_LAT, SAFE_LON)
            status = 0x01 if distance > SAFE_RADIUS_METERS else 0x00
            bpm = max(40, min(latest_stable_bpm, 180))  # Clamp BPM to 1 byte

            # --- Encode GPS coordinates into integers for compact transmission
            lat_decimal = int((lat - 54.0) * 10000)
            lon_decimal = int((-7.0 - lon) * 10000)

            # Limit values to 16-bit range
            lat_decimal = max(0, min(lat_decimal, 65535))
            lon_decimal = max(0, min(lon_decimal, 65535))

            # --- Format payload as 6-byte binary string
            payload = bytes([
                status,
                bpm,
                (lat_decimal >> 8) & 0xFF,
                lat_decimal & 0xFF,
                (lon_decimal >> 8) & 0xFF,
                lon_decimal & 0xFF
            ])

            # Format and send Sigfox payload as hex command
            sigfox_cmd = "AT$SS={:02X}{:02X}{:02X}{:02X}{:02X}{:02X}\r\n".format(
                status,
                bpm,
                (lat_decimal >> 8) & 0xFF,
                lat_decimal & 0xFF,
                (lon_decimal >> 8) & 0xFF,
                lon_decimal & 0xFF
            )

            uart.write(sigfox_cmd)

    # Maintain consistent sample rate
    sleep(int(1000 / SAMPLE_RATE))
