#READ FROM PSOC AND SEND TO SIGFOX
from microbit import *
import time

uart.init(baudrate=9600, tx=pin1)


time_elapsed=0
while True:
    display.clear()
    sleep(10000)
        
    #time_elapsed=round((1/((time.ticks_us()-start)))*30000000)
    time_elapsed +=1
    
    hex_value = "{:02X}".format(time_elapsed)

    sigfox_message = "AT$SS= " + hex_value + "\r\n"
    
    #display.show(time_elapsed)
    
    print(time_elapsed)
    print("Raw Value (Decimal):", time_elapsed)  # Print decimal value
    print("Hex Value:", hex_value)  # Print hexadecimal version
    print("Sigfox Message:", sigfox_message)  # Print formatted Sigfox message
    
    uart.write(sigfox_message)
    sleep(500)

   
    
    
