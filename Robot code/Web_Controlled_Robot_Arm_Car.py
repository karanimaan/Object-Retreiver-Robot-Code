import socket
import network
import time
from machine import Pin,ADC
from libs.ACB_CAR_ARM import *
import libs.ACB_CAR_ARM
import libs.ultrasonic
import libs.vehicle
import _thread
import random

Trig_PIN = 13
Echo_PIN = 14
left_track_sensor = 35
center_track_sensor = 36
right_track_sensor = 39
speeds = 190
Black_Line = 2000
Off_Road = 4000

# Initialize ultrasonic sensor and vehicle
Ultrasonic = libs.ultrasonic.ACB_Ultrasonic(Trig_PIN,Echo_PIN)
car = libs.vehicle.ACB_Vehicle()

# Initialize variables for controlling the robotic arm
val = 0
PTP_X = 0
PTP_Y = 0
PTP_Z = 0

# Define the GPIO pin numbers connected to different parts of the robotic arm
chassis_pin = 25    # Chassis control pin
shoulder_pin = 26      # Elbow control pin
elbow_pin = 27   # Shoulder control pin
wrist_pin = 33      # Claws control pin
claws_pin = 4       # Wrist control pin



adc1 = ADC(left_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc1.width(ADC.WIDTH_12BIT)
adc1.atten(ADC.ATTN_11DB)
adc2 = ADC(right_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc2.width(ADC.WIDTH_12BIT)
adc2.atten(ADC.ATTN_11DB)
adc3 = ADC(center_track_sensor)  # Replace 0 with the appropriate ADC pin number
adc3.width(ADC.WIDTH_12BIT)
adc3.atten(ADC.ATTN_11DB)

record = False

ssid = "Robot_Arm_Car"   # Set WIFI name
password = "12345678"    # Set WIFI password

def setup():
    # Initialize the robotic arm with the specified pins
    car.move(car.Stop, 0)
    ARM_init(chassis_pin, shoulder_pin, elbow_pin, wrist_pin, claws_pin)
    
# Connect to Wi-Fi
def connect():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password,authmode=network.AUTH_WPA2_PSK)
    print('Access Point created. Network config:', ap.ifconfig())

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

# Function for model 3 (follow)
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

# Function for model 2 (obstacle avoidance)
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


# Handle client requests
def handle_client(connection):
    global val
    
    try: 
        query_params = connection.recv(1024).decode('utf-8')
        response = 'HTTP/1.1 404 Not Found\n\nPage not found'
            
        if 'GET /control' in query_params:
             # Parse query parameters
            params = query_params.split(' ')[1].split('?')
            if len(params) > 1:
                query_str = params[1]
                query_params = dict(param.split('=') for param in query_str.split('&'))
                val = int(query_params.get('val', val))
#                 print(val)
                
                if val:
                    
                    handle_control(query_params)

                # Construct response
                response = 'HTTP/1.1 200 OK\nContent-Type: text/html\n\n<html><body>Control Command Received</body></html>'
            else:
                response = 'HTTP/1.1 400 Bad query_params\n\nInvalid query_params'
        
     
        if 'GET /' in query_params:
            response = '''HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
      <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width,initial-scale=1">
          <title>ACEBOTT QD001 ESP32 ROBOT CAR ARM</title>
          <style>

            html {
              touch-action:none;

              touch-action:pan-y;
            }

            body {
              -webkit-user-select: none;
              -moz-user-select: none;
              -ms-user-select: none;
              user-select: none;
              
            }

            input[type=range] {
                -webkit-appearance: none;
                width: 80%;
                height: 10px;
                background: #ccc;
                cursor: pointer;
                margin: 10px;
            }

            input[type=range]::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 20px;
                height: 20px;
                background: #ff3034;
                cursor: pointer;
                border-radius: 50%;
            }

              *{
                  padding: 0; margin: 0;
                  font-family:monospace;
              }

              *{  
                  -webkit-touch-callout:none;  
                  -webkit-user-select:none;  
                  -khtml-user-select:none;  
                  -moz-user-select:none;  
                  -ms-user-select:none;  
                  user-select:none;  
              }

          canvas {
          margin: auto;
          display: block;

          }
          .tITULO{
              text-align: center;
              color: rgb(97, 97, 97);
              
          }
          .LINK{
              color: red;
              width: 60px;
              margin: auto;
              display: block;
              font-size: 14px;
          }
          .cont_flex{
              margin: 20px auto 20px;
              width: 70%;
              max-width: 400px;
              display: flex;
              flex-wrap: wrap;
              justify-content: space-around;
          }
          .cont_flex4{
              margin: 20px auto 20px;
              width: 70%;
              max-width: 400px;
              display: flex;
              flex-wrap: wrap;
              justify-content: space-around;
          }
          .cont_flex4 button{
              width: 80px;
              height: 35px;
              border: none;
              background-color: #3D9EFF;
              border-radius: 10px;
              color: white;

          }
          .cont_flex5{
              margin: 15px auto 5px;
              width: 100%;
              max-width: 400px;
              display: flex;
              flex-wrap: wrap;
              justify-content: space-around;
          }
          .cont_flex5 button{
              width: 280px;
              height: 35px;
              border: none;
              background-color: #3D9EFF;
              border-radius: 10px;
              color: white;

          }
          .cont_flex button{
              width: 80px;
              height: 35px;
              border: none;
              background-color: #0080FF;
              border-radius: 10px;
              color: white;

          }
          .cont_flex button:active{
              background-color: green;
          }
          .cont_flex4 button:active{
              background-color: green;
          }

          .cont_flex1{
              margin: 20px auto 20px;
              width: 70%;
              max-width: 400px;
              display: flex;
              flex-wrap: wrap;
              justify-content: space-around;
          }
          .cont_flex1 button{
              width: 55px;
              height: 30px;
              border: none;
              background-color: #0080FF;
              border-radius: 10px;
              color: white;

          }
          .cont_flex1 button:active{
              background-color: green;
          }

          .cont_flex3 {
            display: flex;
            flex-direction: column;
            align-items: center;
          }
          .slider_container {
            padding-top: 5px; 
          }

          .slider_container1 {
              padding-left: 10px; 
          }

          .cont_flex_hua {
              margin: 20px auto 20px;
              width: 85%;
              max-width: 1000px;
              display: flex;
              flex-wrap: wrap;
              justify-content: space-around;
          }
          .cont_flex_hua p {
              flex: 0 0 auto; 
              width: 65px; 
              margin: 5px;
              box-sizing: border-box;
              padding-bottom: 3px;
          }
          .cont_flex_hua input {
              flex: 1 1 auto;
              box-sizing: border-box;
          }
          @media screen and (max-width: 600px) {
              .cont_flex_hua .input_wrapper {
                  width: 100%;
              }
          }

          .custom-alert {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: lightskyblue;
            padding: 20px;
            border: 1px solid gray;
            border-radius: 5px;
            animation: fadeInOut 2s ease-in-out forwards;
            opacity: 0; 
            visibility: hidden; 
            }

          input{-webkit-user-select:auto;} 
          input[type=range]{-webkit-appearance:none;width:300px;height:25px;background:#cecece;cursor:pointer;margin:0}
          input[type=range]:focus{outline:0}
          input[type=range]::-webkit-slider-runnable-track{width:100%;height:2px;cursor:pointer;background:#EFEFEF;border-radius:0;border:0 solid #EFEFEF}
          input[type=range]::-webkit-slider-thumb{border:1px solid rgba(0,0,30,0);height:22px;width:22px;border-radius:50px;background:#ff3034;cursor:pointer;-webkit-appearance:none;margin-top:-10px}

          </style>
      </head>
      <body>
          <div id="customAlert" class="custom-alert">
            <p id="alertText" style="color: white; font-size: 15px;"></p>
          </div>

          <p style="color: black; display: flex; justify-content: center; align-items: center; font-size: 25px;">Smart Car</p>   

          <div class="cont_flex4">     
              <button type="button" id="Turn_Left" ontouchstart="fetch(document.location.origin+'/control?var=car&val=64');"ontouchend="fetch(document.location.origin+'/control?var=car&val=60');">Turn Left</button>

              <button type="button" id="UP" ontouchstart="fetch(document.location.origin+'/control?var=car&val=63');"ontouchend="fetch(document.location.origin+'/control?var=car&val=60');">Forward</button>

              <button type="button" id="Turn_Right" ontouchstart="fetch(document.location.origin+'/control?var=car&val=66');"ontouchend="fetch(document.location.origin+'/control?var=car&val=60');">Turn Right</button>
          </div>

          <div class="cont_flex4">     
              <button type="button" id="Left" ontouchstart="fetch(document.location.origin+'/control?var=car&val=61');"ontouchend="fetch(document.location.origin+'/control?var=car&val=60');">Left</button>

              <button type="button" id="Down" ontouchstart="fetch(document.location.origin+'/control?var=car&val=65');"ontouchend="fetch(document.location.origin+'/control?var=car&val=60');">Backward</button>

              <button type="button" id="Right" ontouchstart="fetch(document.location.origin+'/control?var=car&val=62');"ontouchend="fetch(document.location.origin+'/control?var=car&val=60');">Right</button> 
          </div>

          <div class="cont_flex4">     
              <button type="button" id="Turn_Left" ontouchstart="fetch(document.location.origin+'/control?var=car&val=67');" >Track</button>

              <button type="button" id="UP" ontouchstart="fetch(document.location.origin+'/control?var=car&val=68');">Follow</button>

              <button type="button" id="Turn_Right" ontouchstart="fetch(document.location.origin+'/control?var=car&val=69');">Avoidance</button>

              <div class="cont_flex5">  
                <button type="button" id="Stop" ontouchstart="fetch(document.location.origin+'/control?var=car&val=60');"ontouchend="fetch(document.location.origin+'/control?var=car&val=3');">Stop</button>
              </div>
              
          </div>

          <div style="display: flex; justify-content: center; align-items: center;">

              <p style="color: black;">Claws &nbsp; :</p>
              <input type="range" style="width: 200px;" id="slider4" min="90" max="180" value="90"  ontouchend="sendSliderValue44();" onmousedown="sendSliderValue44();" onchange="updateValue4(this.value);">
                
              <p id="sliderValue4" style="color: black; width: 25px; margin-left: 10px;" >90</p>
              <input type="text" id="inputValue4" onblur="checkEnter4(event)" style="width:80px;" placeholder="Enter Value" title="Enter a number between 90°and 180°">
          </div>

          <div style="display: flex; justify-content: center; align-items: center; padding-top: 10px;" >
              <p style="color: black;">Wrist &nbsp; :</p>
              <input type="range" style="width: 200px;" id="slider5" min="0" max="180" value="90"  ontouchend="sendSliderValue55();" onmousedown="sendSliderValue55();" onchange="updateValue5(this.value);">
              
              <p id="sliderValue5" style="color: black; width: 25px; margin-left: 10px;" >90</p>
              <input type="text" id="inputValue5" onblur="checkEnter5(event)" style="width:80px;" placeholder="Enter Value" title="Enter a number between 0°and 180°">
          </div>

          <div style="display: flex; justify-content: center; align-items: center; padding-top: 10px;" >
              <p style="color: black;">Elbow &nbsp; :</p>
              <input type="range" style="width: 200px;" id="slider3" min="0" max="180" value="90"  ontouchend="sendSliderValue33();" onmousedown="sendSliderValue33();" onchange="updateValue3(this.value);">
              
              <p id="sliderValue3" style="color: black; width: 25px; margin-left: 10px;" >50</p>
              <input type="text" id="inputValue3" onblur="checkEnter3(event)" style="width:80px;" placeholder="Enter Value" title="Enter a number between 0°and 180°">
          </div>

          <div style="display: flex; justify-content: center; align-items: center; padding-top: 10px;">
          <p style="color: black;">Shoulder:</p>
                <input type="range" style="width: 200px;" id="slider2" min="0" max="180" value="90" ontouchend="sendSliderValue22();" onmousedown="sendSliderValue22();" onchange="updateValue2(this.value);">
                
                <p id="sliderValue2" style="color: black; width: 25px; margin-left: 10px;">40</p>
                <input type="text" id="inputValue2" onblur="checkEnter2(event)" style="width:80px;" placeholder="Enter Value" title="Enter a number between 0°and 180°">
            </div>

          <div style="display: flex; justify-content: center; align-items: center; padding-top: 10px;">
          <p style="color: black;">Chassis :</p>
                <input type="range" style="width: 200px;" id="slider1" min="0" max="180" value="90"  ontouchend="sendSliderValue11();" onmousedown="sendSliderValue11();" onchange="updateValue1(this.value);">
                
                <p id="sliderValue1" style="color: black; width: 25px; margin-left: 10px;">90</p>
                <input type="text" id="inputValue1" onblur="checkEnter1(event)" style="width:80px;" placeholder="Enter Value" title="Enter a number between 0°and 180°">
            </div> 


          <p style="color: black; display: flex; justify-content: center; align-items: center; font-size: 25px;">Custom mode</p>

          <div style="display: flex; justify-content: center; align-items: center; padding-top:8px;">    
            <select id="ModeSelect" onchange="handleModeChange(this.value);">
              <!-- <option value="0">MODE</option> -->
              <option value="1">MODE 1</option>
              <option value="2">MODE 2</option>
              <option value="3">MODE 3</option>
              <option value="4">MODE 4</option>
              <option value="5">MODE 5</option>
              <option value="6">MODE 6</option>
            </select> 
          </div>

          <div class="cont_flex1">    
            
            <button type="button" id="Start_End">Start</button>

            <button type="button" id="Save" onclick="ButtonNote1()">Save</button>

            <button type="button" id="Start" onclick="ButtonNote3()">Run</button>

            <button type="button" id="Reset" onclick="ButtonNote2()">Reset</button>  
          </div>

          <p style="color: black; display: flex; justify-content: center; align-items: center; padding-bottom: 5px; font-size: 25px;">Spatial coordinate</p>

          <div style="display: flex; justify-content: center; align-items: center; padding-bottom:5px;"> 
              
              <p style="color: black; margin-right: 3px;">X:</p>
              <input type="text" style="width: 75px; margin-right: 3px;" id="inputX" placeholder="Enter Value" title="Note the value range when entering the X value"> 

              <p style="color: black; margin-right: 3px;">Y:</p>
              <input type="text" style="width: 75px; margin-right: 3px;" id="inputY" placeholder="Enter Value" title="Note the value range when entering the Y value"> 

              <p style="color: black; margin-right: 3px;">Z:</p>
              <input type="text" style="width: 75px; margin-right: 6px;" id="inputZ" placeholder="Enter Value" title="Note the value range when entering the Z value"> 

              <button type="button" id="Commit" style="width:60px; height: 30px;" onclick="sendValueDw()" ontouchend="fetch(document.location.origin+'/control?var=car&val=3');">Commit</button>

          </div>

          <p style="color: red; display: flex; justify-content: center; align-items: center;  font-size: 15px;">The value of x ranges from -25 to 25.<br>The value of y ranges from 0 to 25.<br>The value of z ranges from 0 to 36.</p>

          <p style="color: red; display: flex; justify-content: center; align-items: center; padding-bottom: 5px; font-size: 15px;">Note: The value range is the point within the sphere.</p>

          <script>
              var customAlert = document.getElementById("customAlert");
              var alertText = document.getElementById("alertText");
              function hideAlert() {
                    customAlert.style.opacity = "0";
                    customAlert.style.visibility = "hidden";
                }

              

              function ButtonNote1(){
                  var startEndButton = document.getElementById("Start_End");
                  if (startEndButton.textContent === "Start") {
                      alertText.textContent = "No start record, please click the Start button.";
                
                  } else {
                      alertText.textContent = "Record success";
                      fetch(document.location.origin+'/control?var=car&val=31');
                      fetch(document.location.origin+'/control?var=car&val=3');
                  }
                  customAlert.style.opacity = "1"; 
                  customAlert.style.visibility = "visible";
                  setTimeout(hideAlert, 1500);
              }

              function ButtonNote2(){
                  var startEndButton = document.getElementById("Start_End");
                  if (startEndButton.textContent === "End") {
                      alertText.textContent = "Now in record mode, please exit(End button) this mode and press Reset button again.";
                  } else {
                      alertText.textContent = "Reset success";
                      fetch(document.location.origin+'/control?var=car&val=35');
                      fetch(document.location.origin+'/control?var=car&val=3');
                  }
                  customAlert.style.opacity = "1"; 
                  customAlert.style.visibility = "visible";
                  setTimeout(hideAlert, 1500);
              }

              function ButtonNote3(){
                  var startEndButton = document.getElementById("Start_End");
                  if (startEndButton.textContent === "End") {
                    alertText.textContent = "Now in record mode, please exit(End button) this mode and press Run button again.";
                  } else{
                    alertText.textContent = "Run";
                    fetch(document.location.origin+'/control?var=car&val=34');
                    fetch(document.location.origin+'/control?var=car&val=3');
                  }
                  customAlert.style.opacity = "1"; 
                  customAlert.style.visibility = "visible";
                  setTimeout(hideAlert, 1500);

              }
              
              function sendValueDw(){
                var inputValue1 = document.getElementById("inputX").value;
                var inputValue2 = document.getElementById("inputY").value;
                var inputValue3 = document.getElementById("inputZ").value;
                
                if (isNaN(inputValue1) || inputValue1 == "") {
                    alertText.textContent = "Please enter a valid value for X.";
                    customAlert.style.opacity = "1"; 
                    customAlert.style.visibility = "visible";
                    setTimeout(hideAlert, 1500);
                    return; 
                }
                if (isNaN(inputValue2) || inputValue2 == "") {
                    alertText.textContent = "Please enter a valid value for Y.";
                    customAlert.style.opacity = "1"; 
                    customAlert.style.visibility = "visible";
                    setTimeout(hideAlert, 1500);
                    return; 
                }
                if (isNaN(inputValue3) || inputValue3 == "") {
                    alertText.textContent = "Please enter a valid value for Z.";
                    customAlert.style.opacity = "1"; 
                    customAlert.style.visibility = "visible";
                    setTimeout(hideAlert, 1500);
                    return; 
                }

                var xylen = 25;
                var zlen = 36
                
                if ( inputValue1 >xylen || inputValue1 < -xylen || inputValue2 > xylen || inputValue2 < 0 || inputValue3 >zlen || inputValue3 < 0) {
                    alertText.textContent = "Out of range!";
                    customAlert.style.opacity = "1"; 
                    customAlert.style.visibility = "visible";
                    setTimeout(hideAlert, 1500);
                    return; 
                }

                if ( inputValue1 == 0 && inputValue2 == 0 && inputValue3 < 28) {
                    alertText.textContent = "Out of range!";
                    customAlert.style.opacity = "1"; 
                    customAlert.style.visibility = "visible";
                    setTimeout(hideAlert, 1500);
                    return; 
                }
                
                var sphereCenter = [0, 0, 11];
                var radius = 25;
                var distance = Math.sqrt((inputValue1 - sphereCenter[0]) ** 2 + (inputValue2 - sphereCenter[1]) ** 2 + (inputValue3 - sphereCenter[2]) ** 2);
                if (distance > radius) {
                  alertText.textContent = "Out of range!";
                        customAlert.style.opacity = "1"; 
                        customAlert.style.visibility = "visible";
                        setTimeout(hideAlert, 1500);
                        return; 
                }

                
                var radius_min = 12;
                var distance_min = Math.sqrt((inputValue1 - sphereCenter[0]) ** 2 + (inputValue2 - sphereCenter[1]) ** 2 + (inputValue3 - sphereCenter[2]) ** 2);
                if (distance_min < radius_min) {
                  alertText.textContent = "Out of range!";
                        customAlert.style.opacity = "1"; 
                        customAlert.style.visibility = "visible";
                        setTimeout(hideAlert, 1500);
                        return; 
                }


                

                fetch(document.location.origin + '/control?var=car&val=51&ss1=' + inputValue1);
                fetch(document.location.origin + '/control?var=car&val=52&ss2=' + inputValue2);
                fetch(document.location.origin + '/control?var=car&val=53&ss3=' + inputValue3);
                alertText.textContent = "x:" + inputValue1 + ", y:" + inputValue2 + ", z:" + inputValue3;
                fetch(document.location.origin+'/control?var=car&val=54');
                customAlert.style.opacity = "1"; 
                customAlert.style.visibility = "visible";
                setTimeout(hideAlert, 1500);
              }
            

              function handleModeChange(mode) {
                switch(mode) {
                    case '0':
                      fetch(document.location.origin+'/control?var=car&val=40')
                      break;
                    case '1':
                      fetch(document.location.origin+'/control?var=car&val=41')
                      alertText.textContent = "Mode 1";
                      customAlert.style.opacity = "1"; 
                      customAlert.style.visibility = "visible";
                      setTimeout(hideAlert, 1500);
                      break;
                    case '2':
                      fetch(document.location.origin+'/control?var=car&val=42')
                      alertText.textContent = "Mode 2";
                      customAlert.style.opacity = "1"; 
                      customAlert.style.visibility = "visible";
                      setTimeout(hideAlert, 1500);
                      break;
                    case '3':
                      fetch(document.location.origin+'/control?var=car&val=43')
                      alertText.textContent = "Mode 3";
                      customAlert.style.opacity = "1"; 
                      customAlert.style.visibility = "visible";
                      setTimeout(hideAlert, 1500);
                      break;
                    case '4':
                      fetch(document.location.origin+'/control?var=car&val=44')
                      alertText.textContent = "Mode 4";
                      customAlert.style.opacity = "1"; 
                      customAlert.style.visibility = "visible";
                      setTimeout(hideAlert, 1500);
                      break;
                    case '5':
                      fetch(document.location.origin+'/control?var=car&val=45')
                      alertText.textContent = "Mode 5";
                      customAlert.style.opacity = "1"; 
                      customAlert.style.visibility = "visible";
                      setTimeout(hideAlert, 1500);
                      break;
                    case '6':
                      fetch(document.location.origin+'/control?var=car&val=46')
                      alertText.textContent = "Mode 6";
                      customAlert.style.opacity = "1"; 
                      customAlert.style.visibility = "visible";
                      setTimeout(hideAlert, 1500);
                      break;
                    default:
                      break;
                }
            }

              function updateValue1(value) {
                  document.getElementById("sliderValue1").textContent = value;
              }
              function updateValue2(value) {
                  document.getElementById("sliderValue2").textContent = value;
              }
              function updateValue3(value) {
                  document.getElementById("sliderValue3").textContent = value;
              }
              function updateValue4(value) {
                  document.getElementById("sliderValue4").textContent = value;
              }
              function updateValue5(value) {
                  document.getElementById("sliderValue5").textContent = value;
              }

              function updateSlider1(value) {
                  var slider = document.getElementById("slider1");
                  slider.value = value;
                  updateValue1(value);
              }
              function checkEnter1(event) {
                  
                      var inputValue = document.getElementById("inputValue1").value;
                      var numericValue = parseInt(inputValue);
                      if (isNaN(numericValue)) {
                          alertText.textContent = "Please enter a number.";
                          customAlert.style.opacity = "1"; 
                          customAlert.style.visibility = "visible";
                          setTimeout(hideAlert, 1000);
                          return;
                      } else if (numericValue < 0 || numericValue >180){
                        alertText.textContent = "Please enter a number between 0°and 180°.";
                        customAlert.style.opacity = "1"; 
                        customAlert.style.visibility = "visible";
                        setTimeout(hideAlert, 1000);
                        return;
                      }
                      numericValue = Math.max(0, Math.min(numericValue, 180)); 
                      updateSlider1(numericValue);
                      sendSliderValue1();
                      setTimeout(function() {
                          fetch(document.location.origin+'/control?var=car&val=3');
                      }, 100);
                  
              }

              function updateSlider2(value) {
                  var slider = document.getElementById("slider2");
                  slider.value = value;
                  updateValue2(value);
              }
              function checkEnter2(event) {
                  
                      var inputValue = document.getElementById("inputValue2").value;
                      var numericValue = parseInt(inputValue);
                      if (isNaN(numericValue)) {
                          alertText.textContent = "Please enter a number.";
                          customAlert.style.opacity = "1"; 
                          customAlert.style.visibility = "visible";
                          setTimeout(hideAlert, 1000);
                          return;
                      } else if (numericValue < 0 || numericValue >180){
                        alertText.textContent = "Please enter a number between 0°and 180°.";
                        customAlert.style.opacity = "1"; 
                        customAlert.style.visibility = "visible";
                        setTimeout(hideAlert, 1000);
                        return;
                      }
                      numericValue = Math.max(0, Math.min(numericValue, 180)); 
                      updateSlider2(numericValue);
                      sendSliderValue2();
                      setTimeout(function() {
                          fetch(document.location.origin+'/control?var=car&val=3');
                      }, 100);
                  
              }

              function updateSlider3(value) {
                  var slider = document.getElementById("slider3");
                  slider.value = value;
                  updateValue3(value);
              }
              function checkEnter3(event) {
                  
                      var inputValue = document.getElementById("inputValue3").value;
                      var numericValue = parseInt(inputValue);
                      if (isNaN(numericValue)) {
                          alertText.textContent = "Please enter a number.";
                          customAlert.style.opacity = "1"; 
                          customAlert.style.visibility = "visible";
                          setTimeout(hideAlert, 1000);
                          return;
                      } else if (numericValue < 0 || numericValue >180){
                        alertText.textContent = "Please enter a number between 0°and 180°.";
                        customAlert.style.opacity = "1"; 
                        customAlert.style.visibility = "visible";
                        setTimeout(hideAlert, 1000);
                        return;
                      }
                      numericValue = Math.max(0, Math.min(numericValue, 180)); 
                      updateSlider3(numericValue);
                      sendSliderValue3();
                      setTimeout(function() {
                          fetch(document.location.origin+'/control?var=car&val=3');
                      }, 100);
              }

              function updateSlider4(value) {
                  var slider = document.getElementById("slider4");
                  slider.value = value;
                  updateValue4(value);
              }
              function checkEnter4(event) {
                  
                      var inputValue = document.getElementById("inputValue4").value;
                      var numericValue = parseInt(inputValue);
                      if (isNaN(numericValue)) {
                          alertText.textContent = "Please enter a number.";
                          customAlert.style.opacity = "1"; 
                          customAlert.style.visibility = "visible";
                          setTimeout(hideAlert, 1000);
                          return;
                      } else if (numericValue < 90 || numericValue >180){
                        alertText.textContent = "Please enter a number between 90°and 180°.";
                        customAlert.style.opacity = "1"; 
                        customAlert.style.visibility = "visible";
                        setTimeout(hideAlert, 1000);
                        return;
                      }
                      numericValue = Math.max(90, Math.min(numericValue, 180)); 
                      updateSlider4(numericValue);
                      sendSliderValue4();
                      setTimeout(function() {
                          fetch(document.location.origin+'/control?var=car&val=3');
                      }, 100);
                  
              }

              function updateSlider5(value) {
                  var slider = document.getElementById("slider5");
                  slider.value = value;
                  updateValue5(value);
              }
              function checkEnter5(event) {
                  
                      var inputValue = document.getElementById("inputValue5").value;
                      var numericValue = parseInt(inputValue);
                      if (isNaN(numericValue)) {
                          alertText.textContent = "Please enter a number.";
                          customAlert.style.opacity = "1"; 
                          customAlert.style.visibility = "visible";
                          setTimeout(hideAlert, 1000);
                          return;
                      } else if (numericValue < 0 || numericValue >180){
                        alertText.textContent = "Please enter a number between 0°and 180°.";
                        customAlert.style.opacity = "1"; 
                        customAlert.style.visibility = "visible";
                        setTimeout(hideAlert, 1000);
                        return;
                      }
                      numericValue = Math.max(0, Math.min(numericValue, 180)); 
                      updateSlider5(numericValue);
                      sendSliderValue5();
                      setTimeout(function() {
                          fetch(document.location.origin+'/control?var=car&val=3');
                      }, 100);
                  
              }

            var button = document.getElementById("Start_End");
            var buttonText = ["End", "Start"];
            var currentTextIndex = 0;
            button.addEventListener("click", function() {
              button.textContent = buttonText[currentTextIndex];
              if (button.textContent === "Start") {
                var startV = document.location.origin + "/control?var=car&val=33";
                fetch(startV);
                alertText.textContent = "End record";
              } else {
                var EndV = document.location.origin + "/control?var=car&val=32";
                fetch(EndV);
                alertText.textContent = "Start recording";

              }
              customAlert.style.opacity = "1"; 
              customAlert.style.visibility = "visible";
              currentTextIndex = (currentTextIndex + 1) % buttonText.length;
              setTimeout(hideAlert, 1500);
            });

            function sendSliderValue1() {
              var sliderValue1 = document.getElementById("slider1").value;
              var url = document.location.origin + "/control?var=car&val=21&s1=" + sliderValue1;
              fetch(url);
            }

            function sendSliderValue11() {
              var sliderValue1 = document.getElementById("slider1").value;
              var url = document.location.origin + "/control?var=car&val=25&s1=" + sliderValue1;
              fetch(url);
              
            }

            function sendSliderValue2() {
              var sliderValue2 = document.getElementById("slider2").value;
              var url = document.location.origin + "/control?var=car&val=22&s2=" + sliderValue2;
              fetch(url);
            }

            function sendSliderValue22() {
              var sliderValue2 = document.getElementById("slider2").value;
              var url = document.location.origin + "/control?var=car&val=26&s2=" + sliderValue2;
              fetch(url);
              
            }

            function sendSliderValue3() {
              var sliderValue3 = document.getElementById("slider3").value;
              var url = document.location.origin + "/control?var=car&val=23&s3=" + sliderValue3;
              fetch(url);
            }

            function sendSliderValue33() {
              var sliderValue3 = document.getElementById("slider3").value;
              var url = document.location.origin + "/control?var=car&val=27&s3=" + sliderValue3;
              fetch(url);
              
            }

            function sendSliderValue4() {
              var sliderValue4 = document.getElementById("slider4").value;
              var url = document.location.origin + "/control?var=car&val=24&s4=" + sliderValue4;
              fetch(url);
            }

            function sendSliderValue44() {
              var sliderValue4 = document.getElementById("slider4").value;
              var url = document.location.origin + "/control?var=car&val=28&s4=" + sliderValue4;
              fetch(url);
              
            }

            function sendSliderValue5() {
              var sliderValue5 = document.getElementById("slider5").value;
              var url = document.location.origin + "/control?var=car&val=29&s5=" + sliderValue5;
              fetch(url);
            }

            function sendSliderValue55() {
              var sliderValue5 = document.getElementById("slider5").value;
              var url = document.location.origin + "/control?var=car&val=30&s5=" + sliderValue5;
              fetch(url);
              
            }

              window.onload = function(){
                  var canvas = document.getElementById("canvas");
                  var ctx = canvas.getContext("2d");

                  ctx.fillStyle = "rgb(255,0,0)";
                  ctx.fillRect(73,25,60,35);
                  ctx.clearRect(78,30,50,25);

                  ctx.fillRect(93,20,20,5);
                  ctx.fillRect(68,35,5,15);
                  ctx.fillRect(133,35,5,15);

                  ctx.beginPath();
                  ctx.arc(92,42,6,0,2*Math.PI,true);
                  ctx.fill();

                  ctx.beginPath();
                  ctx.arc(117,42,6,0,2*Math.PI,true);
                  ctx.fill();

                  ctx.beginPath();
                  ctx.arc(104,100,35,0,Math.PI,true);
                  ctx.fill();

                  ctx.clearRect(50,85,100,20);

              }
          
              document.addEventListener(
              'DOMContentLoaded',function(){
                  function b(B){let C;switch(B.type){case'checkbox':C=B.checked?1:0;break;case'range':case'select-one':C=B.value;break;case'button':case'submit':C='1';break;default:return;}const D=`${c}/control?var=${B.id}&val=${C}`;fetch(D).then(E=>{console.log(`query_params to ${D} finished, status: ${E.status}`)})}var c=document.location.origin;const e=B=>{B.classList.add('hidden')},f=B=>{B.classList.remove('hidden')},g=B=>{B.classList.add('disabled'),B.disabled=!0},h=B=>{B.classList.remove('disabled'),B.disabled=!1},i=(B,C,D)=>{D=!(null!=D)||D;let E;'checkbox'===B.type?(E=B.checked,C=!!C,B.checked=C):(E=B.value,B.value=C),D&&E!==C?b(B):!D&&('aec'===B.id?C?e(v):f(v):'agc'===B.id?C?(f(t),e(s)):(e(t),f(s)):'awb_gain'===B.id?C?f(x):e(x):'face_recognize'===B.id&&(C?h(n):g(n)))};document.querySelectorAll('.close').forEach(B=>{B.onclick=()=>{e(B.parentNode)}}),fetch(`${c}/status`).then(function(B){return B.json()}).then(function(B){document.querySelectorAll('.default-action').forEach(C=>{i(C,B[C.id],!1)})});const j=document.getElementById('stream'),k=document.getElementById('stream-container'),l=document.getElementById('get-still'),m=document.getElementById('toggle-stream'),n=document.getElementById('face_enroll'),o=document.getElementById('close-stream'),p=()=>{window.stop(),m.innerHTML='Start Stream'},q=()=>{j.src=`${c+':81'}/stream`,f(k),m.innerHTML='Stop Stream'};l.onclick=()=>{p(),j.src=`${c}/capture?_cb=${Date.now()}`,f(k)},o.onclick=()=>{p(),e(k)},m.onclick=()=>{const B='Stop Stream'===m.innerHTML;B?p():q()},n.onclick=()=>{b(n)},document.querySelectorAll('.default-action').forEach(B=>{B.onchange=()=>b(B)});const r=document.getElementById('agc'),s=document.getElementById('agc_gain-group'),t=document.getElementById('gainceiling-group');r.onchange=()=>{b(r),r.checked?(f(t),e(s)):(e(t),f(s))};const u=document.getElementById('aec'),v=document.getElementById('aec_value-group');u.onchange=()=>{b(u),u.checked?e(v):f(v)};const w=document.getElementById('awb_gain'),x=document.getElementById('wb_mode-group');w.onchange=()=>{b(w),w.checked?f(x):e(x)};const y=document.getElementById('face_detect'),z=document.getElementById('face_recognize'),A=document.getElementById('framesize');A.onchange=()=>{b(A),5<A.value&&(i(y,!1),i(z,!1))},y.onchange=()=>{return 5<A.value?(alert('Please select CIF or lower resolution before enabling this feature!'),void i(y,!1)):void(b(y),!y.checked&&(g(n),i(z,!1)))},z.onchange=()=>{return 5<A.value?(alert('Please select CIF or lower resolution before enabling this feature!'),void i(z,!1)):void(b(z),z.checked?(h(n),i(y,!0)):g(n))}});
          
          </script>
      </body>
</html>
'''
         
        else:
            response = 'HTTP/1.1 404 Not Found\n\nPage not found'

        connection.sendall(response.encode('utf-8'))
    
    except OSError as e:
        # 捕获连接重置错误，避免程序崩溃
        print(f"Connection error: {e}")
    
    finally:
        connection.close()
        

def handle_control(query_params):
    global PTP_X,PTP_Y,PTP_Z,chassis_angle,shoulder_angle,elbow_angle,claws_angle,wrist_angle,val,record
     # Update angles based on query parameters
    val = int(query_params.get('val',val))
#     print(val)
    
    chassis_angle = int(query_params.get('s1', chassis_angle))
    shoulder_angle = int(query_params.get('s2', shoulder_angle))
    elbow_angle = int(query_params.get('s3', elbow_angle))
    claws_angle = int(query_params.get('s4', claws_angle))
    wrist_angle = int(query_params.get('s5', wrist_angle))
#     print('chassis_angle: {chassis}, shoulder_angle: {shoulder}, elbow_angle: {elbow}, wrist_angle: {wrist}, claws_angle: {claws}'.format(
#         chassis=chassis_angle, shoulder=shoulder_angle, elbow=elbow_angle, wrist=wrist_angle, claws=claws_angle))

    PTP_X = int(query_params.get('ss1', PTP_X))
    PTP_Y = int(query_params.get('ss2', PTP_Y))
    PTP_Z = int(query_params.get('ss3', PTP_Z))
#     print('PTP_X: {}, PTP_Y: {}, PTP_Z: {}'.format(PTP_X, PTP_Y, PTP_Z))
    
    if val == 63:
        car.move(car.Forward, 255)
    elif val == 65:
        car.move(car.Backward, 255)
    elif val == 61:
        car.move(car.Move_Left, 255)
    elif val == 62:
        car.move(car.Move_Right, 255)
    elif val == 64:
        car.move(car.Contrarotate, 255)
    elif val == 66:
        car.move(car.Clockwise, 255)
    elif val == 60:
        car.move(car.Stop, 0)
        
    elif val == 21:
        chassis_cmd(chassis_angle)
        val = 3
    elif val == 22:
        shoulder_cmd(shoulder_angle)
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
        
    elif val == 32:    #start
        record = True
    elif val == 33:     #end
        record = False
    elif val == 34 and record==False:   #run
        executeStates()
    elif val == 35 and record==False:    #reset
        clearSavedStates()
        
    

    elif val == 41:
        libs.ACB_CAR_ARM.mode = 1
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

    elif val == 54:
        PtpCmd(PTP_X,PTP_Y,PTP_Z)
    
    elif val == 67 or val == 68 or val ==69:
        _thread.start_new_thread(start_mode, ())


def start_mode():
    while True:
        if val == 67:
            model1_func()
        elif val == 68:
            model3_func()
        elif val == 69:
            model2_func()

# 启动服务器
def start_server():
    server_socket = None
    port = 80  # port
    max_retries = 5  # reconnect count
    retries = 0
    delay = 2  # retry delay

    while retries < max_retries:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建 socket
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 设置端口重用
            server_socket.bind(('0.0.0.0', port))  # Bind to port
            server_socket.listen(5)  # listen port
            print(f"Server is listening on port {port}")
            break 
        except OSError as e:
            if e.errno == 98:  # EADDRINUSE
                print(f"Port {port} is already in use. Retrying in {delay} seconds...")
                retries += 1
                time.sleep(delay)  # retry
            else:
                print(f"Error: {e}")
                break  # error
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    else:
        print("Failed to bind to port after several attempts.")
        return None

    while True:
        try:
            conn, addr = server_socket.accept()  # Accept client connection 
            handle_client(conn)  
        except Exception as e:
            print(f"Error while handling connection: {e}")
            break

    if server_socket:
        server_socket.close()  # close socket
            
if __name__ == '__main__':
    setup()
    connect()  # connect wifi
    start_server()  # start HTTP server






