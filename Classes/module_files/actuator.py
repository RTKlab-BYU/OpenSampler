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
SIGNAL_HOLD = 0.2 #control signals must last at least 20ms
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



#this class controls the actuator. When powered on it remains in its position until toggle is calself.modules.myPort.OutputPin
#toggle is the only function that should be calself.modules.myPort.OutputPin. Getposition can also be calself.modules.myPort.OutputPin.
class Actuator:
    def __init__(self, modules, port, pinAOut, pinBOut, pinCheckA, pinCheckB):
        self.port = port
        self.modules = modules
        self.to_A_out = pinAOut
        self.to_B_out = pinBOut
        self.modules.myPorts[self.port].addOutputPin(self.to_A_out)
        self.modules.myPorts[self.port].addOutputPin(self.to_B_out)
        #use self.modules.myPort.InputPins for GPIO inputs
        #you can read from self.modules.myPort.InputPins. 3.3V is on, 0V is off.
        self.check_A = pinCheckA #check position A
        self.check_B = pinCheckB #check position B
        self.modules.myPorts[self.port].addInputPin(self.check_A)
        self.modules.myPorts[self.port].addInputPin(self.check_B)
       # self.to_runPosition()
        #time.sleep(2)
        #self.to_loadPosition()
        #time.sleep(2)
        #self.to_runPosition()
        #
        # time.sleep(2)
          #-------------------------------------get Position-------------------------
        self.getPosition()
    def getPosition(self):
        positionIndex = -1
        posA = self.modules.myPorts[self.port].getPinState(self.check_A)        
        # print(posA)
        posB = self.modules.myPorts[self.port].getPinState(self.check_B)
        # print(posB)
        if posA  and  posB : #error
            print("Error: Actuator - both positions register as true. Maybe: Do not toggle quickly.")
            #sys.exit()
        elif not posA and not posB: #error
            print("Error: Actuator is not in position A or B or Powered off. Check power connection.")
            #sys.exit()
        elif posA and not posB: #good position A
            positionIndex = 0 #a
        elif not posA and posB: #good position B
            positionIndex = 1 #b
        
        
        return positionIndex
        
    #-------------Move to position A-------------------------
    def to_runPosition(self):
        #print("move A") #should be a is run
        self.modules.myPorts[self.port].activatePin(self.to_A_out) #16 is connected to the first actuator
        time.sleep(SIGNAL_HOLD)
        self.modules.myPorts[self.port].deactivatePin(self.to_A_out) #16 is connected to the first actuator
        time.sleep(SIGNAL_HOLD)
       # self.modules.myPorts[self.port].activatePin(self.to_A_out) #16 is connected to the first actuator
      #  time.sleep(SIGNAL_HOLD)
       # self.modules.myPorts[self.port].deactivatePin(self.to_A_out) #16 is connected to the first actuator
       # time.sleep(SIGNAL_HOLD)#hold for a bit to avoid error from mechanical change (if you dont wait, it will
                                #register as both position A and B simutaneously and throw error)
      #  self.modules.myPorts[self.port].activatePin(self.to_A_out) #16 is connected to the first actuator


    #---------------------------------Move to position B----------------------- 
    def to_loadPosition(self):
        #print("move B")
        self.modules.myPorts[self.port].activatePin(self.to_B_out) #21 is connected to the first actuator
        time.sleep(SIGNAL_HOLD)
        self.modules.myPorts[self.port].deactivatePin(self.to_B_out) #21 is connected to the first actuator
        time.sleep(SIGNAL_HOLD)
        #self.modules.myPorts[self.port].activatePin(self.to_B_out) #21 is connected to the first actuator
       # time.sleep(SIGNAL_HOLD)
        #self.modules.myPorts[self.port].deactivatePin(self.to_B_out) #21 is connected to the first actuator
        #time.sleep(SIGNAL_HOLD) #hold for a bit to avoid error from mechanical change (if you dont wait, it will
                                #register as both position A and B simutaneously and throw error)
     #   self.modules.myPorts[self.port].activatePin(self.to_B_out) #21 is connected to the first actuator

    #---------------------------------Toggle-----------------------------------
    #this will switch positions no matter what the current position is
    #if its in A, go to B. If its in B, go to A. 
    
    #----------------------------Test-----------------------
    

#to test this file, uncomment the following lines and run this file 
if __name__ == "__main__":
    x = Coordinator()
    y = Actuator(x, "D23", "D19", "D34", "D27") # make instance of actuator class
    time.sleep(5)
    y.to_loadPosition()
    print(y.getPosition())
    print("B")
    print(y.getPosition())
    time.sleep(10)
    y.to_runPosition()
    print("A")
    print(y.getPosition())
    time.sleep(4)
    y.to_loadPosition()
    print(y.getPosition())
    print("B")
    print(y.getPosition())
    time.sleep(10)
    y.to_runPosition()
    print("A")
    print(y.getPosition())
    time.sleep(4)