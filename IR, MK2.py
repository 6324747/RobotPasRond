import RPi.GPIO as GPIO
import time

IR = 23
led = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(IR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(led,GPIO.OUT)

try:
    while True:

        if GPIO.input(IR) == 0:
                print("Objection")
                GPIO.output(led, GPIO.HIGH)
        else:
                print("nothing")
                GPIO.output(led, GPIO.LOW)
            
        time.sleep(0.3)
        
except KeyboardInterrupt:
    GPIO.cleanup()