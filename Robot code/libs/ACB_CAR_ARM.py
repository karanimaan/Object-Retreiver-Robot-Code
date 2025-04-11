from machine import Pin, PWM
import usocket as socket
import machine
import json
import time
import math

Error_Pos = 0  # Initialize error position for chassis
Error_left_poss = 0  # Initialize error for left position
Error_right_poss = 0  # Initialize error for right position

# Set initial angles for servos
chassis_angle = 90
shoulder_angle = 40
elbow_angle = 50
claws_angle = 90
wrist_angle = 90

# Initialize servo variables
servo1 = None
servo2 = None
servo3 = None
servo4 = None
servo5 = None

mode = 1 # Initialize mode variable

limit_z = 1 # Initialize limit for z-axis

record = False  # Initialize recording state
    
SERVOMIN = 500  # Minimum PWM value for servos
SERVOMAX = 2500  # Maximum PWM value for servos

PWMRES_Min = 0  # Minimum PWM resolution
PWMRES_Max = 1023  # Maximum PWM resolution

arm1_length = 11   # Length of arm 1
arm2_length = 7.5  # Lexngth of arm 2 
arm3_length = 17.5  # Length of arm 3

maxStates = 20  # Maximum number of states to save
stateCount1 = 0  # Counter for state 1
stateCount2 = 0  # Counter for state 2
stateCount3 = 0  # Counter for state 3
stateCount4 = 0  # Counter for state 4
stateCount5 = 0  # Counter for state 5
stateCount6 = 0  # Counter for state 6

class ServoState:
    global pos1,pos2,pos3,pos4,pos5
    def __init__(self):
        self.pos1 = 0
        self.pos2 = 0
        self.pos3 = 0
        self.pos4 = 0
        self.pos5 = 0

states = [ServoState() for _ in range(20)]
states1 = [ServoState() for _ in range(20)]
states2 = [ServoState() for _ in range(20)]
states3 = [ServoState() for _ in range(20)]
states4 = [ServoState() for _ in range(20)]
states5 = [ServoState() for _ in range(20)]
states6 = [ServoState() for _ in range(20)]


class Servo:
    pwm_max = 2500
    pwm_min = 500
    period = 65535  # 0xFFFF
    
    def __init__(self, pin):
        self.pwm = PWM(Pin(pin, Pin.OUT))  # Initialize PWM on specified pin
        self.pwm.freq(50)  # Set PWM frequency to 50 Hz
        self.current_angle = None  # Initialize current angle 
    
    def set_angle(self, angle):
        angle = max(0, min(180, angle))
        self.current_angle = angle
        high_level_time = (angle / 180) * (self.pwm_max - self.pwm_min) + self.pwm_min 
        duty_cycle_value = int((high_level_time / 20000) * self.period)
        self.pwm.duty_u16(duty_cycle_value)
        
    def read_angle(self):
        return self.current_angle  # Return current angle

# servo init
def ARM_init(chassis_pin, shoulder_pin, elbow_pin, wrist_pin,claws_pin):
    global servo1, servo2, servo3, servo4, servo5
    servo1 = Servo(chassis_pin)
    time.sleep(0.1)
    servo2 = Servo(shoulder_pin)
    time.sleep(0.1)
    servo3 = Servo(elbow_pin)
    time.sleep(0.1)
    servo4 = Servo(wrist_pin)
    time.sleep(0.1)
    servo5 = Servo(claws_pin)
    time.sleep(0.1)
    '''
    # Move the steering gear to the specified Angle
    servo1.set_angle(chassis_angle)
    servo2.set_angle(shoulder_angle)
    servo3.set_angle(elbow_angle)
    servo4.set_angle(wrist_angle)
    servo5.set_angle(claws_angle)
'''
# init servo angle
def Zero():
    servo1.set_angle(90+Error_Pos)
    servo2.set_angle(40)
    servo3.set_angle(50)
    servo4.set_angle(90)
    servo5.set_angle(90)
    
