"""
Wiring setup for actuator
|--------------|  
|  1B  2W  3O  |
|  4G  5x  6S  |
|--------------|
where B is blue, W is white with blue stripe, O is orange
G is green, x is empty, S is white with orange stripe 1-6 are pin numbers on actuator
"""

from Classes.module_files.IOpins import SerialPort

import time



class Coordinator(): #test class
    def __init__(self):
        self.myPorts = SerialPort() 

class SelectorActuator:
    def __init__(self, myModules, port, homeout, moveout, maxPosition):
        self.port = port
        self.myModules = myModules
        self.move_out_pin = moveout
        self.home_out_pin = homeout
        self.myModules.myPorts[self.port].addOutputPin(self.home_out_pin)
        self.myModules.myPorts[self.port].addOutputPin(self.move_out_pin)
        self.home_actuator()
        self.max_position = maxPosition

    # original methods

    def home_actuator(self):
        print(f"Homing. Setting pin {self.home_out_pin} to ground.")
        self.myModules.myPorts[self.port].deactivatePin(self.home_out_pin) 
        self.myModules.myPorts[self.port].activatePin(self.home_out_pin) 
        
        self.current_position = 1

    def step_actuator(self):
        print(f"Setting pin {self.move_out_pin} to ground.")

        #NO TEST FOR ACTUALLY MOVING
        self.myModules.myPorts[self.port].deactivatePin(self.move_out_pin)
        self.myModules.myPorts[self.port].activatePin(self.move_out_pin)
        self.current_position = self.current_position + 1

    # new methods
    
    # def home_actuator(self):
    #     self.myModules.myPorts[self.port].deactivatePin(self.home_out_pin) # sets home pin to low/ground
    #     print(f"Setting pin {self.home_out_pin} to ground.")
    #     time.sleep(SIGNAL_HOLD)
    #     self.myModules.myPorts[self.port].activatePin(self.home_out_pin) # sets home pin to high
    #     self.current_position = 1

    # def step_actuator(self):
    #     self.myModules.myPorts[self.port].deactivatePin(self.move_out_pin) # sets move pin to low/ground
    #     print(f"Setting pin {self.move_out_pin} to ground.")
    #     time.sleep(SIGNAL_HOLD)
    #     self.myModules.myPorts[self.port].activatePin(self.move_out_pin) # sets move pin to high
    #     self.current_position += 1

    def move_to_position(self, targetPosition):
        if (targetPosition > self.max_position):
            print("Error you went to far")
            return
        
        if (self.current_position > targetPosition):
            self.home_actuator()
        
        while (self.current_position < targetPosition):
            self.step_actuator()
        
