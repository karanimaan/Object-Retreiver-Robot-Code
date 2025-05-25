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

# move arm out of way of camera

chassis_cmd(10)    # move chassis servo to 10 degrees
time.sleep(1)

shoulder_cmd(0)    # move shoulder servo to 0 degrees
time.sleep(1)

elbow_cmd(45)
time.sleep(1)


# WiFi configuration
ssid = 'ESP32-Car'
password = '12345678'

# Vehicle object
vehicle = libs.vehicle.ACB_Vehicle()
speeds = 130

# Ultrasound
Trig_PIN = 13
Echo_PIN = 14
Ultrasonic = libs.ultrasonic.ACB_Ultrasonic(Trig_PIN,Echo_PIN)

# Set up the WiFi access point
ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password,authmode=network.AUTH_WPA2_PSK)
ap.active(True)

# Wait for the AP to be active
while not ap.active():
    time.sleep(1)

print('Car Ready! Use "http://{}" to connect'.format(ap.ifconfig()[0]))
vehicle.move(vehicle.Stop, 0)


# Set up the socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0]
s = socket.socket()
s.bind(('0.0.0.0', 80))
s.listen(1)

print(Ultrasonic.get_distance())


while True:
    try:
        conn, addr = s.accept()
        
        command = conn.recv(1)
        move = command.decode().lower()	# decode() makes it UTF string I think
        print(move)

        if move == 'l':
            vehicle.move(vehicle.Contrarotate, speeds)
        elif move == 'r':
            vehicle.move(vehicle.Clockwise, speeds)
        elif move == 's':
            vehicle.move(vehicle.Stop, 0)
            print(Ultrasonic.get_distance())
        elif move == 'f':
            UT_distance = Ultrasonic.get_distance()
            if UT_distance > 14:
                vehicle.move(vehicle.Forward, speeds)
            else:
                vehicle.move(vehicle.Stop, 0)
            print(UT_distance)
        elif move == 'd':
            vehicle.move(vehicle.Stop, 0)
            time.sleep(1)

            # move arm

            shoulder_cmd(40)
            time.sleep(1)

            # open claws
            claws_cmd(140)
            time.sleep(1)

            # set arm to initial position

            chassis_cmd(90)
            time.sleep(1)

            shoulder_cmd(90)
            time.sleep(1)

            elbow_cmd(90)
            time.sleep(1)

            # move arm to block
            UT_distance = Ultrasonic.get_distance()
            print(UT_distance)
            PtpCmd(0, UT_distance+1, 0)
            time.sleep(3)

            # grab block
            claws_cmd(110)
            time.sleep(1)

            # lift block
            shoulder_cmd(90)
            time.sleep(1)

            # let go of block
            claws_cmd(140)
            time.sleep(1)
    finally:
        conn.close()
