import network
import socket
import select
import time
import libs.ultrasonic
import libs.vehicle
from machine import Pin, PWM, Timer, ADC
import random
from libs.ACB_CAR_ARM import *
import uasyncio as asyncio
import libs.ACB_CAR_ARM

left_track_sensor = 35
center_track_sensor = 36
right_track_sensor = 39
Trig_PIN = 13
Echo_PIN = 14

adc1 = ADC(left_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc1.width(ADC.WIDTH_12BIT)
adc1.atten(ADC.ATTN_11DB)
adc2 = ADC(right_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc2.width(ADC.WIDTH_12BIT)
adc2.atten(ADC.ATTN_11DB)
adc3 = ADC(center_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc3.width(ADC.WIDTH_12BIT)
adc3.atten(ADC.ATTN_11DB)

speeds = 190
Black_Line = 2000
Off_Road = 4000

val = 0

PTP_X = 0
PTP_Y = 0
PTP_Z = 0

# Command Constants
CMD_RUN = 1
CMD_GET = 2
CMD_STANDBY = 3
CMD_TRACK_1 = 4
CMD_TRACK_2 = 5
CMD_AVOID = 6
CMD_FOLLOW = 7

data = None

Ultrasonic = libs.ultrasonic.ACB_Ultrasonic(Trig_PIN,Echo_PIN)

car = libs.vehicle.ACB_Vehicle()

previousMillis = time.ticks_ms()
timeoutDuration = 3000

# Function Mode Constants
FUNCTION_MODES = {
    1: "STANDBY",
    2: "FOLLOW",
    3: "TRACK_1",
    4: "TRACK_2",
    5: "AVOID"
}

ssid = "Robot_Arm_Car"   # Set WIFI name
password = "12345678"    # Set WIFI password
port = 100               # Setting the server port
http_port = 80           # Setting the HTTP server port

# Initialize other global variables
dataLen = 0
index_a = 0
buffer = bytearray(52)
prevc = 0
isStart = False
ED_client = True
WA_en = False
sendBuff = ""
val = 0
st = False

function_mode = "STANDBY"
tcp_server = None
http_server = None
clients = []

# Define the GPIO pin numbers connected to different parts of the robotic arm
chassis_pin = 25    # Chassis control pin
shoulder_pin = 26      # Elbow control pin
elbow_pin = 27   # Shoulder control pin
wrist_pin = 33      # Claws control pin
claws_pin = 4       # Wrist control pin



def readBuffer(index):
    return buffer[index]

def writeBuffer(index, c):
    buffer[index] = c

def setup():
    global tcp_server, http_server
    car.move(car.Stop, 0)
    # Initialize the robotic arm with the specified pins
    ARM_init(chassis_pin, shoulder_pin, elbow_pin, wrist_pin, claws_pin)
    wifi = network.WLAN(network.AP_IF)
    wifi.active(True)
    wifi.config(essid=ssid, password=password, max_clients=5,authmode=network.AUTH_WPA2_PSK)
    print("Ready! Use 'http://{}' to connect".format(wifi.ifconfig()[0]))
    time.sleep(0.1)
    
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(('0.0.0.0', port))
    tcp_server.listen(1)
    
    http_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    http_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    http_server.bind(('0.0.0.0', http_port))
    http_server.listen(1)

def parse_query_string(query):
    global val, chassis_angle, shoulder_angle, elbow_angle, claws_angle, wrist_angle, \
        PTP_X, PTP_Y, PTP_Z
    variables = {}
    for param in query.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            variables[key] = value
            if key == 'val':
                val = int(value)
            if key == 's1':
                chassis_angle = int(value)
            if key == 's2':
                shoulder_angle = int(value)
            if key == 's3':
                elbow_angle = int(value)
            if key == 's4':
                claws_angle = int(value)
            if key == 's5':
                wrist_angle = int(value)
            if key == 's1':
                PTP_X = int(value)
            if key == 's2':
                PTP_Y = int(value)
            if key == 's3':
                PTP_Z = int(value)
                
    return variables

previousMillis = time.ticks_ms()
timeoutDuration = 3000

def handle_tcp_connection(client):
    global isStart, index_a, dataLen, prevc, st, ED_client,previousMillis,data,function_mode
    if (time.ticks_ms() - previousMillis) > timeoutDuration and data is None and st==True:
#         print("disconnect")
        function_mode = "STANDBY"
        car.move(car.Stop, 0)
    ready = select.select([client], [], [], 0.00000000001)
    if ready[0]:
        try:
            data = client.recv(1)

            if data:
                previousMillis = time.ticks_ms()
                
                c = data[0]
                st = False
                if c == 200:
                    st = True
                if c == 0x55 and not isStart:
                    if prevc == 0xff:
                        index_a = 1
                        isStart = True
                else:
                    prevc = c
                    if isStart:
                        if index_a == 2:
                            dataLen = c
                        elif index_a > 2:
                            dataLen -= 1
                        writeBuffer(index_a, c)
                index_a += 1
                if index_a > 120:
                    index_a = 0
                    isStart = False
                if isStart and dataLen == 0 and index_a > 3:
                    isStart = False
                    parse_data()
                    index_a = 0
        except OSError as e:
#             print("disconnect")
            function_mode = "STANDBY"
            car.move(car.Stop, 0)#car.Stop   
        data = None
    functionMode()



def handle_http_connection(client):
#     request = client.recv(1024)
    request = b''
    
    # Iterate through client requests until all data has been received
    while True:
        part = client.recv(1024)
        request += part
        if len(part) < 1024:
            break
    request_str = request.decode('utf-8')

    if request_str.startswith('GET'):
        parts = request_str.split(' ', 2)

        if len(parts) < 2:
            raise ValueError("Invalid request format")

        _, path = parts[:2]

        if '?' in path:
            endpoint, query = path.split('?')
        else:
            endpoint = path
            query = ""

        if endpoint == '/control':
            variables = parse_query_string(query)
            val = variables.get('val')
            val = int(val)
            vals = int(val)
            if vals == 31 or vals == 35:
                response_data = "1"
#                 print(response_data).
                
                response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                client.send(response.encode('utf-8'))
            
            if vals == 40 or vals ==41:
                if libs.ACB_CAR_ARM.stateCount1 == 0:
                    response_data = "0"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
                else:
                    
                    response_data = "1"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
                    
                    
            if vals == 42:
                if libs.ACB_CAR_ARM.stateCount2 == 0:
                    response_data = "0"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
                else:
                    
                    response_data = "1"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
            
            if vals == 43:
                if libs.ACB_CAR_ARM.stateCount3 == 0:
                    response_data = "0"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
                else:
                    
                    response_data = "1"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
            
            if vals == 44:
                if libs.ACB_CAR_ARM.stateCount4 == 0:
                    response_data = "0"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
                else:
                    
                    response_data = "1"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
            
            if vals == 45:
                if libs.ACB_CAR_ARM.stateCount5 == 0:
                    response_data = "0"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
                else:
                    
                    response_data = "1"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
            
            if vals == 46:
                if libs.ACB_CAR_ARM.stateCount6 == 0:
                    response_data = "0"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))
                else:
                    
                    response_data = "1"
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_data)}\r\n\r\n{response_data}"
                    client.send(response.encode('utf-8'))

