import pygame
import RPi.GPIO as GPIO
import cv2
import numpy as np
import serial
import time

# =========================
# [0] NEXTION
# =========================
NEXTION_PORT = "/dev/serial0"   # ou "/dev/ttyUSB0"
NEXTION_BAUD = 9600

nextion = None

def nextion_send(cmd):
    global nextion
    if nextion is not None:
        nextion.write(cmd.encode("ascii"))
        nextion.write(b'\xFF\xFF\xFF')

def nextion_init():
    global nextion
    try:
        nextion = serial.Serial(NEXTION_PORT, NEXTION_BAUD, timeout=1)
        time.sleep(0.5)
        nextion_send("p0.pic=1")
        print("Nextion connecté et commande envoyée : p0.pic=1")
    except Exception as e:
        nextion = None
        print("Nextion non disponible :", e)

# =========================
# [1] CONFIG GPIO
# =========================
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

PIN_27 = 27
PIN_17 = 17
PIN_22 = 22
PIN_23 = 23

# Choisir les GPIO pour les signaux (bras)
SERVO_AB = 13
SERVO_E = 6
SERVO_B = 5
GPIO.setup(SERVO_AB, GPIO.OUT)
GPIO.setup(SERVO_E, GPIO.OUT)
GPIO.setup(SERVO_B, GPIO.OUT)

# Création des PWM à 50 Hz (standard servo)
pwmAB = GPIO.PWM(SERVO_AB, 50)
pwmAB.start(0)
pwmE = GPIO.PWM(SERVO_E, 50)
pwmE.start(0)
pwmB = GPIO.PWM(SERVO_B, 50)
pwmB.start(0)

#pins moteurs
GPIO.setup(PIN_27, GPIO.OUT)
GPIO.setup(PIN_17, GPIO.OUT)
GPIO.setup(PIN_22, GPIO.OUT)
GPIO.setup(PIN_23, GPIO.OUT)

def set_angle(angle, pwm):
    # Conversion angle → DutyCycle
    duty = 2.5 + (angle / 18)  # approx pour MG90S (0°=2%, 90°=7%, 180°=12%)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)  # temps pour que le servo bouge
    pwm.ChangeDutyCycle(0)  # éviter vibrations

def all_off():
    GPIO.output(PIN_27, False)
    GPIO.output(PIN_17, False)
    GPIO.output(PIN_22, False)
    GPIO.output(PIN_23, False)

def move_stop():
    all_off()

def move_forward():  # w
    GPIO.output(PIN_27, True)
    GPIO.output(PIN_17, True)
    GPIO.output(PIN_22, True)
    GPIO.output(PIN_23, True)

def move_backward():  # s
    GPIO.output(PIN_27, True)
    GPIO.output(PIN_17, True)
    GPIO.output(PIN_22, False)
    GPIO.output(PIN_23, False)

def move_left():  # a
    GPIO.output(PIN_27, True)
    GPIO.output(PIN_17, False)
    GPIO.output(PIN_22, True)
    GPIO.output(PIN_23, True)

def move_right():  # d
    GPIO.output(PIN_27, False)
    GPIO.output(PIN_17, True)
    GPIO.output(PIN_22, True)
    GPIO.output(PIN_23, True)
    
def move_up():
    AB = AB + 1
    set_angle(AB, pwmAB)

def move_down():
    AB = AB - 1
    set_angle(AB, pwmAB)

def move_shallow():
    E = E - 1
    set_angle(E, pwmE)

def move_deep():
    E = E + 1
    set_angle(E, pwmE)

def move_l():
    B = B + 1
    set_angle(B, pwmB)

def move_r():
    B = B - 1
    set_angle(B, pwmB)

all_off()

# =========================
# [2] CAMERA
# =========================
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    GPIO.cleanup()
    raise SystemExit("Impossible d'ouvrir la webcam sur /dev/video0")

# =========================
# [3] PYGAME
# =========================
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("RC Camera Control")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

print("Controle: W A S D | X = stop | Q = quitter")
print("IMPORTANT: clique une fois dans la fenêtre pygame si besoin.")

current_state = "STOP"
last_state = None

# initialisation Nextion
nextion_init()

# =========================
# [4] LOOP
# =========================
try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        if keys[pygame.K_q]:
            running = False

        elif keys[pygame.K_x]:
            move_stop()
            current_state = "STOP"

        elif keys[pygame.K_w]:
            move_forward()
            current_state = "FORWARD"

        elif keys[pygame.K_s]:
            move_backward()
            current_state = "BACKWARD"

        elif keys[pygame.K_a]:
            move_left()
            current_state = "LEFT"

        elif keys[pygame.K_d]:
            move_right()
            current_state = "RIGHT"

        else:
            move_stop()
            current_state = "STOP"

        # envoi Nextion seulement si l'état change
        if current_state != last_state:
            if current_state == "STOP":
                nextion_send("p0.pic=0")
            elif current_state == "FORWARD":
                nextion_send("p0.pic=3")
            elif current_state == "BACKWARD":
                nextion_send("p0.pic=0")
            elif current_state == "LEFT":
                nextion_send("p0.pic=2")
            elif current_state == "RIGHT":
                nextion_send("p0.pic=1")

            last_state = current_state

        # lecture caméra
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1)
            frame = np.rot90(frame, k=1)

            frame_surface = pygame.surfarray.make_surface(frame)
            screen.blit(frame_surface, (0, 0))

            text = font.render(f"Etat: {current_state}", True, (0, 255, 0))
            screen.blit(text, (10, 10))

            help_text = font.render("WASD bouger | X stop | Q quitter", True, (255, 255, 0))
            screen.blit(help_text, (10, 40))
        else:
            screen.fill((0, 0, 0))
            text = font.render("Erreur camera", True, (255, 0, 0))
            screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(100)

finally:
    move_stop()
    cap.release()
    GPIO.cleanup()

    if nextion is not None:
        try:
            nextion_send("p0.pic=1")
            nextion.close()
        except:
            pass

    pygame.quit()
    print("Fermé proprement.")