def chassis_cmd(angle):
    speed = 20
    angle = max(0, min(180, angle))
    servo1.current_angle = angle
    high_level_time = (angle / 180) * (servo1.pwm_max - servo1.pwm_min) + servo1.pwm_min 
    duty_cycle_value = int((high_level_time / 20000) * servo1.period)
    current_duty_cycle = servo1.pwm.duty_u16()

    for step in range(speed):
        target_duty_cycle = int(current_duty_cycle + (duty_cycle_value - current_duty_cycle) * (step / float(speed)))
        servo1.pwm.duty_u16(target_duty_cycle)
        time.sleep_ms(speed)
        
def shoulder_cmd(angle):
    speed = 20
    angle = max(0, min(180, angle))
    servo2.current_angle = angle
    high_level_time = (angle / 180) * (servo2.pwm_max - servo2.pwm_min) + servo2.pwm_min 
    duty_cycle_value = int((high_level_time / 20000) * servo2.period)
    current_duty_cycle = servo2.pwm.duty_u16()

    for step in range(speed):
        target_duty_cycle = int(current_duty_cycle + (duty_cycle_value - current_duty_cycle) * (step / float(speed)))
        servo2.pwm.duty_u16(target_duty_cycle)
        time.sleep_ms(speed)
        

def elbow_cmd(angle):
    speed = 20
    angle = max(0, min(180, angle))
    servo3.current_angle = angle
    high_level_time = (angle / 180) * (servo3.pwm_max - servo3.pwm_min) + servo3.pwm_min 
    duty_cycle_value = int((high_level_time / 20000) * servo3.period)
    current_duty_cycle = servo3.pwm.duty_u16()

    for step in range(speed):
        target_duty_cycle = int(current_duty_cycle + (duty_cycle_value - current_duty_cycle) * (step / float(speed)))
        servo3.pwm.duty_u16(target_duty_cycle)
        time.sleep_ms(speed)

def wrist_cmd(angle):
    speed = 20
    angle = max(0, min(180, angle))
    servo4.current_angle = angle
    high_level_time = (angle / 180) * (servo4.pwm_max - servo4.pwm_min) + servo4.pwm_min 
    duty_cycle_value = int((high_level_time / 20000) * servo4.period)
    current_duty_cycle = servo4.pwm.duty_u16()

    for step in range(speed):
        target_duty_cycle = int(current_duty_cycle + (duty_cycle_value - current_duty_cycle) * (step / float(speed)))
        servo4.pwm.duty_u16(target_duty_cycle)
        time.sleep_ms(speed)

def claws_cmd(angle):
    speed = 20
    angle = max(90, min(180, angle))
    servo5.current_angle = angle
    high_level_time = (angle / 180) * (servo5.pwm_max - servo5.pwm_min) + servo5.pwm_min 
    duty_cycle_value = int((high_level_time / 20000) * servo5.period)
    current_duty_cycle = servo5.pwm.duty_u16()

    for step in range(speed):
        target_duty_cycle = int(current_duty_cycle + (duty_cycle_value - current_duty_cycle) * (step / float(speed)))
        servo5.pwm.duty_u16(target_duty_cycle)
        time.sleep_ms(speed)
        
#silde control
def silde_chassisCmd(angle):
    global chassis_angle
    if angle > 180:  
        angle = 180
    if angle < 0:   
        angle = 0
    chassis_angle = angle
    servo1.set_angle(chassis_angle)
    
def silde_shoulderCmd(angle):
    global shoulder_angle
    if angle > 180:  
        angle = 180
    if angle < 0:   
        angle = 0
    shoulder_angle = angle
    limitZ(shoulder_angle,elbow_angle)
    if limit_z <= 1:
#         print("c")
        return
    else:
        servo2.set_angle(shoulder_angle)

def silde_elbowCmd(angle):
    global elbow_angle
    if angle > 180:  
        angle = 180
    if angle < 0:   
        angle = 0
    elbow_angle = angle
    limitZ(shoulder_angle,elbow_angle)
    if limit_z <= 1:
