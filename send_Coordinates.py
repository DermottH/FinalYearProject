# READ GPS COORDINATES AND SEND TO SIGFOX
from microbit import *
import time

# Initialize UART for both GPS and Sigfox
uart.init(baudrate=9600, tx=pin1, rx=pin0)  # GPS on RX/TX, Sigfox on TX

buffer = ""  # Buffer for accumulating GPS data
counter = 0  # Incremental counter
gps_found = False
last_sent_time = running_time()  # Track last Sigfox message time

def convert_nmea_to_decimal(coord, direction):
    """Convert NMEA coordinates (DDMM.MMMM) to decimal degrees."""
    if not coord:
        return None  # No valid coordinate

    degrees = int(float(coord) / 100)  # Extract degrees
    minutes = float(coord) % 100       # Extract minutes
    decimal = degrees + (minutes / 60)  # Convert to decimal degrees

    if direction in ['S', 'W']:
        decimal *= -1  # Negative for South/West

    return round(decimal, 6)  # Return rounded decimal degrees

while True:
    lat, lon = None, None  # Reset GPS values

    # Continuously read GPS data and display it when available
    if uart.any():
        data = uart.read()
        if data:
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

                            if lat is not None and lon is not None:
                                coord_text = "{} , {}".format(lat, lon)
                                display.scroll(coord_text)  # Show GPS coordinates immediately
                                gps_found = True  # GPS data is valid
                                break  # Stop searching once valid GPS is found

            except Exception:
                pass  # Ignore decoding errors

    # Check if it's time to send data to Sigfox (every 30 seconds)
    if running_time() - last_sent_time >= 30000:
        last_sent_time = running_time()  # Reset timer

        if lat is not None and lon is not None:
            # Convert to integer only if lat/lon are valid numbers
            lat_hex = "{:04X}".format(int((lat + 90) * 1000))
            lon_hex = "{:04X}".format(int((lon + 180) * 1000))
            payload = "AT$SS={}{}\r\n".format(lat_hex, lon_hex)
            gps_found = False  # Reset GPS status
        else:
            # If GPS fix is lost, send counter instead
            display.scroll("No GPS Fix")
            counter += 1
            counter_hex = "{:02X}".format(counter)
            payload = "AT$SS={}\r\n".format(counter_hex)

        # Send message over Sigfox
        uart.write(payload)

    sleep(1000)  # Allow time for UART processing
