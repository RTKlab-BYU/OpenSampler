"""
COORDINATOR CLASS 
    This is the class that serves as an interface between the server (web_app.py) and the motor system comprised of all of the other classes that 
    regulate in one way or another the operation of the Zaber motors.
    There are 6 main blocks of code that implement the basic functionalities of the motor system:

    I. Joystick Control
        This section takes care of opening a separate thread that "listens" to the inputs the user provides through the joystick, while the main thread
        executes in an infinite loop any methods associated to the inputs received on the joystick. The infinite loop running on the main thread stops 
        when the "listening" of the joystick is terminated, which can happen whenever the stop_listening() method is called within the joystick or by
        calling the stop_joystick() method from within Coordinator (found in this section).

    II. Instantaneous Commands
        This section provides the ability to move the motors to any location recognized either as a well or wellplate_well in the system. There is a common method 
        called by both procedures called go_to_position() which only receives an x, y, z coordinate as input and goes there with the motors. Therefore,
        the other methods just take care of obtaining the x,y,z coordinate for the specified well or wellplate_well and then call the go_to_position() method with
        that coordinate as the parameter.

    III. Script Methods
        This section specifies methods needed to execute a scripted set of instructions recorded on an external file.

    IV. Labware
        This section defines a variety of methods that have to do with the creation, calibration, deletion, diretories, and models available for labware. 
        It also contains a method that allows for selecting a syringe model.


"""
import threading
import math	
import logging
import os
from datetime import datetime
import time

from Classes.modules import Modules
from Classes.method_reader import MethodReader	
from Classes.module_files.moves import Move
from Classes.protocol_actions import ProtocolActions


#'''



CALIBRATION_POINTS = 3
INBETWEEN_LIFT_DISTANCE = -10 # Default distance the syringe will be lifted/lowered when going from one nanopotss well\reagent wellplate_well to another

LABWARE_CHIP = "c"
LABWARE_PLATE = "W"
LABWARE_SYRINGE = "s"

DEFAULT_CONTROLLER_PROFILE = "settings/default_controller_profile.py"

FROM_NANOLITERS = 0.001

REFRESH_COORDINATE_INTERVAL = 0.1

LINUX_OS = 'posix'
WINDOWS_OS = 'nt'