#         print("c")
        return
    else:
        servo3.set_angle(elbow_angle)

def silde_clawsCmd(angle):
    global claws_angle
    if angle > 180:  
        angle = 180
    if angle < 90:   
        angle = 90
    claws_angle = angle
    servo5.set_angle(claws_angle)

def silde_wristCmd(angle):
    if angle > 180:  
        angle = 180
    if angle < 0:   
        angle = 0
    wrist_angle = angle
    servo4.set_angle(wrist_angle)

def limitZ(pos__2, pos__3):
    global limit_z
    angle2 = pos__2
    angle3 = pos__3
    
    # Calculate the radian value of the joint Angle
    rad2 = math.radians(angle2)
    rad3 = math.radians(180 - angle3)

    # Calculate the coordinates of joint 2
    x2 = arm2_length * math.cos(rad2)
    z2 = arm2_length * math.sin(rad2)

    # Calculate the coordinates of the end effector
    x = x2 + arm3_length * math.cos(rad2 + rad3)
    limit_z = z2 + arm3_length * math.sin(rad2 + rad3) + 14

def saveState():
    global mode,stateCount1,stateCount2,stateCount3,stateCount4,stateCount5,stateCount6
#     print(mode)
    if mode == 1:    # Selection mode
        if stateCount1 < maxStates:   # Check whether the number of states is smaller than the maximum number
            states1[stateCount1].pos1 = chassis_angle   # Save state
            states1[stateCount1].pos2 = shoulder_angle
            states1[stateCount1].pos3 = elbow_angle
            states1[stateCount1].pos4 = claws_angle
            states1[stateCount1].pos5 = wrist_angle
            stateCount1 =  stateCount1 + 1
#             print("State1 saved")
        else:
            print("Cannot save more states")
    elif mode == 2:
        if stateCount2 < maxStates:
            states2[stateCount2].pos1 = chassis_angle
            states2[stateCount2].pos2 = shoulder_angle
            states2[stateCount2].pos3 = elbow_angle
            states2[stateCount2].pos4 = claws_angle
            states2[stateCount2].pos5 = wrist_angle
            stateCount2 += 1
#             print("State2 saved")
        else:
            print("Cannot save more states")
    elif mode == 3:
        if stateCount3 < maxStates:
            states3[stateCount3].pos1 = chassis_angle
            states3[stateCount3].pos2 = shoulder_angle
            states3[stateCount3].pos3 = elbow_angle
            states3[stateCount3].pos4 = claws_angle
            states3[stateCount3].pos5 = wrist_angle
            stateCount3 += 1
#             print("State3 saved")
        else:
            print("Cannot save more states")
    elif mode == 4:
        if stateCount4 < maxStates:
            states4[stateCount4].pos1 = chassis_angle
            states4[stateCount4].pos2 = shoulder_angle
            states4[stateCount4].pos3 = elbow_angle
            states4[stateCount4].pos4 = claws_angle
            states4[stateCount4].pos5 = wrist_angle
            stateCount4 += 1
#             print("State4 saved")
        else:
            print("Cannot save more states")
    elif mode == 5:
        if stateCount5 < maxStates:
            states5[stateCount5].pos1 = chassis_angle
            states5[stateCount5].pos2 = shoulder_angle
            states5[stateCount5].pos3 = elbow_angle
            states5[stateCount5].pos4 = claws_angle
            states5[stateCount5].pos5 = wrist_angle
            stateCount5 += 1
#             print("State5 saved")
        else:
            print("Cannot save more states")
    elif mode == 6:
        if stateCount6 < maxStates:
            states6[stateCount6].pos1 = chassis_angle
            states6[stateCount6].pos2 = shoulder_angle
            states6[stateCount6].pos3 = elbow_angle
            states6[stateCount6].pos4 = claws_angle
            states6[stateCount6].pos5 = wrist_angle
            stateCount6 += 1
#             print("State6 saved")
        else:
            print("Cannot save more states")
    else:
        print("No mode")

