"""
Jacob Davis. Nov 5 2020
actuator.py

OVERVIEW: This file activates and deactivates specific GPIO pins on the GPIO device.
which are connected to the control pins on the VICI actuator model EUD-A. Other
models should work with this code. 
VICI CONTROL PINS: 
there are 6 pins as shown below
|-----------|  
|  1  2  3  |
|  4  5  6  |
|-----------|
Position A is selected by setting pin 4 equal to pin 2
Pin 1 goes high (3.3V) when the actuator reaches position A
Position B is selected by setting pin 6 equal to pin 2 
Pin 3 goes high (3.3V) when the actuator reaches position B
Pin 5 is unused

CONTROL INTERFACE:
When starting the program, the actuator remain in its current position
calling actuator.getPosition() return current position

"""


from Classes.module_files.IOpins import SerialPort

import time





class Coordinator():
    def __init__(self):
        self.myPorts = [SerialPort()]




class Actuator:
    def __init__(self, modules, port, pinAOut, pinBOut, pinCheckA, pinCheckB):
        self.port = port
        self.modules = modules
        self.to_A_out = pinAOut
        self.to_B_out = pinBOut
        self.modules.myPorts[self.port].addOutputPin(self.to_A_out)
        self.modules.myPorts[self.port].addOutputPin(self.to_B_out)
        self.check_A = pinCheckA 
        self.check_B = pinCheckB 
        self.modules.myPorts[self.port].addInputPin(self.check_A)
        self.modules.myPorts[self.port].addInputPin(self.check_B)
        
    #-------------Move to position A-------------------------
    def to_position_A(self):
        self.modules.myPorts[self.port].deactivatePin(self.to_A_out) 
        self.modules.myPorts[self.port].activatePin(self.to_A_out) 

    #---------------------------------Move to position B----------------------- 
    def to_position_B(self):
        self.modules.myPorts[self.port].deactivatePin(self.to_B_out) 
        self.modules.myPorts[self.port].activatePin(self.to_B_out) 
        
    