def functionMode():
    global function_mode
    if function_mode == "FOLLOW":
        model3_func()
    elif function_mode == "TRACK_1":
        model1_func()
    elif function_mode == "TRACK_2":
        model4_func()
    elif function_mode == "AVOID":
        model2_func()

def parse_data():
    global function_mode
    action = readBuffer(9)
    device = readBuffer(10)
    if action == CMD_RUN:
        function_mode = "STANDBY"
        runModule(device)
    elif action == CMD_STANDBY:
        function_mode = "STANDBY"
        car.move(car.Stop, 255)
    elif action == CMD_TRACK_1:
        function_mode = "TRACK_1"
    elif action == CMD_TRACK_2:
        function_mode = "TRACK_2"
    elif action == CMD_AVOID:
        function_mode = "AVOID"
    elif action == CMD_FOLLOW:
        function_mode = "FOLLOW"
    else:
        pass


# Function for model 1 (line following)
def model1_func():
    Left_Tra_Value = adc1.read() #Read the value of left tracking sensor
    Right_Tra_Value = adc2.read()

    time.sleep(0.0005)
    #Both sensors are on the black line
    if Left_Tra_Value < Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Forward, 150) #Smart car forward
    
    #left sensor is on black line,right sensor is on white background
    elif Left_Tra_Value >= Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Contrarotate, 150) #Smart car turn left
    
    #right sensor is on black line,left sensor is on the white background
    elif Left_Tra_Value < Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Clockwise, 150) #Smart car turn right
    
    #Both sensors are on the white background
    elif Left_Tra_Value >= Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Stop, 0) #Smart car stop

def model4_func():
    
    Left_Tra_Value = adc1.read() 
    Right_Tra_Value = adc2.read()
    Middle_Tra_Value = adc3.read()
    time.sleep(0.0005)

    if Left_Tra_Value < Black_Line and Middle_Tra_Value >= Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Forward, 130)
        
    if Left_Tra_Value < Black_Line and Middle_Tra_Value >= Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Forward, 130)
    
    if Left_Tra_Value >= Black_Line and Middle_Tra_Value >= Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Forward, 130)
        
    elif Left_Tra_Value >= Black_Line and Middle_Tra_Value < Black_Line and Right_Tra_Value < Black_Line:
        car.move(car.Contrarotate, 180)
    
    elif Left_Tra_Value < Black_Line and Middle_Tra_Value < Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Clockwise, 180)
        
    elif Left_Tra_Value >= Black_Line and Middle_Tra_Value >= Black_Line and Right_Tra_Value >= Black_Line:
        car.move(car.Forward, 130)
    
