"""
MOTOR SERIES CLASS 
    This class implements the interface to work with a series of Motor objects and perform all the native functionalities in a 
    coordinated manner
"""

from Classes.module_files.zaber_motor import Motor
from Classes.module_files.zaber_syringe import Syringe
from Classes.module_files.moves import Move
from Classes.module_files.labware import Labware
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
MIN_STEP_SIZE = 0.1
MAX_STEP_SIZE = 2.5
STEP_INCREMENT = 5
UNKNOWN_VALUE = "UNKNOWN"

AXIS_NAMES = ["x","y","z"]
SYRINGE_NAME = "s"

LINUX_OS = 'posix'
WINDOWS_OS = 'nt'

class ZaberMotorSeries:

    # The constructor receives a string that specifies the COM port as: "COMX"
    def __init__(self, myModules, motor_configs: dict, log_file_name_head: str, logging_level=logging.ERROR):

        operating_system = ""
        os_recognized = os.name

        self.myModules = myModules

        if os_recognized == WINDOWS_OS:
            operating_system = "w"
            print("Windows Operating System Detected")
        elif os_recognized == LINUX_OS:
            operating_system = "r"
        
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
        self.motorList = [Motor] # This contains the Motor objects of the series
        self.syringeList = [Syringe]
        self.axesDefinitions = {}
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

        # Home all the motors
        # print("Home Motors")
        # for i in range(len(self.motorList)):
        #     self.home_motor(i)

        # for i in range(len(self.syringeList)):
        #     self.home_syringe(i)

        self.system_gear = 1

        self.x_step_size = MIN_STEP_SIZE
        self.x_step_speed = STEP_SPEED

        self.y_step_size = MIN_STEP_SIZE
        self.y_step_speed = STEP_SPEED

        self.z_step_size = MIN_STEP_SIZE
        self.z_step_speed = STEP_SPEED

        self.s_step_size = MIN_STEP_SIZE
        self.s_step_speed = STEP_SPEED

    def initialize_motors(self, reinitialize):
        print("initializing motors")
        self.motorList = []
        self.syringeList = []
        self.stage_type = "Zaber_XYZ"
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
                motor_configs = self.stage_configs["motors"]# This will load a list of lists
                syringe_configs = self.stage_configs["syringes"]
                
                # make list of motor indeces, since this com port isn't used yet
                self.myModules.used_stages[self.com_port] = self.connection
                # Convert to index as key, so we can iterate through the motors found
                self.motorConfig_by_index = {}
                for motor_name in AXIS_NAMES:
                    self.motorConfig_by_index[motor_configs[motor_name][1]] = [motor_configs[motor_name][0],motor_name,motor_configs[motor_name][2]]
                self.syringeConfig_by_index = {syringe_configs["s"][1]: [syringe_configs["s"][0], "s",syringe_configs["s"][2]]}

                # Iterate through the list of devices and initialize each of them
                i = 0
                syringe_index = 0
                motor_index = 0
                for index in range(len(self.device_list)):
                    if str(index) in self.motorConfig_by_index:
                        
                        device = self.device_list[(index)] # extract the device from the list of devices in the COM port
                        max_speed = self.motorConfig_by_index[str(index)][0]
                        tray_length = self.motorConfig_by_index[str(index)][2]
                        try:
                            newMotor = Motor(device, max_speed, tray_length, "Axis") # Create a new Motor instance
                        except Exception as ex:
                            exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to create a new instance of Motor\n"
                            if type(ex).__name__  == "RequestTimeoutException":
                                exception_message += f"The request timeout is set to {self.connection.default_request_timeout} ms\n"
                                self.logger.error(f"Motor #{index} wasn't able to be added to the list")
                        else:
                            self.motorList.append(newMotor) # Add the motor to the motorList data member
                            self.indexID["{}".format(index)] = device.identity.device_id # Associate the factory ID of each motor to the number of each motor through a dictionary
                            self.logger.info("Motor #{} added to the list".format(index))
                            motor_axis = self.motorConfig_by_index[str(index)][1]
                            print(motor_axis)
                            self.axesDefinitions[f"{motor_axis}"] = motor_index
                            motor_index = motor_index + 1
                    elif str(index) in self.syringeConfig_by_index:
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
                            self.syringeList.append(newMotor) # Add the motor to the motorList data member
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
            motor_configs = self.stage_configs["motors"]# This will load a list of lists
            syringe_configs = self.stage_configs["syringes"]
            
            # Convert to index as key, so we can iterate through the motors found
            self.motorConfig_by_index = {}
            for motor_name in AXIS_NAMES:
                self.motorConfig_by_index[motor_configs[motor_name][1]] = [motor_configs[motor_name][0],motor_name,motor_configs[motor_name][2]]
            self.syringeConfig_by_index = {syringe_configs["s"][1]: [syringe_configs["s"][0], "s",syringe_configs["s"][2]]}

            # Iterate through the list of devices and initialize each of them
            i = 0
            syringe_index = 0
            motor_index = 0
            for index in range(len(self.device_list)):
                if str(index) not in self.myModules.used_motors[self.com_port]:
                    self.myModules[self.com_port].append(str(index))
                    reused = False 
                else:
                    print(f"using {index} again")
                    reused = True


                if str(index) in self.motorConfig_by_index:
                    device = self.device_list[(index)] # extract the device from the list of devices in the COM port
                    max_speed = self.motorConfig_by_index[str(index)][0]
                    tray_length = self.motorConfig_by_index[str(index)][2]
                    try:
                        newMotor = Motor(device, max_speed, tray_length, "Axis") # Create a new Motor instance
                    except Exception as ex:
                        exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to create a new instance of Motor\n"
                        if type(ex).__name__  == "RequestTimeoutException":
                            exception_message += f"The request timeout is set to {self.connection.default_request_timeout} ms\n"
                            self.logger.error(f"Motor #{index} wasn't able to be added to the list")
                    else:
                        self.motorList.append(newMotor) # Add the motor to the motorList data member
                        self.indexID["{}".format(index)] = device.identity.device_id # Associate the factory ID of each motor to the number of each motor through a dictionary
                        self.logger.info("Motor #{} added to the list".format(index))
                        motor_axis = self.motorConfig_by_index[str(index)][1]
                        self.axesDefinitions[f"{motor_axis}"] = motor_index
                        motor_index = motor_index + 1
                elif str(index) in self.syringeConfig_by_index:
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
                        self.syringeList.append(newMotor) # Add the motor to the motorList data member
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
            self.motorList = []
            self.indexID = {}
        except:
            print("Not Connected yet, disconnecting anyway")
        else:
            self.motorList = []
            self.indexID = {}
    '''def define_axes(self):
        for motor in range(len(self.motorList)):
            motor_axis = motor_configs[str(motor)][1]
            self.axesDefinitions[f"{motor_axis}"] = motor
            # print(f"Motor #{motor} driving axis {motor_axis}")
    def define_syringes(self):
        for syringe in range(len(self.syringeList)):
            syringe_axis = syringe_configs[str(syringe + len(self.motorList))][1]
            self.syringesDefinitions[f"{syringe_axis}"] = syringe 
    # This returns a map of string values representing each axis to a given index number corresponding to the index of the motor in the self.motorList
    '''
    def get_axes_definitions(self):
        return self.axesDefinitions

    # This returns the index of the motor in self.motorList that controls the x axis
    def get_x_motor_index(self):
        return self.axesDefinitions["x"]
    
    # This returns the index of the motor in self.motorList that controls the y axis
    def get_y_motor_index(self):
        return self.axesDefinitions["y"]

    # This returns the index of the motor in self.motorList that controls the z axis
    def get_z_motor_index(self):
        return self.axesDefinitions["z"]

    # This returns the index of the motor in self.motorList that controls the syringe axis
    def get_first_syringe_motor_index(self, name):
        return self.syringesDefinitions[name]

    # This returns a list with all the methods in the class
    def get_methods(self):
        return [inspect.getmembers(ZaberMotorSeries, predicate=inspect.isfunction)[i][0] for i in range(len(inspect.getmembers(ZaberMotorSeries, predicate=inspect.isfunction)))]

    # This returns the amount of motors included in the motorSeries object
    def motor_count(self):
        return len(self.motorList)

    # Get the IDs of each motor contained in the series as a dictionary
    def get_motor_list(self):
        return self.indexID

    # This is to read the position of all the motors. Useful when creating a script
    def get_motor_positions(self):
        positions = []
        for motor in self.motorList:
            positions.append(motor.get_position())
        return positions
    
    def get_syringe_location(self):
        #gives a list of postions of syringes
        
        '''print(name) #Troubleshooting
        print(self.syringeList)
        print(self.syringesDefinitions)
        print(self.axesDefinitions)'''

        return self.syringeList[self.syringesDefinitions["s"]].get_position()

    # This returns the cordinates of the system, meaning it excludes the syringe position
        # and returns the positions of all the other motors in the right order (x, y, z)
    def get_motor_coordinates(self):
        try:
            x = round(self.motorList[self.axesDefinitions["x"]].get_position(), 3)
            y = round(self.motorList[self.axesDefinitions["y"]].get_position(), 3)
            z = round(self.motorList[self.axesDefinitions["z"]].get_position(), 3)
        except Exception as ex:
            self.logger.error(f"An exception of type {type(ex).__name__} occurred while attempting to read the positions of the motors")
        else:
            return (x, y, z)

    # base_speed * gearbox[max_gear] = max_speed
    # def get_motor_base_speed(self, motor=0):
    #     return self.motorList[motor].get_base_speed()

    def get_motor_max_speed(self, motor=0):
        return self.motorList[motor].get_max_speed()

    def get_motor_gear(self, motor=0):
        return self.motorList[motor].get_gear()

    def get_motor_gearbox(self, motor=0):
        return self.motorList[motor].get_gearbox()

    def get_syringe_gearbox(self, syringe=0):
        return self.syringeList[syringe].get_gearbox()

    def get_x_motor_gearbox(self):
        motor = self.axesDefinitions["x"]
        return self.get_motor_gearbox(motor)

    def get_y_motor_gearbox(self):
        motor = self.axesDefinitions["y"]
        return self.get_motor_gearbox(motor)

    def get_z_motor_gearbox(self):
        motor = self.axesDefinitions["z"]
        return self.get_motor_gearbox(motor)

    def get_syringe_motor_gearbox(self, name):
        motor = self.syringesDefinitions[name]
        return self.get_syringe_gearbox(motor)

    def reset_motor_gear(self, motor=0):
        self.motorList[motor].reset_gear()

    def get_system_gear(self):
        return self.system_gear

    def home_motor(self, motor_index=0):
        self.motorList[motor_index].home()
    
    def home_syringe(self, motor_index=0):
        self.syringeList[motor_index].home()

    # This creates a thread for each motor and in separate threads homes all the motors simultaneously
    def home_all(self):
        threadList = []
        try:
            self.motorList[self.axesDefinitions["z"]].home()
            # This creates a list of started threads (one for each move)
            for motor in range(len(self.motorList)):
                newThread = threading.Thread(target=self.motorList[motor].home)
                newThread.start()
                threadList.append(newThread)

            for thread in threadList:
                thread.join()
        except Exception as ex:
            self.logger.error(f"An exception of type {type(ex).__name__} occurred while attempting to home all the motors\n")
        else:
            self.logger.info("All motors homed")
    
    # This performs a move provided a Move object, which specifies device, relative displacement, and speed
    def relative_move(self, move: Move):
        device, step, speed = move.get_move() # Extract each element of the move
        self.motorList[device].set_default_speed(speed) # Set the speed acording to move
        self.motorList[device].move_step(step) # Perform a relative move

    def absolute_move(self, move: Move, first_call = True):
        # Reset flag for failed connection
        self.connection_error = False

        device, position, speed = move.get_move() # Extract each element of the move
        self.logger.debug(f"Attempting to perform an absolute move. {move.to_string()}")
        if (first_call == True):
            self.error_trys = 0
        try:
            self.motorList[device].set_default_speed(speed) # Set the speed acording to move
            self.motorList[device].move_to(position) # Perform a relative move
        
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
                    device_position = self.motorList[device].get_position()
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
                # Raise connection_error_flag
                self.connection_error = True

                request_timeout_setting = UNKNOWN_VALUE
                try:
                    request_timeout_setting = self.connection.default_request_timeout
                except:
                    self.logger.debug("Unable to retrieve device timeout setting")
                self.logger.debug(f"Connection_error flag set to True due to an exception of the type: {type(ex).__name__}")
                exception_additional_info += f"The request timeout is set to {request_timeout_setting} ms\n"
                print("Connection problem")
            
            elif type(ex).__name__  == "MovementFailedException":
                self.logger.info("A MovementFailedException occurred. Retrying...")
                print("trying")
                # exception_additional_info = ex.reason
                print(exception_additional_info)
                self.error_trys += 1
                if (self.error_trys >= 10):
                    self.logger.error(f"Unsuccesfully attempted the move 3 times and failed. Aborting command: {move.to_string()}")
                    self.error_trys = 0
                    return 
                self.absolute_move(move, False) # Here I call it with the first_call flag as False so that the counter for attempted moves doesn't get reset, but keeps adding 
            else:
                print(type(ex))    #zaber_motion.exceptions import MovementFailedExceptionData
            

            self.logger.debug(exception_additional_info)

        else:
            self.logger.debug(f"absolute_move performed. {move.to_string()}")

    def single_absolute_move(self, move: Move, first_call):
        # Reset flag for failed connection
        self.connection_error = False

        if (first_call == True):
            self.sing_abs_move_attempt_after_reconnection = 0
        if (first_call == True):
            self.error_trys = 0

        device, position, speed = move.get_move() # Extract each element of the move
        self.logger.debug(f"Attempting to perform an absolute move. {move.to_string()}")
        try:
            self.motorList[device].set_default_speed(speed) # Set the speed acording to move
            self.motorList[device].move_to(position) # Perform a relative move

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
                    device_position = self.motorList[device].get_position()
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
                if (self.abs_move_attempt_after_reconnection >= 10):
                    self.logger.error(f"Unsuccesfully attempted the move 3 times and failed. Aborting command: {move.to_string()}")
                    self.abs_move_attempt_after_reconnection = 0
                    return 
                self.single_absolute_move(move, False) # Here I call it with the first_call flag as False so that the counter for attempted moves doesn't get reset, but keeps adding 
                
            elif type(ex).__name__  == "MovementFailedException":
                self.logger.info("A MovementFailedException occurred. Retrying...")
                print("trying")
                # exception_additional_info = ex.reason
                print(exception_additional_info)
                self.error_trys += 1
                if (self.error_trys >= 4):
                    self.logger.error(f"Unsuccesfully attempted the move 3 times and failed. Aborting command: {move.to_string()}")
                    self.error_trys = 0
                    return 
                self.absolute_move(move, False) # Here I call it with the first_call flag as False so that the counter for attempted moves doesn't get reset, but keeps adding 
            self.logger.debug(exception_additional_info)

        else:
            self.logger.debug(f"absolute_move performed. {move.to_string()}")

    def move_to(self, location):

        x = self.get_x_motor_index()
        y = self.get_y_motor_index()
        z = self.get_z_motor_index()

        # LIFT THE SYRINGE AS A PRECAUTION

        # Create the Move oject for the Z axis
        z_move_lift = Move(f"{z} {0.0} {self.get_motor_max_speed(z)}")
        # Perform an absolute displacement to move in the Z axis
        self.single_absolute_move(z_move_lift, True)

        moves_list = []
        motor_indeces = [x, y]
        index  = 0
        # Create the Move objects for the X-Y plane (and put them on a list)
        for motor in motor_indeces:
            max_speed = self.get_motor_max_speed(motor_indeces[index])
            position = location[index]
            move_string = f"{motor_indeces[index]} {position} {max_speed}"
            newMove = Move(move_string)
            moves_list.append(newMove)
            index = index + 1

        # Create the Move oject for the Z axis
        z_move_lower = Move(f"{z} {location[2]} {self.get_motor_max_speed(z)}")

        # Perform a simultaneous absolute displacement to move in the X-Y plane
        self.simultaneous_absolute_move(moves_list)

        # Perform an absolute displacement to move in the Z axis
        self.single_absolute_move(z_move_lower, True)

    def small_move_xy(self, location, move_speed):

        x = self.get_x_motor_index()
        y = self.get_y_motor_index()

        moves_list = []
        motor_indeces = [x, y]
        index  = 0
        # Create the Move objects for the X-Y plane (and put them on a list)
        for motor in motor_indeces:
            position = location[index]
            move_string = f"{motor_indeces[index]} {position} {move_speed}"
            newMove = Move(move_string)
            moves_list.append(newMove)
            index = index + 1

        # Perform a simultaneous absolute displacement to move in the X-Y plane
        self.simultaneous_absolute_move(moves_list)

    def single_absolute_move_syringe(self, move: Move, first_call):
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
                    device_position = self.motorList[device].get_position()
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

        else:
            self.logger.debug(f"absolute_move performed. {move.to_string()}")

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

    def move_syringe_to(self, location, vol_speed):#nL/min
        s = self.syringesDefinitions["s"]
        uL_speed = vol_speed / 1000
        mmspeed = self.uL_to_mm(uL_speed)/60
        syringe_movement = Move(f"{s} {location} {mmspeed}")
        self.single_absolute_move_syringe(syringe_movement, True)

    # This receives a list of moves to be performed simultaneously, opens threads for each 
    # of them and executes each move on its corresponding motor in a separate thread
    def simultaneous_relative_move(self, movesList):
        threadList = []
        
        # This creates a list of started threads (one for each move)
        for move in range(len(movesList)):
            newThread = threading.Thread(target=self.relative_move, args=[movesList[move]])
            newThread.start()
            threadList.append(newThread)

        for thread in threadList:
            thread.join()

    def simultaneous_absolute_move(self, movesList, first_call=True):

        if (first_call == True):
            self.abs_move_attempt_after_reconnection = 0

        threadList = []
        
        # This creates a list of started threads (one for each move)
        for move in range(len(movesList)):
            newThread = threading.Thread(target=self.absolute_move, args=[movesList[move]])
            newThread.start()
            threadList.append(newThread)

        for thread in threadList:
            thread.join()

        # If the connection_error flag is set to True, restart the connection and repeat the move (try up to 3 times)
        if (self.connection_error == True):
            self.logger.info("A connection_error occurred. Closing COM port connection...")
            self.close_motors_connection()
            self.logger.info("Will attempt to reestablish connection in 5 seconds...")
            time.sleep(5)
            self.logger.info("Reinitializing COM port and reestablishing motor connections...")
            self.initialize_motors(True)

            self.abs_move_attempt_after_reconnection += 1
            if (self.abs_move_attempt_after_reconnection >= 4):
                self.logger.error(f"Unsuccesfully attempted the move 3 times and failed. Aborting command: {movesList}")
                self.abs_move_attempt_after_reconnection = 0
                return 
            self.simultaneous_absolute_move(movesList, False) # Here I call it with the first_call flag as False so that the counter for attempted moves doesn't get reset, but keeps adding 

    # This performs a step with a provided size
    def step(self, device=0, size=MIN_STEP_SIZE, speed = STEP_SPEED, first_call = True):
        
        if (first_call == True):
            self.rel_move_attempt_after_reconnection = 0

        try:
            # Execute the step
            self.motorList[device].set_default_speed(speed)
            self.motorList[device].move_step(size)
        except Exception as ex:
            exception_message = f"An exception of type {type(ex).__name__} occurred while attempting to perform a step\n\
                                Attempted step: device #{device}, step_size: {size} [mm], target_speed: {speed} [mm/s]"
        
            self.logger.error(exception_message)

            exception_additional_info = ""

            if type(ex).__name__  != "ConnectionClosedException":

                device_position = UNKNOWN_VALUE
                com_port_connections = UNKNOWN_VALUE
                try:
                    device_position = self.motorList[device].get_position()
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
    
    def step_syringe(self, device=0, size=MIN_STEP_SIZE, speed = STEP_SPEED, first_call = True):
        
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
    
    
    # def stepSyringe(self, device=0, size=MIN_STEP_SIZE, speed = STEP_SPEED, first_call = True):
        
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
    #                 device_position = self.motorList[device].get_position()
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

    # This method sets a value for the step size used in the step_x_motor method
    # def set_step_size_x_motor(self, new_step_size):
    #     self.x_step_size = new_step_size

    # This method sets a value for the step size used in the step_y_motor method
    # def set_step_size_y_motor(self, new_step_size):
    #     self.y_step_size = new_step_size

    # This method sets a value for the step size used in the step_z_motor method
    # def set_step_size_z_motor(self, new_step_size):
    #     self.z_step_size = new_step_size

    # This method sets a value for the step size used in the step_syringe_motor method
    # def set_step_size_syringe_motor(self, new_step_size):
    #     self.s_step_size = new_step_size

    # This method returns the step size used in the step_x_motor method
    # def get_step_size_x_motor(self):
    #     return self.x_step_size

    # This method returns the step size used in the step_y_motor method
    # def get_step_size_y_motor(self):
    #     return self.y_step_size

    # This method returns the step size used in the step_z_motor method
    # def get_step_size_z_motor(self):
    #     return self.z_step_size

    # This method returns the step size used in the step_syringe_motor method
    # def get_step_size_syringe_motor(self):
    #     return self.s_step_size

    # This method sets a value for the step speed used in the step_x_motor method
    # def set_step_speed_x_motor(self, new_step_speed):
    #     self.x_step_speed = new_step_speed

    # This method sets a value for the step speed used in the step_y_motor method
    # def set_step_speed_y_motor(self, new_step_speed):
    #     self.y_step_speed = new_step_speed

    # This method sets a value for the step speed used in the step_z_motor method
    # def set_step_speed_z_motor(self, new_step_speed):
    #     self.z_step_speed = new_step_speed

    # This method sets a value for the step speed used in the step_syringe_motor method
    # def set_step_speed_syringe_motor(self, new_step_speed):
    #     self.s_step_speed = new_step_speed

    # def get_step_speed_x_motor(self):
    #     return self.x_step_speed
    
    # def get_step_speed_y_motor(self):
    #     return self.y_step_speed

    # def get_step_speed_z_motor(self):
    #     return self.z_step_speed

    # def get_step_speed_syringe_motor(self):
    #     return self.s_step_speed











    # # This calls the step method on the motor that controls the x axis
    # def step_x_motor(self, size="DEFAULT", speed="DEFAULT"):
    #     motor = self.axesDefinitions["x"]
    #     if (size == "DEFAULT"):
    #         size = self.x_step_size
    #     if (speed == "DEFAULT"):
    #         speed = self.x_step_speed
    #     self.step(motor, size, speed)

    # # This calls the step method on the motor that controls the y axis
    # def step_y_motor(self, size="DEFAULT", speed="DEFAULT"):
    #     motor = self.axesDefinitions["y"]
    #     if (size == "DEFAULT"):
    #         size = self.y_step_size
    #     if (speed == "DEFAULT"):
    #         speed = self.y_step_speed
    #     self.step(motor, size, speed)

    # # This calls the step method on the motor that controls the z axis
    # def step_z_motor(self, size="DEFAULT", speed="DEFAULT"):
    #     motor = self.axesDefinitions["z"]
    #     if (size == "DEFAULT"):
    #         size = self.z_step_size
    #     if (speed == "DEFAULT"):
    #         speed = self.z_step_speed
    #     self.step(motor, size, speed)

    # # This calls the step method on the motor that controls the syringe axis
    # def step_syringe_motor(self, name, size="DEFAULT", speed="DEFAULT"):
    #     motor = self.syringesDefinitions[name]
    #     if (size == "DEFAULT"):
    #         size = self.s_step_size
    #     if (speed == "DEFAULT"):
    #         speed = self.s_step_speed
    #     self.step(motor, size, speed)










    # This calls the step method on the motor that controls the x axis - direction is either 1 or -1
    def step_x_motor_right(self, *args, **kwargs):
        direction = 1
        motor = self.axesDefinitions["x"]
        self.step(motor, direction * self.x_step_size, self.x_step_speed)

    def step_x_motor_left(self, *args, **kwargs):
        direction = -1
        motor = self.axesDefinitions["x"]
        self.step(motor, direction * self.x_step_size, self.x_step_speed)

    # This calls the step method on the motor that controls the y axis - direction is either 1 or -1
    def step_y_motor_forward(self, *args, **kwargs):
        direction = 1
        motor = self.axesDefinitions["y"]
        self.step(motor, direction * self.y_step_size, self.y_step_speed)
        
    def step_y_motor_back(self, *args, **kwargs):
        direction = -1
        motor = self.axesDefinitions["y"]
        self.step(motor, direction * self.y_step_size, self.y_step_speed)

    # This calls the step method on the motor that controls the z axis - direction is either 1 or -1
    def step_z_motor_up(self, *args, **kwargs):
        direction = 1
        motor = self.axesDefinitions["z"]
        self.step(motor, direction * self.z_step_size, self.z_step_speed)

    def step_z_motor_down(self, *args, **kwargs):
        direction = -1
        motor = self.axesDefinitions["z"]
        self.step(motor, direction * self.z_step_size, self.z_step_speed)

    # This calls the step method on the motor that controls the syringe axis - direction is either 1 or -1
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
        self.step_syringe(motor, direction * step_size, step_speed)

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
        self.step_syringe(motor, direction * step_size, step_speed)




    # def set_motor_gearbox(self, motor=0, gearbox=0):
    #     self.motorList[motor].set_gearbox(gearbox)

    # def set_x_motor_gearbox(self, gearbox):
    #     motor = self.axesDefinitions["x"]
    #     self.set_motor_gearbox(motor, gearbox)

    # def set_y_motor_gearbox(self, gearbox):
    #     motor = self.axesDefinitions["y"]
    #     self.set_motor_gearbox(motor, gearbox)

    # def set_z_motor_gearbox(self, gearbox):
    #     motor = self.axesDefinitions["z"]
    #     self.set_motor_gearbox(motor, gearbox)

    # def set_syringe_motor_gearbox(self, gearbox, name):
    #     motor = self.syringesDefinitions[name]
    #     self.set_motor_gearbox(motor, gearbox)

    def shift_gear_up(self, motor, *args, **kwargs):
        return self.motorList[motor].shift_gear_up()

    def shift_gear_down(self, motor, *args, **kwargs):
        return self.motorList[motor].shift_gear_down()

    # dummy_argument is a placeholder,  when we call a method from motor series it could be called by a button which by itself doesn't always
        # provide an argument (like letter buttons) but sometimes it does (like bumpers) so to generalize the method call a dummy argument is added
    def step_size_up(self, *args):
        # print(f"System gear: {self.system_gear}")
        success = False
        for motor in range(len(self.motorList)):

            success = self.shift_gear_up(motor)
            # print(f"Motor {i} in gear {self.motorList[i].get_gear()}")
        if success:
            self.system_gear = self.system_gear + 1
            
    # dummy_argument is a placeholder,  when we call a method from motor series it could be called by a button which by itself doesn't always
        # provide an argument (like letter buttons) but sometimes it does (like bumpers) so to generalize the method call a dummy argument is added
    def step_size_down(self, *args):
        # print(f"System gear: {self.system_gear}")
        success = False
        for i in range(len(self.motorList)):
            success = self.shift_gear_down(i)
            # print(f"Motor {i} in gear {self.motorList[i].get_gear()}")
        if success:
            self.system_gear = self.system_gear - 1

    # def step_size_up(self, *args, **kwargs):
    #     if self.x_step_size < MAX_STEP_SIZE:
    #         self.x_step_size = self.x_step_size * STEP_INCREMENT
    #     if self.y_step_size < MAX_STEP_SIZE:
    #         self.y_step_size = self.y_step_size * STEP_INCREMENT
    #     if self.z_step_size < MAX_STEP_SIZE:
    #         self.z_step_size = self.z_step_size * STEP_INCREMENT

    # def step_size_down(self, *args, **kwargs):
    #     if self.x_step_size > MIN_STEP_SIZE:
    #         self.x_step_size = self.x_step_size / STEP_INCREMENT
    #     if self.y_step_size < MIN_STEP_SIZE:
    #         self.y_step_size = self.y_step_size / STEP_INCREMENT
    #     if self.z_step_size < MIN_STEP_SIZE:
    #         self.z_step_size = self.z_step_size / STEP_INCREMENT

    # This performs an infinite displacement on the given motor provided a modifier measurement (default to 1)
    def move_speed(self, motor, modifier):
        self.motorList[motor].move_speed(modifier)

    def move_syringe_speed(self, motor, modifier):
        self.syringeList[motor].move_speed(modifier)

    # def stop_listening(self, *args):
    #     print("Doesn't stop anything, hit the button on GUI")

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

    
    def monitor_syringe_speed_from_joystick(self, joystick, input_type, input_index, motor, direction):
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
                self.stop_syringe_motor(motor)
            elif  modifier != previous_modifier:
                self.move_syringe_speed(motor, abs(modifier) * direction)
                previous_modifier = modifier
            else:
                pass #do nothing it is already moving at this speed


    def move_x_motor_right(self, joystick, input_type, input_index):
        direction = 1
        motor = self.axesDefinitions["x"]
        t = threading.Thread(target=self.monitor_motor_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start()        

    def move_x_motor_left(self, joystick, input_type, input_index):
        direction = -1
        motor = self.axesDefinitions["x"]
        t = threading.Thread(target=self.monitor_motor_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start()     
    
    # This calls the move_speed method on the motor that controls the y axis
    def move_y_motor_forward(self, joystick, input_type, input_index):
        direction = 1
        motor = self.axesDefinitions["y"]
        t = threading.Thread(target=self.monitor_motor_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start()     

    def move_y_motor_back(self, joystick, input_type, input_index):
        direction = -1
        motor = self.axesDefinitions["y"]
        t = threading.Thread(target=self.monitor_motor_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start()     

    # This calls the move_speed method on the motor that controls the z axis
    def move_z_motor_up(self, joystick, input_type, input_index):
        direction = 1
        motor = self.axesDefinitions["z"]
        t = threading.Thread(target=self.monitor_motor_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start()     

    def move_z_motor_down(self, joystick, input_type, input_index):
        direction = -1
        motor = self.axesDefinitions["z"]
        t = threading.Thread(target=self.monitor_motor_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start()     
        
    # This calls the move_speed method on the motor that controls the syringe axis
    def move_syringe_motor_up(self, joystick, input_type, input_index):
        direction = -1
        motor = self.syringesDefinitions["s"]
        t = threading.Thread(target=self.monitor_syringe_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start()

    def move_syringe_motor_down(self, joystick, input_type, input_index):
        direction = 1
        motor = self.syringesDefinitions["s"]
        t = threading.Thread(target=self.monitor_syringe_speed_from_joystick, args=(joystick, input_type, input_index, motor, direction))
        t.start() 

    # This stops the specified motor (only needed after calling move_speed)
    def stop_motor(self, device):
        self.motorList[device].stop()

    def stop_syringe_motor(self, device):
        self.syringeList[device].stop()

    # This stops all the motors (only needed after calling move_speed)
    # def stop_all(self, *args):
    #     for motor in self.motorList:
    #         motor.stop()

    # def stop_x_motor(self, *args):
    #     self.stop_motor(self.axesDefinitions["x"])

    # def stop_y_motor(self, *args):
    #     self.stop_motor(self.axesDefinitions["y"])

    # def stop_z_motor(self, *args):
    #     self.stop_motor(self.axesDefinitions["z"])

    def unassigned(self, *args, **kwargs):
        pass

    """
    SCRIPTING FUNCTIONS (AUTOMATED MOTION) ---------------------------------------------------------------------------
    """
    # This reads a file and uploads the commands to the attribute self.masterScript, which contains Move objects 
        # (sequential motion) or lists of Move objects (simultaneous motion)
    # def load_master_script(self, script_file = ""):

    #     # Get rid of previously loaded scripts
    #     self.masterScript = [] # masterScript = [ MoveObject, [MoveObject, MoveObject], MoveObject, [MoveObject, MoveObject, MoveObject] ] (meaning a list of: Move Obejects AND lists of Move Objects )

    #     # Open the file
    #     path = open(script_file, "r")
    #     masterScriptFile = json.load(path)
    #     first_line = True
    #     for line in masterScriptFile:
            
    #         # The following is to skip the first line that indicates what type of script is being read (either Absolute["r"] or Relative["r"])
    #         if (first_line):
    #             self.script_type = line.split()[0] # This extracts the character and gets rid of any white spaces, since split() returns a list we take the first element
    #             first_line = False
    #             continue

    #         commandsPerLine = len(line.split())/3 # A Move object needs 3 elements to form a unit

    #         # If there is only one command in the line
    #         if (commandsPerLine == 1):
    #             command = Move(line)
    #             self.masterScript.append(command)

    #         # If there are multiple commands in the line (simultaneous commands)
    #         else:
    #             # split the commands in the line in a list of strings (one string for each command)
    #             span = 3
    #             split = line.split() # an ordered list of all the numbers in the line
    #             stringList = [" ".join(split[i:i+span]) for i in range(0, len(split), span)] # List of strings

    #             # target list with simultaneous moves
    #             simultaneousMovesList = []

    #             for commandString in stringList:
    #                 # create a Move object
    #                 newMove = Move(commandString)
    #                 # append the Move object to a temporary list
    #                 simultaneousMovesList.append(newMove)

    #             # append the temporary list to the self.masterScript list
    #             self.masterScript.append(simultaneousMovesList)

    #     print("Master script loaded!")

    # # This iterates through the self.masterScript list and executes each element. Since this list has both 
    #     # sequential and simultaneous motion commands, it calls either the move() or the simultaneous_move()
    #     # methods of this class
    # def execute_master_script(self):
    #     # The script is meant to be understood as "r"elative steps
    #     if (self.script_type == "r"):
    #         # Iterate through each element in the masterScript list
    #         for command in self.masterScript:

    #             # If the command is a list of Move objects, call simultaneous_move() method
    #             if type(command) == list:
    #                 self.simultaneous_relative_move(command)
                
    #             # If the command is a single Move object, call the move() method
    #             else:
    #                 self.relative_move(command)

    #         print("Master Script executed succesfully")

    #     # The script is meant to be understood as "a"bsolute positions
    #     elif (self.script_type == "a"):
    #         # Iterate through each element in the masterScript list
    #         for command in self.masterScript:

    #             # If the command is a list of Move objects, call simultaneous_move() method
    #             if type(command) == list:
    #                 self.simultaneous_absolute_move(command)
                
    #             # If the command is a single Move object, call the move() method
    #             else:
    #                 self.absolute_move(command)

    #         print("Master Script executed succesfully")
        
    #     else:
    #         print("Wrong type of script type (neither \"a\"(absolute) or \"r\"(relative)")


def testing():

    mySeries = ZaberMotorSeries("COM4", "one_motor_config.json") # for Raspberry Pi: "/dev/ttyUSB0" # for Windows "COM11" (or whatever COM port it is)
    mySeries.home_all("")
    input("Press ENTER to continue...")
    myMove = Move("0 50 10")
    mySeries.absolute_move(myMove)
    input("Press ENTER to continue...")
    myMove = Move("0 150 10")
    mySeries.absolute_move(myMove)


if __name__ == "__main__":
    testing()