class Coordinator:
    def __init__(self):
        """ Initialize the class and instanciate all the subordinate classes

        Args:
            motors_config_file ([json file name]): specify a file with the configurations of the motors (index, axis controlled, tray length, and max speed)
            joystick_profile ([json file name]): specify a file with the mapping between joystick elements and methods triggered when those elements are pressed by user
        """
     
        # --------------------- Log files namehead
        folder = "logs/" if os.name == 'posix' else "logs\\"
        now = datetime.now()
        timestamp = now.strftime("%m-%d-%Y___%I-%M_%p")
        log_file_name_head = folder + timestamp
        # ---------------------
        self.myModules = Modules()
        self.coordinates_refresh_rate = REFRESH_COORDINATE_INTERVAL
        #----------------------
    
        self.monitoring_joystick = False
        self.updating_positions = False

        #----------------------
        #--------------------- Comment in/out quotation marks below to test GUI on own laptop --------------------
        #'''        
                
        self.myReader = MethodReader(self)
        self.actionOptions = ProtocolActions(self)
        
        #'''



        # initialize the logging info format
        self.myLogger = logging.getLogger(__name__)
        self.myLogger.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(name)s: %(message)s')

        file_handler = logging.FileHandler(f"{log_file_name_head}_coordinator_log.log") #comment in/out
        file_handler.setFormatter(formatter) #comment in/out

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        self.myLogger.addHandler(file_handler) #comment in/out
        self.myLogger.addHandler(stream_handler)




        


    """
    JOYSTICK CONTROL SECTION
        The only method that should be called on from this section from outside this class is start_joystick(). The
        rest of the methods are supporting functions for the operation of start_joystick()
    """

    def monitor_joystick_commands(self, selected_stage):
        """ 
        This method retrieves lists of valid input tuples from the joystick class.
        Input tuples contain:
            (1) input string name 
            (2) respective index value
        The inputs are stored by type and the joystick lists are reset.
        The inputs are then used to call commands according the joystick profile.
        The called commands are given 3 arguments:
            (1) the joystick class instance
            (2) the input type
            (3) the index of the input value (based on the respective input type's list of input values)

        """
        my_stage = self.myModules.myStages[selected_stage]

        while self.monitoring_joystick:

            pressed_buttons, pressed_hats, pressed_axes = self.myModules.myJoysticks[0].deliver_controller_inputs()        

            self.myModules.myJoysticks[0].reset_values()

            for button in pressed_buttons:
                input_name = button[0]
                input_index = button[1]
                input_type = "button"
                method_name = self.active_joystick_profile.buttons_mapping[input_name]
                method = getattr(my_stage, method_name,)
                method(self.myModules.myJoysticks[0], input_type, input_index)

            for hat in pressed_hats:
                input_name = hat[0]
                input_index = hat[1]
                input_type = "hat"
                method_name = self.active_joystick_profile.hats_mapping[input_name]
                method = getattr(my_stage, method_name,)
                method(self.myModules.myJoysticks[0], input_type, input_index)
            
            for axis in pressed_axes:
                input_name = axis[0]
                input_index = axis[1]
                input_type = "axis"
                method_name = self.active_joystick_profile.axes_mapping[input_name] 
                method = getattr(my_stage, method_name)
                method(self.myModules.myJoysticks[0], input_type, input_index) 

            time.sleep(0.1)

    # joystick class exists but is ignored until this is called
    def start_joystick(self, selected_stage):
        """ This method opens a secondary thread to listen to the input of the joystick and calls listen_to_joystick on the main thread on a loop
        """
        my_stage = self.myModules.myStages[selected_stage]

        if not self.myModules.myJoysticks[0].pygame_running:
            self.active_joystick_profile = self.myModules.myJoystickProfiles[selected_stage]
            self.t1 = threading.Thread(target=self.myModules.myJoysticks[0].listening, args=(my_stage.stage_type,))
            self.t1.start()
            
            self.t2 = threading.Thread(target=self.monitor_joystick_commands, args=(selected_stage,))
            self.monitoring_joystick = True
            self.t2.start()

    # end threads started in start_joystick        
    def stop_joystick(self):
        self.myModules.myJoysticks[0].stop_listening()
        self.monitoring_joystick = False

        try:
            while self.t1.is_alive() or self.t2.is_alive():
                pass
        except:
            pass
    




    
    def volume_to_displacement_converter(self, stage=0, volume=0):
        """ This method converts a certain amount of volume into displacement needed to move that amount of liquid in the syringe by retrieving the syringe dimensions from the system and doing some simple math

        Args:
            volume ([float]): volume of liquid to be converted. UNIT: NANOLITERS

        Returns:
            [float]: displacement that results in the displacement of the provided volume on the syringe. UNIT: MILIMETERS
        """
        # Get the current syringe model
        syringe_model = self.myModules.myStages[stage].myLabware.get_syringe_model()

        # Extract syringe radius
        syringe_parameters = self.myModules.myStages[stage].myModelsManager.get_model_parameters(LABWARE_SYRINGE, syringe_model)
        diameter = syringe_parameters["inner_diameter"] # This parameter has units of mm
        radius = diameter / 2

        # Calculate area and distance (height of the cylindric volume)
        area = math.pi * radius**2 # Basic formula for area
        distance = volume * FROM_NANOLITERS / area # Volume is assumed to come in nanoLiters to it's converted to microliters to perform accurate calculations
        
        # DEBUGGING
        self.myLogger.info(f"Volume: {volume} [nanoliters]. Displacement: {distance} [mm]")

        # Return the distance needed to displace that amount of volume
        return distance

    def pick_up_liquid(self, stage=0, syringe_name="", volume=0, speed=0): 
        """ Sends a command to the syringe motor to displace a distance that is equivalent to aspirating a given volume of liquid

        Args:
            volume ([float]): volume of liquid to be aspirated. UNIT: NANOLITERS
            speed ([float]): speed at which the given volume of liquid will be aspirated. UNIT: MILIMITERS/SECOND
        """
        step_displacement = -1 * self.volume_to_displacement_converter(stage, volume) # Multiplied by -1 so that the step is negative	
        self.myModules.myStages[stage].stepSyringe(self.myModules.myStages[stage].syringesDefinitions[syringe_name], step_displacement, speed)	

    def drop_off_liquid(self, stage=0, syringe_name="", volume=0, speed=0):
        """ Sends a command to the syringe motor to displace a distance that is equivalent to dispensing a given volume of liquid

        Args:
            volume ([float]): volume of liquid to be dispensed,. UNIT: NANOLITERS
            speed ([float]): speed at which the given volume of liquid will be dispensed. UNIT: MILIMITERS/SECOND
        """
        step_displacement = self.volume_to_displacement_converter(stage, volume)	
        self.myModules.myStages[stage].stepSyringe(self.myModules.myStages[stage].syringesDefinitions[syringe_name], step_displacement, speed)
    

    """
    LABWARE METHODS SECTION
        This section specifies methods related to the adding and removing of labware components
    """

    def save_labware_setup(self, stage=0, output_file_name=""):
        """ Exports all the calibrated components to a file that can later be loaded onto the system to avoid recalibrating each component individually

        Args:
            output_file_name ([str]): desired name of output file
        """
        self.myModules.myStages[stage].myLabware.save_labware_to_file(output_file_name)
    
    def load_labware_setup(self, input_file_name, stage=0):
        """ Import previously calibrated and saved labware components from a json file to avoid recalibrating them individually

        Args:
            input_file_name ([str]): name of desired input file
        """
        self.myModules.myStages[stage].myLabware.load_labware_from_file(input_file_name)






def testing():
    myApp = Coordinator()
    # myApp.manual_control()
    # myApp.automatic_control(SCRIPT_NAME)

    keep_testing = True
    while keep_testing:
        well_or_wellplate_well = input("Well or wellplate_well? [\"w\"/\"p\"]:")
        chip_plate = int(input("In which chip/plate is this well/wellplate_well? "))
        nickname = input("What's its nickname? ")
        if well_or_wellplate_well == "W":
            myApp.go_to_well(chip_plate, nickname)
        else:
            myApp.go_to_wellplate_well(chip_plate, nickname)
        choice = input("Want to stop? [y/n]")
        if choice == "y":
            keep_testing = False

if __name__ == "__main__":
    testing()
