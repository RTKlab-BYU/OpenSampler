"""
Wiring setup for actuator
|--------------|  
|  1B  2W  3O  |
|  4G  5x  6S  |
|--------------|
where B is blue, W is white with blue stripe, O is orange
G is green, x is empty, S is white with orange stripe 1-6 are pin numbers on actuator
Wiring setup for actuator
||---------------||  
|  17G  27O  22S  |
|-----------------| 
|------------|  
|  14B  15W  |
||----------||
where B is blue, W is white with blue stripe, O is orange
4 is green, 6 is white with orange stripe, and numbers are GPIO numbers not pin numbers
"""

from Classes.module_files.IOpins import SerialPort

import time

class Coordinator(): #test class
    def __init__(self):
        self.myPorts = SerialPort() 

class SelectorActuator:
    def __init__(self, myModules, port, moveout, homeout, maxPosition):
        self.port = port
        self.myModules = myModules
        self.move_out_pin = moveout
        self.home_out_pin = homeout
        self.myModules.myPorts[self.port].addOutputPin(self.move_out_pin)
        self.myModules.myPorts[self.port].addOutputPin(self.home_out_pin)
        #use self.myModules.myPort.InputPins for GPIO inputs
        #you can read from self.myModules.myPort.InputPins. 3.3V is on, 0V is off.
        
       # self.to_runPosition()
        #time.sleep(2)
        #self.to_loadPosition()
        #time.sleep(2)
        #self.to_runPosition()
        #
        # time.sleep(2)
          #-------------------------------------get Position-------------------------
        self.home_actuator()
        self.max_position = maxPosition
    
    def home_actuator(self):
        self.myModules.myPorts[self.port].activatePin(self.home_out_pin) 
        time.sleep(0.1)
        self.myModules.myPorts[self.port].deactivatePin(self.home_out_pin) 
        time.sleep(0.1)
        self.current_position = 1

    def step_actuator(self):
        #NO TEST FOR ACTUALLY MOVING
        self.myModules.myPorts[self.port].activatePin(self.move_out_pin) 
        time.sleep(0.1)
        self.myModules.myPorts[self.port].deactivatePin(self.move_out_pin) 
        time.sleep(0.1)
        self.current_position = self.current_position + 1
        
    

    def move_to_position(self, targetPosition):
        if (targetPosition > self.max_position):
            print("Error you went to far")
            return
        
        if (self.current_position > targetPosition):
            self.home_actuator()
            self.home_actuator()

        
        while (self.current_position < targetPosition):
            self.step_actuator()
        
        print("Multiposition Actuator in postion " + str(self.current_position))

    def test_multiposition_actuator(self): # test function to see if the code works the way I think it should	
        #self.calibrate(1)	
        inputVal = 1 	
        while(inputVal != 0):
            print("type '0' to quit")	
            self.move_to_position(inputVal)
            inputVal = int(input())

##Test code
if __name__ == "__main__":
    x = Coordinator()
    myTipValve = SelectorActuator(x, 8)
    myTipValve.test_multiposition_actuator()
