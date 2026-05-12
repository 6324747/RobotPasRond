import pygame
import RPi.GPIO as GPIO
import cv2
import numpy as np
import serial
import time

# =========================
# [0] NEXTION
# =========================
NEXTION_PORT = "/dev/serial0"
NEXTION_BAUD = 9600

nextion = None
last_nextion_pic = None
last_nextion_time = 0

NEXTION_MIN_DELAY = 0.12

# IDs des images Nextion
IMG_FORWARD = 0
IMG_RIGHT = 1
IMG_LEFT = 2
IMG_BACK = 3

def nextion_send(cmd):

    global nextion
    global last_nextion_time

    if nextion is None:
        return

    now = time.time()

    # anti spam
    if now - last_nextion_time < NEXTION_MIN_DELAY:
        return

    try:
        nextion.write(cmd.encode("ascii"))
        nextion.write(b'\xFF\xFF\xFF')
        nextion.flush()

        last_nextion_time = now

    except Exception as e:
        print("Erreur Nextion:", e)

def show_pic(pic_id):

    global last_nextion_pic

    # évite d'envoyer la même image
    if pic_id == last_nextion_pic:
        return

    nextion_send(f"p0.pic={pic_id}")

    last_nextion_pic = pic_id

def nextion_init():

    global nextion

    try:
        nextion = serial.Serial(
            NEXTION_PORT,
            NEXTION_BAUD,
            timeout=0.1
        )

        time.sleep(0.5)

        nextion.reset_input_buffer()
        nextion.reset_output_buffer()

        # désactive réponses Nextion
        nextion_send("bkcmd=0")

        time.sleep(0.2)

        # image par défaut
        show_pic(IMG_FORWARD)

        print("Nextion connecté")

    except Exception as e:

        nextion = None

        print("Nextion non disponible :", e)

# =========================
# RESET NEXTION
# =========================
def nextion_reset_screen():

    global last_nextion_pic

    if nextion is None:
        return

    try:
        print("Reset Nextion...")

        nextion.reset_input_buffer()
        nextion.reset_output_buffer()

        time.sleep(0.1)

        nextion_send("bkcmd=0")

        time.sleep(0.1)

        nextion_send("page page0")

        time.sleep(0.3)

        last_nextion_pic = None

        show_pic(IMG_FORWARD)

        print("Nextion reset OK")

    except Exception as e:

        print("Erreur reset Nextion:", e)

# =========================
# [1] CONFIG GPIO
# =========================
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

PIN_27 = 27
PIN_17 = 17
PIN_22 = 22
PIN_23 = 23

SERVO_AB = 13
SERVO_E = 6
SERVO_B = 5

GPIO.setup(SERVO_AB, GPIO.OUT)
GPIO.setup(SERVO_E, GPIO.OUT)
GPIO.setup(SERVO_B, GPIO.OUT)

pwmAB = GPIO.PWM(SERVO_AB, 50)
pwmAB.start(0)

pwmE = GPIO.PWM(SERVO_E, 50)
pwmE.start(0)

pwmB = GPIO.PWM(SERVO_B, 50)
pwmB.start(0)

B = 88
AB = 90
E = 90

GPIO.setup(PIN_27, GPIO.OUT)
GPIO.setup(PIN_17, GPIO.OUT)
GPIO.setup(PIN_22, GPIO.OUT)
GPIO.setup(PIN_23, GPIO.OUT)

def set_angle(angle, pwm):

    duty = 2.5 + (angle / 18)

    pwm.ChangeDutyCycle(duty)

    time.sleep(0.15)

    pwm.ChangeDutyCycle(0)

def all_off():

    GPIO.output(PIN_27, False)
    GPIO.output(PIN_17, False)
    GPIO.output(PIN_22, False)
    GPIO.output(PIN_23, False)

def move_stop():

    all_off()

def move_forward():

    GPIO.output(PIN_27, True)
    GPIO.output(PIN_17, True)
    GPIO.output(PIN_22, False)
    GPIO.output(PIN_23, False)

def move_backward():

    GPIO.output(PIN_27, True)
    GPIO.output(PIN_17, True)
    GPIO.output(PIN_22, True)
    GPIO.output(PIN_23, True)

