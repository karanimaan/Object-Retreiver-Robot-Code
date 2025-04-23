import network
import socket
from machine import Pin
import time
import libs.vehicle
import libs.ultrasonic


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
            #time.sleep(0.3)
            #vehicle.move(vehicle.Stop, 0)
        elif move == 'r':
            vehicle.move(vehicle.Clockwise, speeds)
            #time.sleep(0.3)
            #vehicle.move(vehicle.Stop, 0)
        elif move == 's':
            vehicle.move(vehicle.Stop, 0)
            print(Ultrasonic.get_distance())
        elif move == 'f':
            UT_distance = Ultrasonic.get_distance()
            if UT_distance > 9:
                vehicle.move(vehicle.Forward, speeds)
                #time.sleep(0.3)
                #vehicle.move(vehicle.Stop, 0)
            else:
                vehicle.move(vehicle.Stop, 0)
            print(UT_distance)
        #time.sleep(0.5)
    finally:
        conn.close()
