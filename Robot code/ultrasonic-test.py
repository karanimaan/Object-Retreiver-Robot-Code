import libs.ultrasonic
import time

Trig_PIN = 13
Echo_PIN = 14

Ultrasonic = libs.ultrasonic.ACB_Ultrasonic(Trig_PIN,Echo_PIN)

while True:
#for i in range(10):
    UT_distance = Ultrasonic.get_distance()
    
    #the distance of the ultrasonic detection
    print(UT_distance) # cm
    time.sleep(0.1)