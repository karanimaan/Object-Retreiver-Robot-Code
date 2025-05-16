import network
import socket
from machine import Pin
import time
import libs.vehicle
import libs.ultrasonic
from libs.ACB_CAR_ARM import *


# arm initial positioning

chassis_pin = 25    # Chassis control pin
shoulder_pin = 33      # Elbow control pin
elbow_pin = 27   # Shoulder control pin
wrist_pin = 26      # Claws control pin
claws_pin = 4       # Wrist control pin

ARM_init(chassis_pin, shoulder_pin, elbow_pin, wrist_pin, claws_pin)
time.sleep(1)


shoulder_cmd(40)
time.sleep(1)

claws_cmd(140)
time.sleep(1)

# set to initial position
chassis_cmd(90)
time.sleep(1)

shoulder_cmd(90)
time.sleep(1)

elbow_cmd(90)
time.sleep(1)


y = 12  # hard-coded value
PtpCmd(0, 12, 0)
time.sleep(3)

claws_cmd(110)
time.sleep(1)

shoulder_cmd(90)
time.sleep(1)

claws_cmd(140)
time.sleep(1)
