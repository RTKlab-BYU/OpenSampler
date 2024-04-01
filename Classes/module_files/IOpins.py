'''The used ports are:
    A2-7 for outputs on valves and D2-7 for inputs
    D8 for MS contact closure
    
'''

import multiprocessing
import time
from threading import Thread

from serial import Serial, STOPBITS_ONE
from serial.tools import list_ports


class SerialPort:

    command_in = multiprocessing.Queue()
    result_out = multiprocessing.Queue()

    def  __init__(self, portNamePattern, command_in = command_in, result_out = result_out):
        self.command_in = command_in
        self.result_out = result_out
        self.t = self.PinManager(portNamePattern, self.command_in, self.result_out)
        self.t.start()
        self.inputs = []
        self.outputs = []
        
    class PinManager(Thread):
        """handle the GPIO process, command comes from command_in and process
        sequence

        Args:
            command_in ([type]): [description]
            result_out ([type]): [description]

        """
        command_in = multiprocessing.Queue()
        result_out = multiprocessing.Queue()

        def __init__(self, portNamePattern, command_in = command_in, result_out = result_out):
            super().__init__()
            self.disconnected = False
            self.command_pip = command_in
            self.result = result_out
            self.system_on = True
            self.restart = False
            self.error = False

            if self.find_port(portNamePattern) is None:
                self.ser = None
                print("No GPIO board")
            else:
                self.ser = Serial(port=self.find_port(portNamePattern), baudrate=115200,
                                        bytesize=8, timeout=1, stopbits=STOPBITS_ONE)
                # print(self.ser)

        def run(self):
            """Overloaded Thread.run, runs the update method every 1 seconds.
            """
            while not self.disconnected:
                self.restart = False
                self.update()
                self.error = False


        def disconnect(self):
            """End this timer thread"""
            self.disconnected = True
            time.sleep(1.5)
            print("disconnected")

        def update(self):
            """main loop for step through tasks
            """
            self.Send_out_finish(self.command_pip.get()
                                )  # this will wait until command


        def update(self):
            """main loop for step through tasks
            """
            self.Send_out_finish(self.command_pip.get()
                                )  # this will wait until command


        def Send_out_finish(self, commandToSend):
            
            self.ser.flushInput()
            self.ser.flushOutput()

            self.ser.write(str(commandToSend).encode())
            #print("read output")
            time.sleep(0.1)
            readout = self.ser.readline().decode('ascii',errors="replace")
            self.result.put(readout)


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

    class InputPin:
        def __init__(self, command_in, result_out, pin_manager, pin_number): #com name is "COM3" pin number is 3 char long either A## or D##
            super().__init__()
            self.is_pressed = False
            self.myManager = pin_manager
            self.pin_number = pin_number
            self.running = True
            #self.serialPort = serial.Serial(bytesize=8, timeout = max_wait_time, stopbits = serial.STOPBITS_ONE)
            #self.serialPort.baudrate = 115200
            #self.serialPort.port = com_name
            #if(not self.serialPort.is_open):
            #   print("(")
            #  self.serialPort.open()
            self.initializePin(command_in)

        def initializePin(self, command_in):
            self.send_command(command_in, "config_input " + str(self.pin_number))
            print("initializing pin number " + str(self.pin_number) + " as input")
            #self.get_state(command_in, result_out)
            time.sleep(1)
           # print(self.is_pressed)

        
        def get_state(self, command_in, result_out):
            self.send_command(command_in, "input " + str(self.pin_number))
            input_string = ""
            while input_string == "" and self.running:
                input_string = result_out.get()
           # print(input_string)
            input_string = input_string.lstrip("pin"+self.pin_number + " ")
            input_string = input_string.rstrip("\r\n")
            input_string = input_string.rstrip("\n")
            if "on" in input_string:
                self.is_pressed = True
            elif "off" in input_string:
                self.is_pressed = False
            else:
                print(f"Error, bad serial string: {input_string}") #testing

        def send_command(self, command_in, this_string):
            this_command = this_string + "\r\n"
          #  print(this_command)
            command_in.put(this_command)

    def addInputPin (self, pin_number, command_in = command_in, result_out = result_out):
        new_pin = self.InputPin(command_in, result_out, self.t, pin_number)
        self.inputs.append(new_pin)
    
    def getPinState(self, this_pin, command_in = command_in, result_out = result_out):
        for each_pin in self.inputs:
            if each_pin.pin_number == this_pin:
                each_pin.get_state(command_in, result_out)
                #each_pin.get_state(command_in, result_out)
                return each_pin.is_pressed
            else:
                pass
                # print(each_pin.pin_number)
        return "ERROR"
    
    class OutputPin:
        def __init__(self, command_in, pin_manager, this_pin): #com name is "COM3" pin number is 3 char long either A## or D##
            super().__init__()
            self.is_pressed = False
            self.myManager = pin_manager
            self.pin_number = this_pin
            self.running = True
            self.initializePin(command_in)

        def initializePin(self, command_in):
            self.send_command(command_in, "config_output " + str(self.pin_number))
            print("initializing pin number " + str(self.pin_number) + " as output")
            time.sleep(1)
            # self.turnOff(command_in)
           # print(self.is_pressed)
        
        def turnOn(self, command_in):
            self.send_command(command_in, "turn_on " + str(self.pin_number))
            #print("turn_on " + str(self.pin_number))
            self.is_pressed = True

        def turnOff(self, command_in):
            self.send_command(command_in, "turn_off " + str(self.pin_number))
            self.is_pressed = False

        def send_command(self, command_in, this_string):
            this_command = this_string + "\r\n"
          #  print(this_command)
            command_in.put(this_command)

    def addOutputPin (self, this_pin, command_in = command_in, result_out = result_out):
        new_pin = self.OutputPin(command_in, self.t, this_pin)
        new_pin.turnOn(command_in)
        self.outputs.append(new_pin)

    def activatePin (self, this_pin, command_in = command_in):
        for each_pin in self.outputs:
            if each_pin.pin_number == this_pin:
                each_pin.turnOn(command_in)
                return "Success"

            else:
                pass
                # print(each_pin.pin_number)
        return "ERROR: no pin named " + this_pin

    def deactivatePin (self, this_pin, command_in = command_in):
        for each_pin in self.outputs:
            if each_pin.pin_number == this_pin:
                each_pin.turnOff(command_in)
                return "Success"
            else:
                pass
                # print(each_pin.pin_number)
        return "ERROR: no pin named " + this_pin

    def killPins(self):
        for each_pin in self.outputs:
            each_pin.running = False
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

