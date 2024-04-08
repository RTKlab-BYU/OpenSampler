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

        if self.find_port(portNamePattern) is None:
            self.ser = None
            print("No GPIO board")
        else:
            self.ser = Serial(port=self.find_port(portNamePattern), baudrate=115200,
                                    bytesize=8, timeout=1, stopbits=STOPBITS_ONE)
            # print(self.ser)

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
                time.sleep(0.1)
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
        self.ser.write(str("turn_on "+this_pin).encode())
        self.outputs.append(this_pin)

    def activatePin (self, this_pin):
        for each_pin in self.outputs:
            if each_pin == this_pin:
                self.ser.write(str("turn_on "+this_pin).encode())
                return "Success"

            else:
                pass
                # print(each_pin.pin_number)
        return "ERROR: no pin named " + this_pin

    def deactivatePin (self, this_pin):
        for each_pin in self.outputs:
            if each_pin == this_pin:
                self.ser.write(str("turn_off "+this_pin).encode())
                return "Success"
            else:
                pass
                # print(each_pin.pin_number)
        return "ERROR: no pin named " + this_pin

    def killPins(self):
        self.outputs = []
        self.inputs = []
                
                
if __name__ == "__main__":
    myPort = SerialPort()    
    print("**")
    myPort.addOutputPin("D17") 
    print("^^")
    print(myPort.activatePin("D17"))
    time.sleep(1)
    print(myPort.deactivatePin("D17") )
    time.sleep(10)  
    myPort.addOutputPin("D23")    
    time.sleep(1)
    myPort.deactivatePin("D23")
    time.sleep(1)
    myPort.activatePin("D23")
    time.sleep(20)
    myPort.t.ser.close()

