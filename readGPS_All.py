#GPS WORKING ASKDHASKJDHASKJLHDSFKHDFASHKFDASKHLAFD
from microbit import *

# Initialize UART on Pin1 (TX) and Pin0 (RX)
uart.init(baudrate=9600, tx=pin1, rx=pin0)

# Create an empty list to store received data
received_data = []

while True:
    if uart.any():  # Check if data is available to read
        data = uart.read()  # Read incoming data

        if data:  # Ensure data is not None
            try:
                data = data.decode('utf-8').strip()  # Decode and clean up data
                received_data.append(data)  # Store in array
                
                display.scroll(data)  # Show received data on Micro:bit screen
                print("Received:", data)  # Print to USB Serial Console

            except Exception as e:
                print("Decoding error:", e)  # Handle potential decoding errors

    sleep(1000)  # Pause for a moment