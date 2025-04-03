# READ GPS COORDINATES AND CHECK SAFE AREA AND SEND TO SIGFOX
from microbit import *
import time
import math

# Initialize UART for GPS
uart.init(baudrate=9600, tx=pin1, rx=pin0)  # GPS on RX/TX, Sigfox on TX

buffer = ""  # Buffer for accumulating GPS data
gps_found = False
last_sent_time = running_time()  # Track last Sigfox message time

# Safe Area Coordinates (centre of the safe zone)
SAFE_LAT = 54.8420854
SAFE_LON = -7.9366608
SAFE_RADIUS_METERS = 200  # 200 meters

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # Distance in meters

def convert_nmea_to_decimal(coord, direction):
    #"""Convert NMEA coordinates (DDMM.MMMM) to decimal degrees."""
    if not coord:
        return None  # No valid coordinate

    try:
        degrees = int(float(coord) / 100)  # Extract degrees
        minutes = float(coord) % 100       # Extract minutes
        decimal = degrees + (minutes / 60)  # Convert to decimal degrees

        if direction in ['S', 'W']:
            decimal *= -1  # Negative for South/West

        return round(decimal, 6)  # Return rounded decimal degrees
    except ValueError:
        return None  # Handle cases where conversion fails

while True:
    lat, lon = None, None  # Reset GPS values

    # Continuously read GPS data and display it when available
    if uart.any():
        data = uart.read()
        if data:
            #display.scroll("Data Received")  # Debugging
            try:
                buffer += data.decode('utf-8')  # Append new data
                lines = buffer.split("\n")
                buffer = lines.pop()  # Save incomplete line

                for line in lines:
                    line = line.strip()
                    
                    if line.startswith("$GPGGA"):  # NMEA GPS data
                        parts = line.split(",")

                        if len(parts) > 5 and parts[2] and parts[4]:  # Ensure valid data
                            lat = convert_nmea_to_decimal(parts[2], parts[3])
                            lon = convert_nmea_to_decimal(parts[4], parts[5])

                            if lat is None or lon is None:
                                continue  # Skip invalid GPS read

                            # **More lenient filtering**
                            if not (50.0 <= lat <= 55.0 and -8.5 <= lon <= -7.0):
                                display.scroll("GPS Error")
                                continue  # Keep last good reading

                            coord_text = "{} , {}".format(lat, lon)
                            display.scroll(coord_text)

                            # Calculate distance from safe area
                            distance = haversine(lat, lon, SAFE_LAT, SAFE_LON)

                            if distance > SAFE_RADIUS_METERS:
                                display.scroll("ALERT")
                            else:
                                display.scroll("SAFE")

                            gps_found = True  # GPS data is valid
                            break  # Stop searching once valid GPS is found

            except Exception:
                pass  # Ignore decoding errors

    # Only send to Sigfox if GPS is working
    if gps_found and running_time() - last_sent_time >= 30000:
        last_sent_time = running_time()  # Reset timer

        if lat is not None and lon is not None:
            # Calculate distance from safe area
            distance = haversine(lat, lon, SAFE_LAT, SAFE_LON)
            status = 0x01 if distance > SAFE_RADIUS_METERS else 0x00

            payload = "AT$SS={:02X}\r\n".format(status)
            #display.scroll("Sending: {}".format(payload))  # Debugging
            uart.write(payload)  # Send to Sigfox

    sleep(1000)  # Allow time for UART processing
