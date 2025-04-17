from libs.ACB_CAR_ARM import *  # Import all functions from the ACB_CAR_ARM library for controlling the robotic arm

# Define the GPIO pin numbers connected to different parts of the robotic arm
chassis_pin = 25    # Chassis control pin
shoulder_pin = 26      # Elbow control pin
elbow_pin = 27   # Shoulder control pin
wrist_pin = 33      # Claws control pin
claws_pin = 4       # Wrist control pin

# Initialize the robotic arm with the specified pins
ARM_init(chassis_pin, shoulder_pin, elbow_pin, wrist_pin, claws_pin)

# Infinite loop to continuously accept user input for joint angles
while True:
    # Prompt the user to enter angles for the chassis, elbow, shoulder, wrist, and claws
    user_input = input('''Enter chassis_angle(0-180°)\n shoulder_angle(0-180°)\n elbow_angle(0-180°)\n wrist_angle(0-180°)\n claws_angle(90-180°): ''')
    
    # Split the input string by spaces and store the individual angle values in a list
    angle = user_input.split()
    
    # Check if the user has entered exactly 5 angle values
    if len(angle) == 5:
        # Convert the string input to integer values for each joint angle
        chassis_angle, shoulder_angle,elbow_angle, wrist_angle, claws_angle = map(int, angle)

        # Check if any of the angle values exceed 180 degrees (invalid input)
        if claws_angle > 180 or elbow_angle > 180 or shoulder_angle > 180 or wrist_angle > 180 or chassis_angle > 180:
            print("Error: One or more angles exceed degrees. Please try again.")  # Print error message
            continue  # Skip the rest of the loop and ask the user to enter the angles again
        
        # Check if any angle value is less than 0 or the claws angle is below 90 degrees (invalid input)
        if claws_angle < 90 or elbow_angle < 0 or shoulder_angle < 0 or wrist_angle < 0 or chassis_angle < 0:
            print("Error: One or more angles exceed degrees. Please try again.")  # Print error message
            continue  # Skip the rest of the loop and ask the user to enter the angles again
        else:
            # If the input angles are valid, print the values for each joint
            print("chassis_angle =", chassis_angle)
            print("shoulder_angle =", shoulder_angle)
            print("elbow_angle =", elbow_angle)
            print("wrist_angle =", wrist_angle)
            print("claws_angle =", claws_angle)

            # Send the valid angles to the corresponding control functions for each part of the robotic arm
            chassis_cmd(chassis_angle)  # Command to control the chassis
            shoulder_cmd(elbow_angle)   # Command to control the shoulder (it seems reversed, may need fixing)
            elbow_cmd(shoulder_angle)   # Command to control the elbow (it seems reversed, may need fixing)
            wrist_cmd(wrist_angle)      # Command to control the wrist
            claws_cmd(claws_angle)      # Command to control the claws
            
    else:
        # If the user doesn't input exactly 5 angles, show an error message
        print("Error: Please enter exactly five angles.")