def executeStates():
    global mode,stateCount1,stateCount2,stateCount3,stateCount4,stateCount5,stateCount6
    if mode == 1:
        for state in range(stateCount1):
            chassis_angle = states1[state].pos1
            shoulder_angle = states1[state].pos2
            elbow_angle = states1[state].pos3
            claws_angle = states1[state].pos4
            wrist_angle = states1[state].pos5
            
            chassis_cmd(chassis_angle)
            shoulder_cmd(shoulder_angle)
            elbow_cmd(elbow_angle)
            claws_cmd(claws_angle)
            wrist_cmd(wrist_angle)
    elif mode == 2:
        for state in range(stateCount2):
            chassis_angle = states2[state].pos1
            shoulder_angle = states2[state].pos2
            elbow_angle = states2[state].pos3
            claws_angle = states2[state].pos4
            wrist_angle = states2[state].pos5
            
            chassis_cmd(chassis_angle)
            shoulder_cmd(shoulder_angle)
            elbow_cmd(elbow_angle)
            claws_cmd(claws_angle)
            wrist_cmd(wrist_angle)
    elif mode == 3:
        for state in range(stateCount3):
            chassis_angle = states3[state].pos1
            shoulder_angle = states3[state].pos2
            elbow_angle = states3[state].pos3
            claws_angle = states3[state].pos4
            wrist_angle = states3[state].pos5
            
            chassis_cmd(chassis_angle)
            shoulder_cmd(shoulder_angle)
            elbow_cmd(elbow_angle)
            claws_cmd(claws_angle)
            wrist_cmd(wrist_angle)
    elif mode == 4:
        for state in range(stateCount4):
            chassis_angle = states4[state].pos1
            shoulder_angle = states4[state].pos2
            elbow_angle = states4[state].pos3
            claws_angle = states4[state].pos4
            wrist_angle = states4[state].pos5
            
            chassis_cmd(chassis_angle)
            shoulder_cmd(shoulder_angle)
            elbow_cmd(elbow_angle)
            claws_cmd(claws_angle)
            wrist_cmd(wrist_angle)
    elif mode == 5:
        for state in range(stateCount5):
            chassis_angle = states5[state].pos1
            shoulder_angle = states5[state].pos2
            elbow_angle = states5[state].pos3
            claws_angle = states5[state].pos4
            wrist_angle = states5[state].pos5
            
            chassis_cmd(chassis_angle)
            shoulder_cmd(shoulder_angle)
            elbow_cmd(elbow_angle)
            claws_cmd(claws_angle)
            wrist_cmd(wrist_angle)
    elif mode == 6:
        for state in range(stateCount6):
            chassis_angle = states6[state].pos1
            shoulder_angle = states6[state].pos2
            elbow_angle = states6[state].pos3
            claws_angle = states6[state].pos4
            wrist_angle = states6[state].pos5
            
            chassis_cmd(chassis_angle)
            shoulder_cmd(shoulder_angle)
            elbow_cmd(elbow_angle)
            claws_cmd(claws_angle)
            wrist_cmd(wrist_angle)
    
def clearSavedStates():
    global mode,stateCount1,stateCount2,stateCount3,stateCount4,stateCount5,stateCount6
    if mode == 1:
        stateCount1 = 0
    elif mode == 2:
        stateCount2 = 0
    elif mode == 3:
        stateCount3 = 0
    elif mode == 4:
        stateCount4 = 0
    elif mode == 5:
        stateCount5 = 0
    elif mode == 6:
        stateCount6 = 0
#     pass
    
