# GPS WORKING and filtering to gpgga
from microbit import *

# Initialize UART on Pin1 (TX) and Pin0 (RX)
uart.init(baudrate=9600,  rx=pin0)

# Create an empty list to store received data
received_data = []
buffer = ""

while True:
    if uart.any():  # Check if data is available to read
        data = uart.read()  # Read incoming data

        if data:  # Ensure data is not None
            try:
                # data = data.decode('utf-8').strip()  # Decode and clean up data
                # This will overwrite. Each time data comes in it replaces the old value
                buffer += data.decode('utf-8')
                # received_data.append(data)  # Store in array
                lines = buffer.split("\n")
                buffer = lines.pop()

                for line in lines:
                    line = line.strip()

                    if line.startswith("$GPGGA"):
                        received_data.append(line)
                        display.scroll(line)
                    print("Received:", line)

            except Exception as e:
                print("Decoding error:", e)  # Handle potential decoding errors

    sleep(1000)  # Pause for a moment
