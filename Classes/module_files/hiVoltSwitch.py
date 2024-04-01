"""
    Jacob Davis. Created: Oct 16 2020
    jacobmdavis4@gmail.com
    hiVoltSwitch.py
    OVERVIEW: This file controls the High Voltage Switch with raspberry pi GPIO
    pins 6 and 12. When 3.3V is sent to left_pin the left channel is opened. If 3.3V
    is sent to right_pin the right channel is opened. To make this work, when one
    is set to 3.3V the other is turned off (0V).
    CONTROLS:
    When starting the program, the left channel is opened.
    Left Arrow: Open Left Channel
    Right Arrow: Open Right Channel
    Space: Toggle Channels
    Escape: quit
    PSEUDO CODE:
    1.) initialize and open left channel to start
    2.) wait key strokes
    -if left arrow: go to left position
        -left_pin.on()   (3.3V)
        -right_pin.off() (0v)
    -if right arrow: go to right position
        -right_pin.on()  (3.3V)
        -left_pin.off()  (0V)
    -if spacebar: toggle
        -if  left, go to right
        -if right, go to left
    -if escape: exit
        -sys.exit()
"""

# from os import environ

# environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # this line keeps pygame from printing a message when imported 
# from pygame.locals import *

#---use led for GPIO output; can write to LED, so you can control the Actuator---#



resolution = (600,400) #defines resolution; length and width of window
'''
#init the screen
#pygame.init()
resolution = (1,1) #for some reason pygame needs a screen to get keystrokes
screen = pygame.display.set_mode(resolution)
'''
class HiVoltageSwitch:	
    def __init__(self,  manager, port, left_pin, right_pin):
        self.left_pin = left_pin  #goes to left side
        self.right_pin = right_pin #goes to right side
        self.mymanager = manager	
        self.channels = ["Left", "Right"]
        self.port = port
        self.mymanager.myPorts[self.port].addOutputPin(self.right_pin)
        self.mymanager.myPorts[self.port].addOutputPin(self.left_pin)	
        self.channelIndex = 1 #0 is left, 1 is right	
        self.calibrate(1) # initialize this to the right side based off the actuators	
    	
    def openLeftChannel(self): #move to position A
        self.mymanager.myPorts[self.port].activatePin(self.left_pin) 
        self.mymanager.myPorts[self.port].deactivatePin(self.right_pin)
        self.mymanager.myPorts[self.port].activatePin(self.left_pin) 
        self.mymanager.myPorts[self.port].deactivatePin(self.right_pin) 
        
        self.channelIndex = 0	


        return self.channelIndex           	
    
    def openRightChannel(self): #Move to position B
        self.mymanager.myPorts[self.port].activatePin(self.right_pin) 
        self.mymanager.myPorts[self.port].deactivatePin(self.left_pin)
        self.mymanager.myPorts[self.port].activatePin(self.right_pin)
        self.mymanager.myPorts[self.port].deactivatePin(self.left_pin)
        self.channelIndex = 1	
        	
        return self.channelIndex	
    		
    def toggle(self): #toggle/switches channel
        if self.channelIndex == 0:	
            self.channelIndex = self.openLeftChannel()	
        elif self.channelIndex == 1:	
            self.channelIndex = self.openRightChannel()	
            	
        return self.channelIndex	
            	
    def calibrate(self, startPosition): 	
        """This sets the channel to the desired position when you call the run function.	
           it generally is based off the actuator. See the manager class inits.	
        Args:	
            channelIndex ([int]): [0 or 1 for channel left or right]"""
        if startPosition == 1:	
            self.openLeftChannel()	
        elif startPosition == 0:	
            self.openRightChannel()	
        else:	
            print("\n****ERROR: switch not calibrated to either position left or right")	
            	
        print("\n\n SWTICH POSITION INDEX:")	
        print(self.channelIndex)	
    	
    '''def printInstructions(self):   	
        print("Instructions")	
        print("Left Arrow: Open Left Channel")	
        print("Right Arrow: Open Right Channel")	
        print("Spacebar: Toggle Channel")	
        print("Escape: quit")	
   	
    def run(self, channelIndex):	
    	
        self.calibrate(channelIndex)	
        #self.printInstructions()	
        print()	
        	
        	
        while True:	
            for event in pygame.event.get():	
                if event.type == QUIT:	
                    pygame.quit()	
                    sys.exit()	
                    	
                if event.type == pygame.KEYDOWN:	
                    if event.key == pygame.K_RIGHT and channelIndex == 0:	
                        channelIndex = self.openRightChannel(channelIndex)	
                    if event.key == pygame.K_LEFT  and channelIndex == 1:	
                        channelIndex = self.openLeftChannel(channelIndex)	
                    if event.key == pygame.K_SPACE: #toggle	
                        channelIndex = self.toggle(channelIndex)	
                    if event.key == pygame.K_ESCAPE:	
                        pygame.quit()	
                        sys.exit()	
                print(channels[channelIndex]) #print position to terminal	
    
    def test_switch(self): # test function to see if the code works the way I think it should	
        #self.calibrate(1)	
        inputVal = "on" 	
        while(inputVal != "quit"):	
            if inputVal == "off": # should disconnect wires	
                pass	
            elif inputVal == "on": # should connect wired	
                self.toggle() 	
            else:	
                print("non-valid option")	
            inputVal = input()	
            '''


#---commment this in to test this file alone---#
#mySwitch = HiVoltageSwitch(0)	
#mySwitch.test_switch()