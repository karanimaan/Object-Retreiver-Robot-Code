from libs.ACB_CAR_ARM import *

# Define the GPIO pin numbers connected to different parts of the robotic arm
chassis_pin = 25    # Chassis control pin
shoulder_pin = 26      # Elbow control pin
elbow_pin = 27   # Shoulder control pin
wrist_pin = 33      # Claws control pin
claws_pin = 4       # Wrist control pin

print('okay')
time.sleep(1)

# Initialize the robotic arm with the specified pins
ARM_init(chassis_pin, shoulder_pin, elbow_pin, wrist_pin, claws_pin)
print('elbow')
time.sleep(1)
elbow_cmd(150)
time.sleep(1)


'''
PtpCmd(0, 10, 3)
time.sleep(1)

claws_cmd(110)
time.sleep(1)

PtpCmd(0, 10, 4)
time.sleep(1)

print('done')
'''