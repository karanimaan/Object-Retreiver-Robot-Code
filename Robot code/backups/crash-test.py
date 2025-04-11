import libs.ultrasonic
import libs.vehicle
from libs.ACB_CAR_ARM import *
import time

# Define the GPIO pin numbers connected to different parts of the robotic arm
chassis_pin = 25    # Chassis control pin
shoulder_pin = 26      # Elbow control pin

elbow_pin = 27   # Shoulder control pin
wrist_pin = 33      # Claws control pin
claws_pin = 4       # Wrist control pin

Trig_PIN = 13
Echo_PIN = 14


car = libs.vehicle.ACB_Vehicle()
car.move(car.Stop, 0)

Ultrasonic = libs.ultrasonic.ACB_Ultrasonic(Trig_PIN,Echo_PIN)

def setup():
    # Initialize the robotic arm with the specified pins
    
    car.move(car.Stop, 0)
    
setup()

UT_distance = Ultrasonic.get_distance()
print(UT_distance)

starting_dist = UT_distance
dist_to_take = 5

while UT_distance > starting_dist - dist_to_take and UT_distance>=20:
    UT_distance = Ultrasonic.get_distance()
    print(UT_distance)
    time.sleep(0.005)
    
    car.move(car.Forward, 130) #Smart car
        
print(UT_distance <= starting_dist)      
car.move(car.Stop, 0)
