"""
MOTOR SERIES CLASS 
    This class implements the interface to work with a series of Motor objects and perform all the native functionalities in a 
    coordinated manner
"""

from Classes.module_files.zaber_motor import Motor
from Classes.module_files.zaber_syringe import Syringe
from Classes.module_files.moves import Move
from Classes.module_files.labware_syringe_only import Labware
from Classes.module_files.models_manager import ModelsManager

import os
import threading
import inspect
import json
import logging
import time

from numpy import pi

from zaber_motion import Library, LogOutputMode
from zaber_motion.ascii import Connection



STEP_SPEED = 1
STEP_SIZE = 0.1
UNKNOWN_VALUE = "UNKNOWN"
MIN_STEP_SIZE = 0.1

LINUX_OS = 'posix'
WINDOWS_OS = 'nt'

class ZaberIndependentSyringe:

    # The constructor receives a string that specifies the COM port as: "COMX"
    def __init__(self, myModules, motor_configs, log_file_name_head, logging_level=logging.ERROR):
        operating_system = ""
        os_recognized = os.name

        if os_recognized == WINDOWS_OS:
            operating_system = "w"
            print("Windows Operating System Detected")
        elif os_recognized == LINUX_OS:
            operating_system = "r"

        self.system_gear = 1
        
        self.myModules = myModules
        self.myLabware = Labware(0,motor_configs["syringes"]["s"][2],None)
        self.myModelsManager = ModelsManager(operating_system)

        # ----------------------------------- Zaber Factory Logs
        file_name_tail = "_zaber_log.log"
        log_file_path = log_file_name_head + file_name_tail
        Library.set_log_output(LogOutputMode.FILE, log_file_path)
        # -----------------------------------

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging_level)
        formatter  = logging.Formatter('%(asctime)s - %(levelname)s  - %(message)s')

        file_handler = logging.FileHandler(f'{log_file_name_head}_{__name__}_log.log', mode="w")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

        
        self.stage_configs = motor_configs
        self.com_port = self.stage_configs["port"]

        # Define data members
        self.syringeList = []
        self.syringesDefinitions = {}
        self.indexID = {} # This dictionary maps the device number to its system-defined ID number
        self.masterScript = [] # This is a list of lists of Move objects
        self.script_type = ""

        # Open serial communication through the COM port
        Library.enable_device_db_store() 

        self.connection_error = False
        self.sing_abs_move_attempt_after_reconnection = 0 #counter for moving syringe
        self.abs_move_attempt_after_reconnection = 0 # Counter for absolute movement attempts after a failed one
        self.rel_move_attempt_after_reconnection = 0 # Counter for relative movement attempts after a failed one
        
        # Initialize motors
        self.logger.debug("Initializing motors at ZaberMotorSeries __init__ method")
        print("Init Motors")
        self.initialize_motors(False)

        self.s_step_size = MIN_STEP_SIZE
        self.s_step_speed = STEP_SPEED

        # Home all the motors
        # print("Home Motors")
        
        # for i in range(len(self.syringeList)):
        #     self.home_syringe(i)

    def initialize_motors(self, reinitialize):
        print("initializing motors")       
        self.stage_type = "Zaber_Syringe_Only"

        if self.com_port not in self.myModules.used_stages.keys() or reinitialize: #if you lost connection you need to redo this
            try:
                self.connection = Connection.open_serial_port(self.com_port)
            except Exception as ex:
                exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to open the COM port\n"
                self.logger.error(exception_message)
            else:
                self.logger.info("{} port succesfully opened".format(self.com_port))
                self.device_list = self.connection.detect_devices()
                self.logger.info("{} device(s) found in port {}. \nInitializing each motor...".format(len(self.device_list), self.com_port))

                # Load default configurations
                syringe_configs = self.stage_configs["syringes"]
                
                # make list of motor indeces, since this com port isn't used yet
                self.myModules.used_stages[self.com_port] = self.connection
                # Convert to index as key, so we can iterate through the motors found
                self.motorConfig_by_index = {}
                self.syringeConfig_by_index = {syringe_configs["s"][1]: [syringe_configs["s"][0], "s",syringe_configs["s"][2]]}

                # Iterate through the list of devices and initialize each of them
                i = 0
                syringe_index = 0
                for index in range(len(self.device_list)):
                    if str(index) in self.syringeConfig_by_index:
                        device = self.device_list[(index)] # extract the device from the list of devices in the COM port
                        max_speed = self.syringeConfig_by_index[str(index)][0]
                        tray_length = self.syringeConfig_by_index[str(index)][2]
                        try:
                            newMotor = Syringe(device, max_speed, tray_length, "Syringe") # Create a new Motor instance
                        except Exception as ex:
                            exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to create a new instance of Syringe\n"
                            if type(ex).__name__  == "RequestTimeoutException":
                                exception_message += f"The request timeout is set to {self.connection.default_request_timeout} ms\n"
                            self.logger.error(f"Syringe #{index} wasn't able to be added to the list")
                            self.logger.error(exception_message)
                        else:
                            self.syringeList.append(newMotor) # Add the motor to the syringeList data member
                            self.indexID["{}".format(index)] = device.identity.device_id # Associate the factory ID of each motor to the number of each motor through a dictionary
                            self.logger.info("Syringe #{} added to the list".format(index))
                            syringe_axis = self.syringeConfig_by_index[str(index)][1]
                            self.syringesDefinitions[f"{syringe_axis}"] = syringe_index
                            syringe_index = syringe_index + 1
                    else:
                        print(f"WARNING: motor {index} not configured!")
                    i = i + 1
                self.logger.info("{} motor(s) initialized".format(len(self.device_list)))
        else:
            self.connection = self.myModules.used_stages[self.com_port]
            self.device_list = self.connection.detect_devices()
            self.logger.info("{} device(s) found in port {}. \nInitializing each motor...".format(len(self.device_list), self.com_port))

            # Load default configurations
            syringe_configs = self.stage_configs["syringes"]
            
            # Convert to index as key, so we can iterate through the motors found
            self.syringeConfig_by_index = {syringe_configs["s"][1]: [syringe_configs["s"][0], "s",syringe_configs["s"][2]]}

            # Iterate through the list of devices and initialize each of them
            i = 0
            syringe_index = 0
            for index in range(len(self.device_list)):
            
                if str(index) in self.syringeConfig_by_index:
                    device = self.device_list[(index)] # extract the device from the list of devices in the COM port
                    max_speed = self.syringeConfig_by_index[str(index)][0]
                    tray_length = self.syringeConfig_by_index[str(index)][2]
                    try:
                        newMotor = Syringe(device, max_speed, tray_length, "Syringe") # Create a new Motor instance
                    except Exception as ex:
                        exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to create a new instance of Syringe\n"
                        if type(ex).__name__  == "RequestTimeoutException":
                            exception_message += f"The request timeout is set to {self.connection.default_request_timeout} ms\n"
                        self.logger.error(f"Syringe #{index} wasn't able to be added to the list")
                        self.logger.error(exception_message)
                    else:
                        self.syringeList.append(newMotor) # Add the motor to the syringeList data member
                        self.indexID["{}".format(index)] = device.identity.device_id # Associate the factory ID of each motor to the number of each motor through a dictionary
                        self.logger.info("Syringe #{} added to the list".format(index))
                        syringe_axis = self.syringeConfig_by_index[str(index)][1]
                        self.syringesDefinitions[f"{syringe_axis}"] = syringe_index
                        syringe_index = syringe_index + 1
                else:
                    print(f"WARNING: motor {index} not configured!")
                i = i + 1
            self.logger.info("{} motor(s) initialized".format(len(self.device_list)))
            #just add them as devices
    
    # Close the COM port connection and reset the class values that hold information on active motors
    def close_motors_connection(self):
        try:
            self.connection.close()
            self.indexID = {}
        except:
            print("Not Connected yet, disconnecting anyway")
        else:
            self.indexID = {}
    '''def define_axes(self):
        for motor in range(len(self.syringeList)):
            motor_axis = self.motor_configs[str(motor)][1]
            self.axesDefinitions[f"{motor_axis}"] = motor
            # print(f"Motor #{motor} driving axis {motor_axis}")
    def define_syringes(self):
        for syringe in range(len(self.syringeList)):
            syringe_axis = self.syringe_configs[str(syringe + len(self.syringeList))][1]
            self.syringesDefinitions[f"{syringe_axis}"] = syringe 
    # This returns a map of string values representing each axis to a given index number corresponding to the index of the motor in the self.syringeList
    '''

    # This returns the index of the motor in self.syringeList that controls the syringe axis
    def get_first_syringe_motor_index(self, name):
        return self.syringesDefinitions[name]

    # This returns a list with all the methods in the class
    def get_methods(self):
        return [inspect.getmembers(ZaberIndependentSyringe, predicate=inspect.isfunction)[i][0] for i in range(len(inspect.getmembers(ZaberIndependentSyringe, predicate=inspect.isfunction)))]

    # Get the IDs of each motor contained in the series as a dictionary
    def get_motor_list(self):
        return self.indexID

    # This is to read the position of all the motors. Useful when creating a script
    
    def get_motor_positions_syringe(self, name):
        #gives a list of postions of syringes
        
        '''print(name) #Troubleshooting
        print(self.syringeList)
        print(self.syringesDefinitions)
        print(self.axesDefinitions)'''

        return self.syringeList[self.syringesDefinitions[name]].get_position()

    # This returns the cordinates of the system, meaning it excludes the syringe position
        # and returns the positions of all the other motors in the right order (x, y, z)

    def get_syringe_gearbox(self, syringe):
        return self.syringeList[syringe].get_gearbox()

    def home_syringe(self, motor_index):
        self.syringeList[motor_index].home()

    def home_all(self):
        for i in range(len(self.syringeList)):
             self.home_syringe(i)

    # This creates a thread for each motor and in separate threads homes all the motors simultaneously
    # This performs a move provided a Move object, which specifies device, relative displacement, and speed
    
    def single_absolute_move_syringe(self, move, first_call):
        # Reset flag for failed connection
        self.connection_error = False

        if (first_call == True):
            self.sing_abs_move_attempt_after_reconnection = 0

        device, position, speed = move.get_move() # Extract each element of the move
        self.logger.debug(f"Attempting to perform an absolute move. {move.to_string()}")
        try:
            self.syringeList[device].set_default_speed(speed) # Set the speed acording to move
            self.syringeList[device].move_to(position) # Perform a relative move

        except Exception as ex:
            exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to perform an absolute_move\n\
                                device #{device}, target_position: {position}, target_speed: {speed} [mm/s]"
           
            self.logger.error(exception_message)

            exception_additional_info = ""

            if type(ex).__name__  != "ConnectionClosedException":
                # Raise connection_error_flag
                self.connection_error = True

                device_position = UNKNOWN_VALUE
                com_port_connections  = UNKNOWN_VALUE
                try:
                    device_position = self.syringeList[device].get_position()
                except:
                    self.logger.debug("Unable to retrieve device position")
                try:
                    com_port_connections = self.connection.detect_devices()
                except:
                    self.logger.debug("Unable to retrieve connections in the COM port")

                self.logger.debug(f"Connection_error flag set to True due to an exception of the type: {type(ex).__name__}")
                exception_additional_info += f"Device #{device}. Position: {device_position}\n\
                                        Current connections on the com port: {com_port_connections}\n"

            if type(ex).__name__  == "RequestTimeoutException":
                self.logger.info("A RequestTimeoutException occurred. Closing COM port connection...")
                self.close_motors_connection()
                self.logger.info("Will attempt to reestablish connection in 5 seconds...")
                time.sleep(5)
                self.logger.info("Reinitializing COM port and reestablishing motor connections...")
                self.initialize_motors(True)

                self.abs_move_attempt_after_reconnection += 1
                if (self.abs_move_attempt_after_reconnection >= 4):
                    self.logger.error(f"Unsuccesfully attempted the move 3 times and failed. Aborting command: {move.to_string()}")
                    self.abs_move_attempt_after_reconnection = 0
                    return 
                self.single_absolute_move_syringe(move, False) # Here I call it with the first_call flag as False so that the counter for attempted moves doesn't get reset, but keeps adding 
                
            self.logger.debug(exception_additional_info)

        else:
            self.logger.debug(f"absolute_move performed. {move.to_string()}")


    # This receives a list of moves to be performed simultaneously, opens threads for each 
    # of them and executes each move on its corresponding motor in a separate thread
    
    def step(self, device=0, size=MIN_STEP_SIZE, speed = STEP_SPEED, first_call = True):
        
        if (first_call == True):
            self.rel_move_attempt_after_reconnection = 0

        try:
            # Execute the step
            self.syringeList[device].set_default_speed(speed)
            self.syringeList[device].move_step(size)
        except Exception as ex:
            exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to perform a step\n\
                                Attempted step: device #{device}, step_size: {size} [mm], target_speed: {speed} [mm/s]"
        
            self.logger.error(exception_message)

            exception_additional_info = ""

            if type(ex).__name__  != "ConnectionClosedException":

                device_position = UNKNOWN_VALUE
                com_port_connections = UNKNOWN_VALUE
                try:
                    device_position = self.syringeList[device].get_position()
                except:
                    self.logger.debug("Unable to retrieve device position")
                try:
                    com_port_connections = self.connection.detect_devices()
                except:
                    self.logger.debug("Unable to retrieve connections in the COM port")

                exception_additional_info += f"Device #{device}. Position: {device_position}\n\
                                        Current connections on the com port: {com_port_connections}\n"

            if type(ex).__name__  == "RequestTimeoutException":

                request_timeout_setting = UNKNOWN_VALUE
                try:
                    request_timeout_setting = self.connection.default_request_timeout
                except:
                    self.logger.debug("Unable to retrieve device timeout setting")
                    
                exception_additional_info += f"\t\tThe request timeout is set to {request_timeout_setting} ms\n"

            self.logger.debug(exception_additional_info)
            if (self.rel_move_attempt_after_reconnection >= 4):
                self.logger.error(f"Unsuccesfully attempted the step 3 times and failed. Aborting command: device #{device}, step_size: {size} [mm], target_speed: {speed} [mm/s]")
                self.rel_move_attempt_after_reconnection = 0 # Reset value for future failures
                return

            # Since command failed, wait 5 seconds, restart motor connection, and re-attempt the step
            self.logger.info("An error occurred while attempting to perform the step. Closing COM port connection...")
            self.close_motors_connection()
            self.logger.info("Will attempt to reestablish connection in 5 seconds...")
            time.sleep(5)
            self.logger.info("Reinitializing COM port and reestablishing motor connections...")
            self.initialize_motors(True)

            self.rel_move_attempt_after_reconnection += 1

            self.logger.info("Re-attempting the step...")
            self.step(device, size, speed, False) #  Recursive call to re-attempt the step
            
        else:
            self.logger.debug(f"step performed. Device: {device}, Size: {size}, Speed: {speed}")
    

    # def stepSyringe(self, device, size, speed = STEP_SPEED, first_call = True):
        
    #     if (first_call == True):
    #         self.rel_move_attempt_after_reconnection = 0

    #     try:
    #         # Execute the step
    #         self.syringeList[device].set_default_speed(speed)
    #         self.syringeList[device].move_step(size)
    #     except Exception as ex:
    #         exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to perform a step\n\
    #                             Attempted step: device #{device}, step_size: {size} [mm], target_speed: {speed} [mm/s]"
        
    #         self.logger.error(exception_message)

    #         exception_additional_info = ""

    #         if type(ex).__name__  != "ConnectionClosedException":

    #             device_position = UNKNOWN_VALUE
    #             com_port_connections = UNKNOWN_VALUE
    #             try:
    #                 device_position = self.syringeList[device].get_position()
    #             except:
    #                 self.logger.debug("Unable to retrieve device position")
    #             try:
    #                 com_port_connections = self.connection.detect_devices()
    #             except:
    #                 self.logger.debug("Unable to retrieve connections in the COM port")

    #             exception_additional_info += f"Device #{device}. Position: {device_position}\n\
    #                                     Current connections on the com port: {com_port_connections}\n"

    #         if type(ex).__name__  == "RequestTimeoutException":

    #             request_timeout_setting = UNKNOWN_VALUE
    #             try:
    #                 request_timeout_setting = self.connection.default_request_timeout
    #             except:
    #                 self.logger.debug("Unable to retrieve device timeout setting")
                    
    #             exception_additional_info += f"\t\tThe request timeout is set to {request_timeout_setting} ms\n"

    #         self.logger.debug(exception_additional_info)
    #         if (self.rel_move_attempt_after_reconnection >= 4):
    #             self.logger.error(f"Unsuccesfully attempted the step 3 times and failed. Aborting command: device #{device}, step_size: {size} [mm], target_speed: {speed} [mm/s]")
    #             self.rel_move_attempt_after_reconnection = 0 # Reset value for future failures
    #             return

    #         # Since command failed, wait 5 seconds, restart motor connection, and re-attempt the step
    #         self.logger.info("An error occurred while attempting to perform the step. Closing COM port connection...")
    #         self.close_motors_connection()
    #         self.logger.info("Will attempt to reestablish connection in 5 seconds...")
    #         time.sleep(5)
    #         self.logger.info("Reinitializing COM port and reestablishing motor connections...")
    #         self.initialize_motors(True)

    #         self.rel_move_attempt_after_reconnection += 1

    #         self.logger.info("Re-attempting the step...")
    #         self.stepSyringe(device, size, speed, False) #  Recursive call to re-attempt the step
            
    #     else:
    #         self.logger.debug(f"step performed. Device: {device}, Size: {size}, Speed: {speed}")


    def shift_gear_up(self, motor, *args):
        return self.syringeList[motor].shift_gear_up()

    def shift_gear_down(self, motor, *args):
        return self.syringeList[motor].shift_gear_down()
    # dummy_argument is a placeholder,  when we call a method from motor series it could be called by a button which by itself doesn't always
        # provide an argument (like letter buttons) but sometimes it does (like bumpers) so to generalize the method call a dummy argument is added
    def step_size_up(self, *args, **kwargs):
        # print(f"System gear: {self.system_gear}")
        success = False
        for motor in range(len(self.syringeList)):

            success = self.shift_gear_up(motor)
            # print(f"Motor {i} in gear {self.syringeList[i].get_gear()}")
        if success:
            self.system_gear = self.system_gear + 1
            
    # dummy_argument is a placeholder,  when we call a method from motor series it could be called by a button which by itself doesn't always
        # provide an argument (like letter buttons) but sometimes it does (like bumpers) so to generalize the method call a dummy argument is added
    def step_size_down(self, *args, **kwargs):
        # print(f"System gear: {self.system_gear}")
        success = False
        for i in range(len(self.syringeList)):
            success = self.shift_gear_down(i)
            # print(f"Motor {i} in gear {self.syringeList[i].get_gear()}")
        if success:
            self.system_gear = self.system_gear - 1


    # This method sets a value for the step size used in the step_x_motor method
    # This method sets a value for the step size used in the step_syringe_motor method
    def set_step_size_syringe_motor(self, new_step_size):
        self.s_step_size = new_step_size

    # This method returns the step size used in the step_syringe_motor method
    def get_step_size_syringe_motor(self):
        return self.s_step_size

    # This method sets a value for the step speed used in the step_syringe_motor method
    def set_step_speed_syringe_motor(self, new_step_speed):
        self.s_step_speed = new_step_speed

    def get_step_speed_syringe_motor(self):
        return self.s_step_speed
    
    def mm_to_vol(self, mm_distance):
        syr_model = self.myLabware.syringe_model
        path_to_model = "models/syringes/"+syr_model+".json"
        with open(path_to_model, 'r') as myfile: # open file
            data = myfile.read()
        obj = json.loads(data)
        syr_radius = obj["inner_diameter"]/2
        syr_cross_section = syr_radius**2*pi
        volume = mm_distance*syr_cross_section # 1 mm^3 per uL
        return volume

    def uL_to_mm(self, volume):
        syr_model = self.myLabware.syringe_model
        path_to_model = "models/syringes/"+syr_model+".json"
        with open(path_to_model, 'r') as myfile: # open file
            data = myfile.read()
        obj = json.loads(data)
        syr_radius = obj["inner_diameter"]/2
        syr_cross_section = syr_radius**2*pi
        mm_distance = volume/syr_cross_section # 1 mm^3 per uL
        return mm_distance

    def step_syringe_motor_up(self, *args, **kwargs):
        if "volume" in kwargs:
            vol_size = float(kwargs["volume"]) / 1000
            step_size = self.uL_to_mm(vol_size)
        else:
            step_size = self.s_step_size
        if "speed" in kwargs:
            vol_speed = float(kwargs["speed"]) / 1000 # nL to uL
            step_speed = self.uL_to_mm(vol_speed) / 60 # per min to per s
        else:
            step_speed = self.s_step_speed
        direction = -1
        motor = self.syringesDefinitions["s"]
        self.step(motor, direction * step_size, step_speed)

    def step_syringe_motor_down(self, *args, **kwargs):
        if "volume" in kwargs:
            vol_size = float(kwargs["volume"]) / 1000
            step_size = self.uL_to_mm(vol_size)
        else:
            step_size = self.s_step_size
        if "speed" in kwargs:
            vol_speed = float(kwargs["speed"]) / 1000 # nL to uL
            step_speed = self.uL_to_mm(vol_speed) / 60 # per min to per s
        else:
            step_speed = self.s_step_speed
        direction = 1
        motor = self.syringesDefinitions["s"]
        self.step(motor, direction * step_size, step_speed)

    # This calls the step method on the motor that controls the syringe axis
    def step_syringe_motor(self, name, size="DEFAULT", speed="DEFAULT"):
        motor = self.syringesDefinitions[name]
        if (size == "DEFAULT"):
            size = self.s_step_size
        if (speed == "DEFAULT"):
            speed = self.s_step_speed
        self.step(motor, size, speed)

    # This calls the step method on the motor that controls the syringe axis - direction is either 1 or -1
    def joystick_step_syringe_motor(self, name, direction=1):
        motor = self.syringesDefinitions[name]
        self.step(motor, direction * self.s_step_size, self.s_step_speed)

    # def set_syringe_motor_gearbox(self, gearbox, name):
    #     motor = self.syringesDefinitions[name]
    #     self.set_motor_gearbox(motor, gearbox)

    def stop_motor(self, device):
        self.syringeList[device].stop()

    def get_syringe_location(self):
        #gives a list of postions of syringes
        
        '''print(name) #Troubleshooting
        print(self.syringeList)
        print(self.syringesDefinitions)
        print(self.axesDefinitions)'''

        return self.syringeList[self.syringesDefinitions["s"]].get_position()

    def monitor_motor_speed_from_joystick(self, joystick, input_type, input_index, motor, direction):
        '''
        This function calls move_speed with arguments determined by joystick inputs
        It monitors the corresponding joystick input values for speed control.
        The speed modifier is 1 if buttons or d-pad are used for control,
        but can be any value between 1-0 for thumbsticks/triggers.
        The stop_motor function is called when the controlling input values return to their initial (rest) state. 
        '''
        keep_moving = True
        previous_modifier = 0
        while keep_moving:
            time.sleep(0.1)

            if input_type == "button":
                modifier = joystick.buttons[input_index]
            elif input_type == "hat":
                if joystick.hats[input_index] == (0,0):
                    modifier = 0
                else:
                    modifier = 1
            elif input_type == "axis":
                modifier = joystick.axes[input_index]

            if modifier == 0 or joystick.stop_joystick:

                keep_moving = False
                self.stop_motor(motor)
            elif  modifier != previous_modifier:
                self.move_speed(motor, abs(modifier) * direction)
                previous_modifier = modifier
            else:
                pass #do nothing it is already moving at this speed

    def move_syringe_to(self, location, vol_speed):#nL/min
        s = self.syringesDefinitions["s"]
        uL_speed = vol_speed / 1000
        mmspeed = self.uL_to_mm(uL_speed)/60
        syringe_movement = Move(f"{s} {location} {mmspeed}")
        self.single_absolute_move_syringe(syringe_movement, True)

    def move_syringe_motor_up(self, joystick, input_type, input_index):
        direction = -1
        motor = self.syringesDefinitions["s"]
        t = threading.Thread(target=self.monitor_motor_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start()

    def move_syringe_motor_down(self, joystick, input_type, input_index):
        direction = 1
        motor = self.syringesDefinitions["s"]
        t = threading.Thread(target=self.monitor_motor_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start() 


    
    # dummy_argument is a placeholder,  when we call a method from motor series it could be called by a button which by itself doesn't always
        # provide an argument (like letter buttons) but sometimes it does (like bumpers) so to generalize the method call a dummy argument is added
    def shift_all_gears_up(self):
        # print(f"System gear: {self.system_gear}")
        success = False
        for i in range(len(self.syringeList)):
            success = self.shift_gear_up(i)
            # print(f"Motor {i} in gear {self.syringeList[i].get_gear()}")
        if success:
            self.system_gear = self.system_gear + 1
            
    # dummy_argument is a placeholder,  when we call a method from motor series it could be called by a button which by itself doesn't always
        # provide an argument (like letter buttons) but sometimes it does (like bumpers) so to generalize the method call a dummy argument is added
    def shift_all_gears_down(self):
        # print(f"System gear: {self.system_gear}")
        success = False
        for i in range(len(self.syringeList)):
            success = self.shift_gear_down(i)
            # print(f"Motor {i} in gear {self.syringeList[i].get_gear()}")
        if success:
            self.system_gear = self.system_gear - 1

        def get_syringe_location(self):
            #gives a list of postions of syringes
            
            '''print(name) #Troubleshooting
            print(self.syringeList)
            print(self.syringesDefinitions)
            print(self.axesDefinitions)'''

            return self.syringeList[self.syringesDefinitions["s"]].get_position()

    # This performs an infinite displacement on the given motor provided a trigger measurement (default to 1)
    # This calls the move_speed method on the motor that controls the syringe axis
    def move_speed(self, motor, modifier):
        self.syringeList[motor].move_speed(modifier)

    def unassigned(self, *args, **kwargs):
        pass

    # This stops the specified motor (only needed after calling move_speed)
    