def PtpCmd(x, y, z):
    global chassis_angle
    pi = 3.141592653589793
    L0 = 1100
    L1 = 750
    L2 = 1750
    sphereCenter = [0, 0, 11]
    r_max = 25
    distance_max = ((x - sphereCenter[0]) ** 2 + (y - sphereCenter[1]) ** 2 + (z - sphereCenter[2]) ** 2) ** 0.5
    r_min = 12
    distance_min = ((x - sphereCenter[0]) ** 2 + (y - sphereCenter[1]) ** 2 + (z - sphereCenter[2]) ** 2) ** 0.5

    if x > 25 or x < -25:
        print("Exceeds the value range of x.")
        return
    elif y > 25 or y < 0:
        print("Exceeds the value range of y.")
        return
    elif z > 36 or z < 0:
        print("Exceeds the value range of z.")
        return
    elif x == 0 and y == 0 and z < 28:
        print("Exceeds the value range of z.")
        return
    elif distance_max > r_max:
        print("Out of range!")
        return
    elif distance_min < r_min:
        print("Out of range!")
        return
    else:
        Alpha = 0
        if x == 0 and y != 0:
            y = y - 1
            z = z - 2
            chassis_angle =  90 + Error_Pos 
            chassis_cmd(chassis_angle)

        elif x > 0 and y == 0:
            x = x - 1
            z = z - 2
            chassis_cmd(0)
            chassis_angle = 0
        elif x < 0 and y == 0:
            x = x + 1
            z = z - 2
            chassis_cmd(180)
            chassis_angle = 180
        elif x == 0 and y == 0:
            z = z - 2
            chassis_angle =  90 + Error_Pos 
            chassis_cmd(chassis_angle)
#             chassis_angle = chassis_pos1
        else:
            if x > 0:
                x = x + 1
                y = y - 1
            else:
                x = x - 1
                y = y - 1
            xz_angle1 = (math.atan(x / y) * 180.0 / pi) + 90
            if xz_angle1 < 90:
                xz_angle1 = 180 - xz_angle1 + Error_Pos + Error_right_poss
            else:
                xz_angle1 = 180 - xz_angle1 + Error_Pos + Error_left_poss
            chassis_cmd(xz_angle1)
            chassis_angle = xz_angle1
    time.sleep(0.2)
    x = x * 100
    y = y * 100
    z = z * 100
    y = ((x ** 2 + y ** 2) ** 0.5)  # Hypotenuse of the x and y coordinates
    z = z - L0  # - L3 * math.sin(Alpha * pi / 180.0)
    if z < -L0:
        pass
    if math.sqrt(y ** 2 + z ** 2) > (L1 + L2):
        pass
    ccc = math.acos(y / math.sqrt(y ** 2 + z ** 2))
    bbb = (y ** 2 + z ** 2 + L1 ** 2 - L2 ** 2) / (2 * L1 * math.sqrt(y ** 2 + z ** 2))
    if bbb > 1 or bbb < -1:
        pass
    zf_flag = -1 if z < 0 else 1
    servo_angle2 = ccc * zf_flag + math.acos(bbb)  # Calculate the arc of steering gear 2
    servo_angle2 = servo_angle2 * 180.0 / pi  # Conversion Angle
    servo_angle2 = 180 - servo_angle2
    if servo_angle2 > 180.0 or servo_angle2 < 0.0:
        pass
    aaa = -(y ** 2 + z ** 2 - L1 ** 2 - L2 ** 2) / (2 * L1 * L2)
    if aaa > 1 or aaa < -1:
        pass
    servo_angle3 = math.acos(aaa)
    servo_angle3 = servo_angle3 * 180.0 / pi
    if servo_angle3 > 135.0 or servo_angle3 < -135.0:
        pass
    servo_angle4 = Alpha - servo_angle2 + servo_angle3
    if servo_angle4 > 90.0 or servo_angle4 < -90.0:
        pass
    elbow_cmd(servo_angle3)
    elbow_angle = servo_angle3
    time.sleep(0.1)
    shoulder_cmd(servo_angle2)
    shoulder_angle = servo_angle2
    
def Chassis_angle_adjust(chassis_pos):
    global Error_Pos, chassis_angle
    Error_Pos = chassis_pos
    chassis_angle = 90 + Error_Pos

def Slight_adjust(left_pos,right_pos):
    global right_poss,left_poss
    right_poss = right_pos
    left_poss = left_pos
    





