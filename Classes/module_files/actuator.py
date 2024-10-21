"""
Jacob Davis. Nov 5 2020
actuator.py
OVERVIEW: This file activates and deactivates specific GPIO pins on the RPi
which are connected to the control pins on the VICI actuator model EUD-A. Other
models should work with this code. This class is controlself.modules.myPort.OutputPin by a controller class
which calls the toggle function. 
CONTROL PINS: there are 6 pins as shown below
|-----------|  
|  1  2  3  |
|  4  5  6  |
|-----------|
Position A is controlself.modules.myPort.OutputPin by pin 4
Pin 1 goes high (3.3V) when the actuator reaches position A
Position B is controlself.modules.myPort.OutputPin by pin 6
Pin 3 goes high (3.3V) when the actuator reaches position B
Pin 2 is used to make the controls. When pins 2 and 4 are shorted together
the actuator moves to position A. It moves to position B when pins 2 and 6
are shorted together. They are shorted by the RPi by connecting pin 2 to a
GPIO pin and then setting its voltage to 0V (pins 4 and 6 are set to 3.3V.
Then when the RPi turns one of them off (0V), it is like they are shorted
together. The signal can be turned back to 3.3V and the actuator will
remain in its position until the next control.
Pin 5 is unused
CONNECTING TO THE RPi: you will probably need a schematic of RPi4 pin nums.
Pin 1 ---> GPIO 20
Pin 2 ---> GPIO 26
Pin 3 ---> GPIO 19
Pin 4 ---> GPIO 16
Pin 5 ---> Unused/Ground
Pin 6 ---> GPIO 21
*Note that these are the 6 pins (including ground) closed to ethernet port
*There should be a cable that I made for this to work, but if not, you can
make another with this
CONTROL INTERFACE:
When starting the program, the actuator remain in its current position
calling actuator.toggle() will switch the valve from its current position and return new position index.
calling actuator.getPosition() return current position

"""


#---------------------------------imports-----------------------------------
from Classes.module_files.IOpins import SerialPort

import time

#--------------------------------constants---------------------------------
SIGNAL_HOLD = 1.5 #control signals must last at least 20ms
                 #anything less than 70 and you start to pick up errors with mechanical change
                 #becuase it will think it is in position A and B at the same time. This delay gives it time to change.

#--------------------------------variables----------------------------------
#positionIndex = 0 #0 is A, 1 is B

#------------------------------set up GPIO Pins-----ACTUATOR 1-----------------------
#use self.modules.myPort.OutputPin for GPIO output
#you can wr 
#this one needs to be grounded always

#-------------------------------------END VARIABLES-------------------------------


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
        self.modules.myPorts[self.port].deactivatePin(self.to_A_out) #16 is connected to the first actuator
        time.sleep(SIGNAL_HOLD)
        self.modules.myPorts[self.port].activatePin(self.to_A_out) #16 is connected to the first actuator
        time.sleep(SIGNAL_HOLD)

    #---------------------------------Move to position B----------------------- 
    def to_position_B(self):
        self.modules.myPorts[self.port].deactivatePin(self.to_B_out) #21 is connected to the first actuator
        time.sleep(SIGNAL_HOLD)
        self.modules.myPorts[self.port].activatePin(self.to_B_out) #21 is connected to the first actuator
        
    

