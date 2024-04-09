'''The used ports are:
    A2-7 for outputs on valves and D2-7 for inputs
    D8 for MS contact closure
    
'''

import time
from threading import Thread

from serial import Serial, STOPBITS_ONE
from serial.tools import list_ports


class SerialPort:

    def  __init__(self, portNamePattern):
        
        self.inputs = []
        self.outputs = []    

        self.port = self.find_port(portNamePattern)
        if  self.port is None:
            self.ser = None
            print("No GPIO board")
        else:
            self.ser = Serial(port=self.port, baudrate=115200,
                                    bytesize=8, timeout=1, stopbits=STOPBITS_ONE)
            print(self.ser)

    def find_port(self, name):
        """Find the serial port with specific name

        Args:
            name ([str]): device full descritpion, run this module to find all
            COM port descriptions.
        Returns:
            [str]: first device found with name, e.g., /dev/ttyUSB0
        """
        com_ports = list(list_ports.comports())
        for item in com_ports:
            if name is None:
                print(item.description)
            elif name in item.description:
                return item.device
        return None

    
    def addInputPin (self, this_pin):
        self.ser.write(str("config_input "+this_pin).encode())
        self.inputs.append(this_pin)

    def getPinState (self, this_pin):
        for eachPin in self.inputs:
            if eachPin == this_pin:
                self.ser.flushInput()
                self.ser.flushOutput()

                self.ser.write(str("input "+this_pin).encode())
                #print("read output")
                time.sleep(0.2)
                readout = self.ser.readline().decode('ascii',errors="replace")
                readout = readout.lstrip("pin"+this_pin+" ").rstrip("\r\n").rstrip("\n")
                if "on" in readout:  
                   return True
                elif "off" in readout:
                    return False
                else:
                    return readout 
        return "ERROR: no pin named " + this_pin

    def addOutputPin (self, this_pin):
        self.ser.write(str("config_output "+this_pin).encode())
        time.sleep(2)
        self.ser.write(str("turn_on "+this_pin).encode())
        time.sleep(1)
        self.outputs.append(this_pin)

    def activatePin (self, this_pin):
        for each_pin in self.outputs:
            if each_pin == this_pin:
                self.ser.write(str("turn_on "+this_pin).encode())
                print(self.port)
                print(self.ser)
                print(this_pin)
                return "Success"

            else:
                pass
                # print(each_pin.pin_number)
        return "ERROR: no pin named " + this_pin

    def deactivatePin (self, this_pin):
        for each_pin in self.outputs:
            if each_pin == this_pin:
                self.ser.write(str("turn_off "+this_pin).encode())
                print(self.port)
                print(self.ser)
                print(this_pin)
                return "Success"
            else:
                pass
                # print(each_pin.pin_number)
        return "ERROR: no pin named " + this_pin

    def killPins(self):
        self.outputs = []
        self.inputs = []
                
                
if __name__ == "__main__":
    comPorts = ["COM5","COM6"]   
    myPorts = []
    for port in comPorts:
        myPorts.append(SerialPort(port))
    print("**")
    myPorts[1].addOutputPin("D19")
    myPorts[0].addOutputPin("D17") 
    myPorts[1].addOutputPin("D23")
    myPorts[1].addInputPin("D27")
    print("^^")
    print(myPorts[1].activatePin("D19"))
    time.sleep(2)
    print(myPorts[1].deactivatePin("D19") )
    time.sleep(10)  
    myPorts[0].activatePin("D17")
    time.sleep(0.2)
    myPorts[0].deactivatePin("D17")
    time.sleep(5)

    time.sleep(1)
    myPorts[1].activatePin("D23")
    time.sleep(20)
    myPorts[1].deactivatePin("D23")

    
    time.sleep(1)
    print(myPorts[1].getPinState("D27"))
    time.sleep(10)
    for eachPort in myPorts:
        eachPort.ser.close()