# follow
def model3_func():
    UT_distance = Ultrasonic.get_distance()
    
    if UT_distance < 15:
        car.move(car.Backward, 200)
    elif 15 <= UT_distance and UT_distance <= 20:
        car.move(car.Stop, 0)
    elif 20 <= UT_distance and UT_distance <= 25:
        car.move(car.Forward, speeds-70)
    elif 25 <= UT_distance and UT_distance <= 50:
        car.move(car.Forward, 220)
    else:
        car.move(car.Stop, 0)

#avoid
def model2_func():
    UT_distance = Ultrasonic.get_distance()
    middle_distance = UT_distance
    
    if middle_distance <= 25:
        car.move(car.Stop, 0)
        time.sleep(0.1)
        rand_number = random.randint(1, 4)
        if rand_number == 1:
            car.move(car.Backward, 180)
            time.sleep(0.5)
            car.move(car.Move_Left, 180)
            time.sleep(0.5)
        elif rand_number == 2:
            car.move(car.Clockwise, 180)
            time.sleep(1)
        elif rand_number == 3:
            car.move(car.Contrarotate, 180)
            time.sleep(1)
        elif rand_number == 4:
            car.move(car.Backward, 180)
            time.sleep(0.5)
            car.move(car.Move_Right, 180)
            time.sleep(0.5)
    else:
        car.move(car.Forward, 180)
    time.sleep(0.1)
        
    
def runModule(device):
    global speeds
    val = readBuffer(12)
    if device == 0x0C:
        if val == 0x01:
            car.move(car.Forward, speeds)
        elif val == 0x02:
            car.move(car.Backward, speeds)
        elif val == 0x03:
            car.move(car.Move_Left, speeds)
        elif val == 0x04:
            car.move(car.Move_Right, speeds)
        elif val == 0x05:
            car.move(car.Top_Left, speeds)
        elif val == 0x06:
            car.move(car.Bottom_Left, speeds)
        elif val == 0x07:
            car.move(car.Top_Right, speeds)
        elif val == 0x08:
            car.move(car.Bottom_Right, speeds)
        elif val == 0x0A:
            car.move(car.Clockwise, speeds)
        elif val == 0x09:
            car.move(car.Contrarotate, speeds)
        elif val == 0x00:
            car.move(car.Stop, 0)

    elif device == 0x0D:
        speeds = val
        print(val)

setup()
        
while True:
    global mode
    ready = select.select([tcp_server, http_server], [], [], 0.00000000001)
    if ready[0]:
        if http_server in ready[0]:
            client, _ = http_server.accept()
            handle_http_connection(client)
            
        if tcp_server in ready[0]:
            client, _ = tcp_server.accept()
            clients.append(client)
    
        
    if val == 21:
        chassis_cmd(chassis_angle)
        val = 3
    elif val == 22:
        shoulder_cmd(shoulder_angle)
        shoulder_angle = shoulder_angle
        val = 3
    elif val == 23:
        elbow_cmd(elbow_angle)
        val = 3
    elif val == 24:
        claws_cmd(claws_angle)
        val = 3
    elif val == 29:
        wrist_cmd(wrist_angle)
        val = 3
    
    elif val == 25:
        silde_chassisCmd(chassis_angle)
        val = 3
    elif val == 26:
        silde_shoulderCmd(shoulder_angle)
        val = 3
    elif val == 27:
        silde_elbowCmd(elbow_angle)
        val = 3
    elif val == 28:
        silde_clawsCmd(claws_angle)
        val = 3
    elif val == 30:
        silde_wristCmd(wrist_angle)
        val = 3
    
    elif val == 31 and record:
        saveState()
        val = 3
    elif val == 32:
        record = True
    elif val == 33:
        record = False
    elif val == 34 and record==False:
        executeStates()
        val = 3
    elif val == 35 and record:
        clearSavedStates()
        val = 3
    
#     elif val == 40:
#         mode = 0
    elif val == 41:
        libs.ACB_CAR_ARM.mode = 1
        val = 3
    elif val == 42:
        libs.ACB_CAR_ARM.mode = 2
    elif val == 43:
        libs.ACB_CAR_ARM.mode = 3
    elif val == 44:
        libs.ACB_CAR_ARM.mode = 4
    elif val == 45:
        libs.ACB_CAR_ARM.mode = 5
    elif val == 46:
        libs.ACB_CAR_ARM.mode = 6
    
    elif val == 70:
        Zero()
        val = 3
    
    elif val == 54:
        PtpCmd(PTP_X,PTP_Y,PTP_Z)
        val = 3
    
    
    for client in clients:
        handle_tcp_connection(client)