def move_left():

    GPIO.output(PIN_27, True)
    GPIO.output(PIN_17, True)
    GPIO.output(PIN_22, True)
    GPIO.output(PIN_23, False)

def move_right():

    GPIO.output(PIN_27, True)
    GPIO.output(PIN_17, True)
    GPIO.output(PIN_22, False)
    GPIO.output(PIN_23, True)

def move_up():

    global AB

    AB = min(180, AB + 10)

    set_angle(AB, pwmAB)

def move_down():

    global AB

    AB = max(0, AB - 10)

    set_angle(AB, pwmAB)

def move_shallow():

    global E

    E = max(0, E - 10)

    set_angle(E, pwmE)

def move_deep():

    global E

    E = min(180, E + 10)

    set_angle(E, pwmE)

def move_l():

    global B

    B = min(180, B + 10)

    set_angle(B, pwmB)

def move_r():

    global B

    B = max(0, B - 10)

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

    raise SystemExit("Impossible d'ouvrir la webcam")

# =========================
# [3] PYGAME
# =========================
pygame.init()

screen = pygame.display.set_mode((640, 480))

pygame.display.set_caption("RC Camera Control")

clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 28)

print("Controle: W A S D | X = stop | R = reset écran | Q = quitter")

current_state = "STOP"
last_state = None

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

        new_state = current_state

        if keys[pygame.K_q]:

            set_angle(80, pwmB)
            set_angle(130, pwmAB)
            set_angle(20, pwmE)

            running = False

        elif keys[pygame.K_r]:

            nextion_reset_screen()

        elif keys[pygame.K_x]:

            move_stop()
            new_state = "STOP"

        elif keys[pygame.K_w]:

            move_forward()
            new_state = "FORWARD"

        elif keys[pygame.K_s]:

            move_backward()
            new_state = "BACKWARD"

        elif keys[pygame.K_a]:

            move_left()
            new_state = "LEFT"

        elif keys[pygame.K_d]:

            move_right()
            new_state = "RIGHT"

        elif keys[pygame.K_i]:

            move_up()

        elif keys[pygame.K_k]:

            move_down()

        elif keys[pygame.K_u]:

            move_shallow()

        elif keys[pygame.K_o]:

            move_deep()

        elif keys[pygame.K_j]:

            move_l()

        elif keys[pygame.K_l]:

            move_r()

        else:

            move_stop()
            new_state = "STOP"

        current_state = new_state

        # =========================
        # NEXTION
        # =========================
        if current_state != last_state:

            if current_state == "STOP":
                show_pic(IMG_FORWARD)

            elif current_state == "FORWARD":
                show_pic(IMG_FORWARD)

            elif current_state == "BACKWARD":
                show_pic(IMG_BACK)

            elif current_state == "LEFT":
                show_pic(IMG_LEFT)

            elif current_state == "RIGHT":
                show_pic(IMG_RIGHT)

            last_state = current_state

        # =========================
        # CAMERA
        # =========================
        ret, frame = cap.read()

        if ret:

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            frame = cv2.flip(frame, 1)

            frame = np.rot90(frame, k=1)

            frame_surface = pygame.surfarray.make_surface(frame)

            screen.blit(frame_surface, (0, 0))

            text = font.render(
                f"Etat: {current_state}",
                True,
                (0, 255, 0)
            )

            screen.blit(text, (10, 10))

            help_text = font.render(
                "WASD bouger | R reset écran | X stop | Q quitter",
                True,
                (255, 255, 0)
            )

            screen.blit(help_text, (10, 40))

        else:

            screen.fill((0, 0, 0))

            text = font.render(
                "Erreur camera",
                True,
                (255, 0, 0)
            )

            screen.blit(text, (10, 10))

        pygame.display.flip()

        clock.tick(30)

finally:

    move_stop()

    cap.release()

    pwmAB.stop()
    pwmE.stop()
    pwmB.stop()

    GPIO.cleanup()

    if nextion is not None:

        try:
            show_pic(IMG_FORWARD)

            time.sleep(0.5)

            nextion.close()

        except:
            pass

    pygame.quit()

    print("Fermé proprement.")