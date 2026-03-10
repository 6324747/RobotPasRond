import cv2
import RPi.GPIO as GPIO
import pigpio
import time

# =========================================
# [1] CONFIGURATION GPIO
# =========================================
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Victor SP : une seule pin signal
PIN_ESC = 23

# Servo direction
PIN_SERVO = 25

GPIO.setup(PIN_SERVO, GPIO.OUT)

# =========================================
# [2] CONNEXION pigpio
# =========================================
pi = pigpio.pi()
if not pi.connected:
    raise SystemExit("Impossible de se connecter à pigpio")

# =========================================
# [3] PWM SERVO DIRECTION
# =========================================
servo_pwm = GPIO.PWM(PIN_SERVO, 50)
servo_pwm.start(0)

# =========================================
# [4] PARAMÈTRES
# =========================================
SERVO_CENTER = 7.5
SERVO_LEFT   = 5.5
SERVO_RIGHT  = 9.5

ESC_NEUTRAL = 1500
ESC_FORWARD_MIN = 1520
ESC_FORWARD_MAX = 1700
ESC_REVERSE_MIN = 1480
ESC_REVERSE_MAX = 1300

DEFAULT_SPEED = 35

# =========================================
# [5] FONCTIONS MOTEUR
# =========================================
def esc_write(us):
    us = max(1000, min(2000, us))
    pi.set_servo_pulsewidth(PIN_ESC, us)

def stop_motor():
    esc_write(ESC_NEUTRAL)

def forward(speed=DEFAULT_SPEED):
    speed = max(0, min(100, speed))
    us = ESC_FORWARD_MIN + int((ESC_FORWARD_MAX - ESC_FORWARD_MIN) * speed / 100.0)
    esc_write(us)

def backward(speed=DEFAULT_SPEED):
    speed = max(0, min(100, speed))
    us = ESC_REVERSE_MIN - int((ESC_REVERSE_MIN - ESC_REVERSE_MAX) * speed / 100.0)
    esc_write(us)

# =========================================
# [6] FONCTIONS DIRECTION
# =========================================
def steer_center():
    servo_pwm.ChangeDutyCycle(SERVO_CENTER)
    time.sleep(0.12)
    servo_pwm.ChangeDutyCycle(0)

def steer_left():
    servo_pwm.ChangeDutyCycle(SERVO_LEFT)
    time.sleep(0.12)
    servo_pwm.ChangeDutyCycle(0)

def steer_right():
    servo_pwm.ChangeDutyCycle(SERVO_RIGHT)
    time.sleep(0.12)
    servo_pwm.ChangeDutyCycle(0)

# =========================================
# [7] ARRÊT PROPRE
# =========================================
def safe_shutdown():
    stop_motor()
    steer_center()
    time.sleep(0.2)
    servo_pwm.stop()
    pi.set_servo_pulsewidth(PIN_ESC, 0)
    pi.stop()
    GPIO.cleanup()

# =========================================
# [8] DÉMARRAGE
# =========================================
print("Initialisation...")
stop_motor()
steer_center()
time.sleep(3.0)

# =========================================
# [9] CONFIG CAMERA USB
# =========================================
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    safe_shutdown()
    raise SystemExit("Impossible d'ouvrir la webcam sur /dev/video0")

print("======================================")
print("Contrôles clavier dans la fenêtre caméra :")
print("w = avancer")
print("s = reculer")
print("a = tourner à droite")
print("d = tourner à gauche")
print("c = recentrer direction")
print("x = stop moteur")
print("+ = augmenter vitesse")
print("- = diminuer vitesse")
print("q = quitter")
print("======================================")

speed = DEFAULT_SPEED
current_drive = "STOP"

# =========================================
# [10] BOUCLE PRINCIPALE
# =========================================
try:
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Lecture caméra impossible")
            break

        cv2.putText(frame, f"Vitesse: {speed}%", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.putText(frame, f"Moteur: {current_drive}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.putText(frame, "W/S moteur | A/D direction | X stop | C centre | Q quit",
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

        cv2.imshow("RC Car Camera", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        elif key == ord('w'):
            forward(speed)
            current_drive = "FORWARD"

        elif key == ord('s'):
            backward(speed)
            current_drive = "REVERSE"

        elif key == ord('x'):
            stop_motor()
            current_drive = "STOP"

        elif key == ord('a'):
            steer_right()

        elif key == ord('d'):
            steer_left()

        elif key == ord('c'):
            steer_center()

        elif key == ord('+') or key == ord('='):
            speed = min(100, speed + 5)
            print(f"Vitesse = {speed}%")
            if current_drive == "FORWARD":
                forward(speed)
            elif current_drive == "REVERSE":
                backward(speed)

        elif key == ord('-') or key == ord('_'):
            speed = max(0, speed - 5)
            print(f"Vitesse = {speed}%")
            if current_drive == "FORWARD":
                forward(speed)
            elif current_drive == "REVERSE":
                backward(speed)

        time.sleep(0.001)

finally:
    cap.release()
    cv2.destroyAllWindows()
    safe_shutdown()
    print("Fermé proprement.")
