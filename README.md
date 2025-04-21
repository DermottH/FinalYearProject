# Micro:bit GPS & BPM Monitoring System (Sigfox + ThingSpeak)


This project combines a GPS module, heart rate sensor (MAX30102), and Sigfox communication to create a portable safety monitoring device using the BBC micro:bit. The system monitors biometric and geolocation data in real time, sends alerts when users move outside a predefined safe zone, and logs information to ThingSpeak for remote access and analysis.

 Features
📍 GPS Tracking
Parses NMEA $GPGGA data, converts to decimal coordinates, and validates location accuracy.

❤️ Heart Rate Monitoring
Reads optical pulse data using the MAX30102 sensor. Applies a moving average filter and detects BPM with peak interval analysis and exponential moving average (EMA).

📡 Sigfox Communication
Encodes and sends compressed payloads (status, BPM, coordinates) over the 0G Sigfox network every 30 seconds.

🧭 Safe Zone Alerts
Calculates user distance from a set safe zone using the Haversine formula. Scrolls ALERT or SAFE messages on the Micro:bit display accordingly.

📊 ThingSpeak Integration
Easily integrate Sigfox backend callbacks to log GPS + BPM data on ThingSpeak dashboards.

Hardware Requirements
-BBC micro:bit
-MAX30102 Heart Rate Sensor (I2C)
-GPS Module (NMEA output via UART)
-Sigfox-compatible radio or board (UART)
-Power supply (e.g. USB battery pack)

Data Format (Sigfox Payload)
6-byte payload format:
'[Status][BPM][Lat_H][Lat_L][Lon_H][Lon_L]'
Status: 0x01 if user is outside the safe zone, 0x00 if inside

BPM: Latest stable heart rate, clamped between 40–180
Lat/Lon: Offsets from base value (e.g. 54.000000 and -7.000000) encoded as 16-bit integers

Safe Zone Logic
Set your own coordinates and radius (in meters) in the main script:
SAFE_LAT = 54.953160
SAFE_LON = -7.722004
SAFE_RADIUS_METERS = 200

Connecting to ThingSpeak
1-Create a ThingSpeak channel.
2-Use the Sigfox backend callbacks to forward messages to your ThingSpeak endpoint.
3-Decode payloads using a custom parser script.
