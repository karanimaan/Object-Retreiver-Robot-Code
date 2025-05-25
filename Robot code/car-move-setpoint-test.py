import libs.vehicle 
import libs.ultrasonic
import time

Trig_PIN = 13
Echo_PIN = 14

car = libs.vehicle.ACB_Vehicle()
Ultrasonic = libs.ultrasonic.ACB_Ultrasonic(Trig_PIN,Echo_PIN)

UT_distance = Ultrasonic.get_distance()
print(UT_distance)

#If the distance is greater than 25, move forward

car.move(car.Forward, 130)

while UT_distance > 25:
    UT_distance = Ultrasonic.get_distance()
    print(UT_distance)
    
car.move(car.Stop, 0)
