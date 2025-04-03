#filters only coorindates
from microbit import *

# Initialize UART on Pin1 (TX) and Pin0 (RX)
uart.init(baudrate=9600, tx=pin1, rx=pin0)

buffer = ""  # Buffer for accumulating data

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
    if uart.any():  # Check if data is available to read
        data = uart.read()  # Read incoming data

        if data:  # Ensure data is not None
            try:
                buffer += data.decode('utf-8')  # Append new data to buffer
                lines = buffer.split("\n")
                buffer = lines.pop()  # Save incomplete line for next loop

                for line in lines:
                    line = line.strip()
                    print("Raw:", line)  # Debug print

                    if line.startswith("$GPGGA"):
                        parts = line.split(",")  # Split into fields

                        if len(parts) > 5 and parts[2] and parts[4]:  # Ensure valid data
                            lat = convert_nmea_to_decimal(parts[2], parts[3])  # Latitude
                            lon = convert_nmea_to_decimal(parts[4], parts[5])  # Longitude

                            if lat is not None and lon is not None:
                                coord_text = str(lat) + "," + str(lon)
                                display.scroll(coord_text)  # Show only lat, lon
                                print("GPS Coordinates:", coord_text)  # Print for debugging
                            else:
                                display.scroll("No GPS")  # No valid GPS data
                        else:
                            display.scroll("No GPS Fix")  # No lock yet

            except Exception as e:
                print("Decoding error:", str(e))  # Debugging

    sleep(1000)  # Pause for a moment
