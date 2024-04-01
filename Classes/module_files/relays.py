"""
Jacob Davis. Jan 12 2021

relays.py

OVERVIEW: this files controls three relay switches that will be used for the MS and LC contact 
closure. It is set up for all three relays to work, but at the time of this file's creation we 
should only need access to two relays.

WHAT IS A RELAY: A relay is just a simple switch that that can be flipped with a signal instead
of manually. This will allow us to connect and disconect the proper wires for the contact closure
to start the LC pump and the MS. 

The board we are using is called "RPI Relay Board" and is sold by waveshare.
https://www.waveshare.com/rpi-relay-board.htm
https://www.waveshare.com/wiki/RPi_Relay_Board
search "demo code" on the wiki page to access the source code in several languages.

If you go to the wiki page (see links above) you will see that generally this board is placed
directly on top of the Rpi and attaches to all the GPIO pins. However, we need to have a cooling
fan attached to the RPI which means this will not be able to mount on top of the RPI. 

To handle this we will just be connecting the needed pins from the Rpi directly to the relay board.
You should only need access to the 5v, 3.3v, and pins 26, 20, and 21 as listed on the wiki.

PROBLEM: as stated above pins 26, 20, and 21 are the pins used to control each of the three relays.
These pins are currently being used by the actuators as they need a grid of 6 pins where at least
five of them are GPIO pins. All you need to know is that if we wanted to use these exact pins, we 
would need to make new cables for the actuators, and we do not want to do that. 

SOLUTION: The solution to this problem is rather simple. instead of manually connecting to pins
26, 20, and 21, we just connect to any other three pins and use them to control the relays. 

Below is the code and we used pins 2, 3, and 4 for this. This is just a random selection becuase
they were next to eachother and were close to a 3.3v and 5v which I think are needed to power the relays. 

Make sure you connect the wires you want to connect into the center and right channels of the relays
 _______
|_1_2_3_| each relay has 3 inputs. Connect the contact closure wires to numbers 2 and 3. 

CONTROLING THE RELAYS: See the top of the wiki page (remember that the circle with an X in it 
represents an LED). Its basically explains that a low voltage (0v from the GPIO pins) will connect 
the center to the right and turn on the LED. A high voltage will connect the center to the left 
and turn off the LEDs.

*Note that the board we have has 3 relays you can access. 

"""



##################################################

#           P26 ----> Relay_Ch1
#			P20 ----> Relay_Ch2
#			P21 ----> Relay_Ch3

# note that these are the pins we need to connect to on the relay board from the RPI.
#       P2 --> P26
#       P3 --> P20
#       P4 --> P21

# this means that pins 2,3, and 4 control relays 1,2, and 3 respectively. 

##################################################
#!/usr/bin/python
# -*- coding:utf-8 -*-

from Classes.module_files.IOpins import SerialPort

import time

# the wires connecting the RPi to the relay board are attacked to the RPis GPIO pins 2, 3, and 4
# any 3 would do, I picked these at random. 


class Coordinator():
    def __init__(self):
        self.myPorts = [SerialPort()] 

class Relays:
	def __init__(self, modules, port, pin):
		self.modules = modules
		self.modules.myPorts[port].addOutputPin(pin)
		self.port = port
		self.pin = pin
		self.relay_off()


	def relay_off(self):
		self.modules.myPorts[self.port].deactivatePin(self.pin) 

	def relay_on(self):
		self.modules.myPorts[self.port].activatePin(self.pin) 

	def test_relays(self): # test function to see if the code works the way I think it should
		inputVal = "off" 
		while(inputVal != "quit"):
			if inputVal == "off": # should disconnect wires
				self.relay_off("D17")
			elif inputVal == "on": # should connect wired
				self.relay_on("D17") 
			else:
				print("non-valid option")

			inputVal = input()


if __name__ == "__main__":
    x = Coordinator()
    y = Relays(x)
    time.sleep(5)
    y.relay_off("D07")
    print("stop")
    time.sleep(10)
    y.relay_on("D07")
    print("go")
    time.sleep(4)
    y.relay_off("D07")
    print("stop")

#to test this file, uncomment the following line and run this file 
#Relays().test_relays()

