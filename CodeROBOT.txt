import cv2
import RPi.GPIO as GPIO
import time
 
# =========================
# [1] CONFIG GPIO (ton code)
# =========================
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
 
PIN_27 = 27
PIN_17 = 17
PIN_22 = 22
PIN_23 = 23
 
GPIO.setup(PIN_27, GPIO.OUT)
GPIO.setup(PIN_17, GPIO.OUT)
GPIO.setup(PIN_22, GPIO.OUT)
GPIO.setup(PIN_23, GPIO.OUT)
GPIO.setmode(GPIO.BCM)
 
GPIO.setmode(GPIO.BCM)
 
def all_off():
    GPIO.output(PIN_27, False)
    GPIO.output(PIN_17, False)
    GPIO.output(PIN_22, False)
    GPIO.output(PIN_23, False)
 
# Start safe
all_off()
 
# =========================
# [2] CONFIG CAMERA (USB)
# =========================
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
 
# Force MJPEG + résolution stable (comme ton test ffplay)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 200)
 
if not cap.isOpened():
    all_off()
    GPIO.cleanup()
    raise SystemExit("Impossible d'ouvrir la webcam sur /dev/video0")
def init_pwm(speed):
    pwm1 = GPIO.PWM(PIN_27, 500)
    pwm1.start(0)
 
    pwm2 = GPIO.PWM(PIN_17, 500)
    pwm2.start(0)
 
    pwm3 = GPIO.PWM(PIN_22, 500)
    pwm3.start(0)
 
    pwm4 = GPIO.PWM(PIN_23, 500)
    pwm4.start(0)


 
print("Contrôles: w a s d | x = stop | q = quitter")
 
# =========================
# [3] BOUCLE PRINCIPALE
# =========================
try:
    while True:
        ok, frame = cap.read()
        if not ok:
            print("Lecture caméra impossible")
            break
 
        # Affiche la vidéo
        cv2.imshow("Webcam (q quitter)", frame)
 
        # Lecture clavier (dans la fenêtre OpenCV)
        key = cv2.waitKey(1) & 0xFF
 
        if key == ord('q'):
            break
 
        elif key == ord('s'):
            GPIO.output(PIN_27, True)
            GPIO.output(PIN_17, True)
            GPIO.output(PIN_22, True)
            GPIO.output(PIN_23, True)
 
        elif key == ord('w'):
            GPIO.output(PIN_27, True)
            GPIO.output(PIN_17, True)
            GPIO.output(PIN_22, False)
            GPIO.output(PIN_23, False)
 
        elif key == ord('a'):
            GPIO.output(PIN_27, True)
            GPIO.output(PIN_17, False)
 
        elif key == ord('d'):
            GPIO.output(PIN_27, False)
            GPIO.output(PIN_17, True)
 
        elif key == ord('x'):
            # Stop: tout OFF
            all_off()
 
        # Petit sleep optionnel pour calmer le CPU
        time.sleep(0.001)
 
finally:
    # Nettoyage obligatoire
    cap.release()
    cv2.destroyAllWindows()
    all_off()
    GPIO.cleanup()
    print("Fermé proprement.")