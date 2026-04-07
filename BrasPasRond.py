import RPi.GPIO as GPIO
import time

# Utilisation de la numérotation BCM (mode GPIO number plutôt que PIN number)
GPIO.setmode(GPIO.BCM)

# Choisir les GPIO pour les signaux
SERVO_PIN1 = 13
SERVO_PIN2 = 15
SERVO_PIN3 = 17
GPIO.setup(SERVO_PIN1, GPIO.OUT)
GPIO.setup(SERVO_PIN2, GPIO.OUT)
GPIO.setup(SERVO_PIN3, GPIO.OUT)

# Création des PWM à 50 Hz (standard servo)
pwm1 = GPIO.PWM(SERVO_PIN1, 50)
pwm1.start(0)
pwm2 = GPIO.PWM(SERVO_PIN2, 50)
pwm2.start(0)
pwm3 = GPIO.PWM(SERVO_PIN3, 50)
pwm3.start(0)

def set_angle(angle, pwm):
    # Conversion angle → DutyCycle
    duty = 2.5 + (angle / 18)  # approx pour MG90S (0°=2%, 90°=7%, 180°=12%)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)  # temps pour que le servo bouge
    pwm.ChangeDutyCycle(0)  # éviter vibrations

try:
    #Épaule --> [80, 170] degrés
    #Avant-Bras --> [50, 130] degrés
    #Base --> [5, 170] degrés
    
    #format "set_angle(X, pwmX)" et "time.sleep(0,1)
   
    while True:
        set_angle(5, pwm1)
    #    set_angle(30, pwm2)
     #   set_angle(90, pwm3)
        time.sleep(1) # 100ms juste pour dire qu'on ne recommence pas tout de suite
        set_angle(170, pwm1)
      #  set_angle(60, pwm2)
       # set_angle(110, pwm3)
        time.sleep(1)
        set_angle(230, pwm1)
        #set_angle(120, pwm2)
        #set_angle(130, pwm3)
        time.sleep(0.1)

except KeyboardInterrupt:
    pass

pwm1.stop()
pwm2.stop()
pwm3.stop()
GPIO.cleanup() # Défaire le setup des GPIO