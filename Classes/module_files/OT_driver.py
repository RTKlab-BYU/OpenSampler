"""
Description of the program:

    This code contains a child class that is used to control the robot by single step movements. 
    The parent class is the driver that Opentrons have created to send commands to the OT2 
    
    In order to move a single axis an amount of units, we pass in the unit we want to use and the 
    amount we want the robot to move every step. There is a function on SmoothieDriver_3_0_0 class 
    that returns the position as a dicctionary in the following format: 

        { 'X': 150, 'Y': 150, 'Z': 170.15, 'A': 218.0, 'B': 0.0, 'C': 0.0}
volume
    The move on a single axis happens by using the method SmoothieDriver_3_0_0.move() wich moves to a 
    specified coordinate, but in this case we only change the coordinate that we need keeping the rest
    the same. 

"""
from opentrons.drivers.smoothie_drivers.driver_3_0 import SmoothieDriver_3_0_0 as SM, SmoothieError
from opentrons.drivers.rpi_drivers.gpio_simulator import SimulatingGPIOCharDev
from opentrons.drivers.command_builder import CommandBuilder
from opentrons.config.robot_configs import build_config
from serial.tools import list_ports
from numpy import pi
import os
from os import environ
import time
import threading
import json

from Classes.module_files.labware import Labware
from Classes.module_files.models_manager import ModelsManager

X_MAX = 418
X_MIN = 25
Y_MAX = 350
Y_MIN = 5
Z_MAX = 218
Z_MIN_NO_SYRINGE = 0
Z_MIN_WITH_SYRINGE = 30 
A_MAX = 218
A_MIN_NO_SYRINGE = 0
A_MIN_WITH_SYRINGE = 30

# These should be moved to syringe model files
SYRINGE_MAX = 18
SYRINGE_REST = -66
SYRINGE_MIN = -150

# these should be determined in system configuration
LEFT_SYRINGE_MOUNT_ATTACHED = True
RIGHT_SYRINGE_MOUNT_ATTACHED = False

SMOOTHIE_COMMAND_TERMINATOR = '\r\n\r\n'

DEFAULT_STEP_SIZE = 5 # Used for manual and protocol control when step size is not specified
SHORT_MEDIUM_STEP_LIMIT = 10 # used for determining appropriate motor speeds
MEDIUM_LONG_STEP_LIMIT = 50 # used for determining appropriate motor speeds
APPROACH_DISTANCE = 30 # Distance from target where robot slows down if needed

DEFAULT_STEP_SPEED = 10  # default speed for protocols (only used if user forgets to specify speeds)
SLOW_SPEED = 10  # mm/s
MEDIUM_SPEED = 40  # mm/s
HIGH_SPEED = 160  # mm/s
STEP_CHANGE = 50  # how much to decrease step size for continuous movement

SYRINGE_MM_FACTOR = 4  # 3.8896 4.16
DEFAULT_SYRINGE_STEP = 1 # mm 
DEFAULT_SYRINGE_SPEED = 0.25 # mm/s 


DEFAULT_VOL_STEP_SIZE = 400
LIST_OF_STEP_SIZES = [0.01, 0.1, 1, 5, 10, 25, 50]  # step sizes available for manual control, currently index must match volumes
LIST_OF_VOLUME_STEPS = [100, 200, 300, 400, 500, 1000, 1000]  # nL
DEFAULT_STEP_INDEX = 3 # Determines starting step size for manual control from LIST_OF_STEP_SIZES
DEFAULT_VOL_INDEX = DEFAULT_STEP_INDEX

LEFT = 'Left' #A
RIGHT = 'Right' #B

WINDOWS_OT_PORT = 'COM4'
WINDOWS_OT_SER = 'A50285BIA'
LINUX_OT_PORT = '/dev/ttyACM0'
MACBOOK_OT_PORT = "/dev/cu.usbserial-A50285BI"
LINUX_OS = 'posix'
WINDOWS_OS = 'nt'

class OT2_nanotrons_driver(SM):

    def __init__(self, myModules, motors_config):#, port):
        super().__init__(config=build_config({}),gpio_chardev=SimulatingGPIOCharDev("simulated"))
        operating_system = ""
        self.stage_type = "Opentrons"
        os_recognized = os.name
        side = motors_config["side"]
        
        self.myModules = myModules

        if os_recognized == WINDOWS_OS:
            operating_system = "w"
            # print("Windows Operating System Detected")
        elif os_recognized == LINUX_OS:
            operating_system = "r"

        # this should not be automatic
        self.myLabware = Labware(SYRINGE_MIN,SYRINGE_MAX,SYRINGE_REST)
        self.myModelsManager = ModelsManager(operating_system)

        # Atributes that control the size and speed of the X Y and Z axis. 
        #   When changed, all of them move at the same rate
        self.xyz_step_size_index = DEFAULT_STEP_INDEX
        self.xyz_step_size = LIST_OF_STEP_SIZES[self.xyz_step_size_index]
        
        self._port = None

        self.side = side
        self.right_syringe_mount_attached = RIGHT_SYRINGE_MOUNT_ATTACHED
        self.left_syringe_mount_attached = LEFT_SYRINGE_MOUNT_ATTACHED



        # These settings all start at the largest range afforded by the robot, but they can be artificially limited
        if self.left_syringe_mount_attached:
            self.z_min = Z_MIN_WITH_SYRINGE
        else:
            self.z_min = Z_MIN_NO_SYRINGE
        if self.right_syringe_mount_attached:
            self.a_min = A_MIN_WITH_SYRINGE
        else:
            self.a_min = A_MIN_NO_SYRINGE
        self.x_max = X_MAX
        self.x_min = X_MIN
        self.y_max = Y_MAX
        self.y_min = Y_MIN
        self.z_max = Z_MAX
        self.a_max = A_MAX
        self.safe_z = self.z_max  
        self.safe_a = self.a_max

        

        self.connect_driver()


# Functions that help movements    
    
    def check_for_valid_move(self, pos: float, axis: str) -> bool:
        """
        This function checks for limits. If the user tries to go too far, the move 
        will not be executed. Returns false if the move is outside the allowed limits
        """

        if axis == 'X' and (pos > self.x_max or pos < self.x_min):
            print("Not a valid move for X axis!")
            print(f"Requested move to: {pos}, axis max: {self.x_max}, axis min: {self.x_min}")
            return False
        elif axis == 'Y' and (pos > self.y_max or pos < self.y_min):
            print("Not a valid move for Y axis!")
            print(f"Requested move to: {pos}, axis max: {self.y_max}, axis min: {self.y_min}")
            return False
        elif axis == 'Z' and (pos > self.z_max or pos < self.z_min):
            print("Not a valid move for Z axis!")
            print(f"Requested move to: {pos}, axis max: {self.z_max}, axis min: {self.z_min}")
            return False
        elif axis == 'A' and (pos > self.a_max or pos < self.a_min):
            print("Not a valid move for A axis!")
            print(f"Requested move to: {pos}, axis max: {self.a_max}, axis min: {self.a_min}")
            return False
        elif axis == 'B' and (pos > self.myLabware.get_syringe_max() or pos < self.myLabware.get_syringe_min()):
            print("Not a valid move for B axis!")
            print(f"Requested move to: {pos}, axis max: {self.myLabware.get_syringe_max()}, axis min: {self.myLabware.get_syringe_min()}")
            return False
        elif axis == 'C' and (pos > self.myLabware.get_syringe_max() or pos <= self.myLabware.get_syringe_min()):
            print("Not a valid move for C axis!")
            print(f"Requested move to: {pos}, axis max: {self.myLabware.get_syringe_max()}, axis min: {self.myLabware.get_syringe_min()}")
            return False
        else:
            return True

    def check_speed(self, step_size):
        """
        This function sets a speed acording to the step size given.
        There are 3 different speeds that are assigned: Slow, Medium and High
        """
        if step_size <= SHORT_MEDIUM_STEP_LIMIT:
            return SLOW_SPEED
        elif step_size < MEDIUM_LONG_STEP_LIMIT:
            return MEDIUM_SPEED
        else:
            return HIGH_SPEED

    def step_size_up(self, *args, **kwargs):
        """"
        xyz_step_size is assigned from a list of available step sizes.
        This function first checks that the current step size is not the maximum step size on the list.
        If it is not, then xyz_step size is assigned to the next size up in the list.
        """
        if self.xyz_step_size != LIST_OF_STEP_SIZES[-1]:
            self.xyz_step_size_index += 1
            self.xyz_step_size = LIST_OF_STEP_SIZES[self.xyz_step_size_index]
            print(f"\nXYZ Manual Movement set to {self.xyz_step_size} mm\n")
        else:
            print("\nCannot further increase the Manual Control movement size")
            print(f"XYZ Manual Movement set to {self.xyz_step_size} mm\n")

    def step_size_down(self, *args, **kwargs):
        """"
        xyz_step_size is assigned from a list of available step sizes.
        This function first checks that the current step size is not the minimum step size on the list.
        If it is not, then xyz_step size is assigned to the next size down in the list.
        """
        if self.xyz_step_size_index > 0:
            self.xyz_step_size_index -= 1
            self.xyz_step_size = LIST_OF_STEP_SIZES[self.xyz_step_size_index]
            print(f"\nXYZ Manual Movement set to {self.xyz_step_size} mm\n")
        else:
            print("\nCannot further increase the Manual Control movement size")
            print(f"XYZ Manual Movement set to {self.xyz_step_size} mm\n")

    def uL_to_mm(self, volume):
        '''
        Converts uL to mm using syringe i.d.
        Syringe motors aren't correctly set to mm units.
        Empirical data suggests real movement is 1/4 mm per unit.
        '''
        syr_model = self.myLabware.syringe_model
        path_to_model = "models/syringes/"+syr_model+".json"
        with open(path_to_model, 'r') as myfile: # open file
            data = myfile.read()
        obj = json.loads(data)
        syr_radius = obj["inner_diameter"]/2 # in mm
        syr_cross_section = syr_radius**2*pi
        syringe_mm_distance = SYRINGE_MM_FACTOR*volume/syr_cross_section # 1 mm^3 per uL
        return syringe_mm_distance

    def add_or_remove_syringe_mount(self):
        
        if self.side == LEFT:
            if self.left_syringe_mount_attached:
                self.left_syringe_mount_attached = False
                self.z_min = Z_MIN_NO_SYRINGE 
                print("Removing left syringe in settings.")
                print("Make sure left syringe is really removed!")
            elif not self.left_syringe_mount_attached:
                self.left_syringe_mount_attached = True
                self.z_min = Z_MIN_WITH_SYRINGE 
                print("Attaching left syringe in settings.")
                print("Make sure left syringe is really attached!")
    
        elif self.side == RIGHT:
            if self.right_syringe_mount_attached:
                self.right_syringe_mount_attached = False
                self.a_min = A_MIN_NO_SYRINGE
                print("Removing right syringe in settings.")
                print("Make sure right syringe is really removed!")
            elif not self.right_syringe_mount_attached:
                self.right_syringe_mount_attached = True
                self.a_min = A_MIN_WITH_SYRINGE 
                print("Attaching right syringe in settings.")
                print("Make sure right syringe is really attached!")
        
        else:
            print("'self.side' not recognized")

    def move_safe_az(self, target):
        """
        make sure the unused axis is up and out of the way
        then compare the current and target positions
        move to 30 mm above the higher option if possible
        or move to the safe height if necessary

        currently safe heights default to max
        """
        if self.side == LEFT:
            self.move({'A': self.safe_a}, speed= MEDIUM_SPEED)

            current_z = self._position['Z']
            if target <= current_z and current_z + 30 < self.safe_z:
                self.move({'Z': current_z + 30}, speed= MEDIUM_SPEED)
            elif target >= current_z and target + 30  < self.safe_z:
                self.move({'Z': target  + 30}, speed= MEDIUM_SPEED)
            else:
                self.move({'Z': self.safe_z}, speed= MEDIUM_SPEED)

        elif self.side == RIGHT:
            self.move({'Z': self.safe_z}, speed= MEDIUM_SPEED)

            current_a = self._position['A']
            if target <= current_a and current_a + 30 < self.safe_a:
                self.move({'A': current_a + 30}, speed= MEDIUM_SPEED)
            elif target >= current_a and target + 30  < self.safe_a:
                self.move({'A': self.safe_a}, speed= MEDIUM_SPEED)
            else:
                self.move({'A': self.safe_a}, speed= MEDIUM_SPEED)

    def move_current_axis_safe_az(self):
        if self.side == LEFT:
            self.move({'Z': self.safe_z}, speed=MEDIUM_SPEED)
        elif self.side == RIGHT:
            self.move({'A': self.safe_a}, speed=MEDIUM_SPEED)

    def get_motor_coordinates(self):  
        self.update_position()
        if self.side == LEFT:
            x = self._position['X']
            y = self._position['Y']
            z = self._position['Z']
        elif self.side == RIGHT:
            x = self._position['X']
            y = self._position['Y']
            z = self._position['A']
        return (x, y, z)
    
    def get_syringe_location(self):
        if self.side == LEFT:
            self.update_position()
            s = self._position["B"]
        elif self.side == RIGHT:
            self.update_position()
            s = self._position["C"]
        return s
    
    def update_home_positions(self):
        x = self._position['X']
        y = self._position['Y']
        z = self._position['Z']
        a = self._position['A']
        self.x_max = x
        self.y_max = y
        self.z_max = z
        self.a_max = a

        self.safe_z = z
        self.safe_a = a

        print(f"\nHomed Coordinates: X - {x}, Y - {y}, Z - {z}, A - {a}")
         
    def home_all(self, *args, **kwargs): # all non-syringe motors
        try:
            self.home('X Y Z A')
            positions = self.update_position()
            self.update_home_positions()

        except SmoothieError:
            print("cannot Home motors at this time")

    def home_syringe(self, *args, **kwargs):
        try:
            if self.side == LEFT:
                if self.left_syringe_mount_attached:
                    self.home('B')
                else:
                    print("Must attach syringe before homing!")
            elif self.side == RIGHT:
                if self.right_syringe_mount_attached:
                    self.home('C')
                else:
                    print("Must attach syringe before homing!")
        except SmoothieError:
            print("cannot Home syringe at this time")


# Functions for discrete movement of the X, Y, Z, A and syringe motors: 

    def step_x_motor_left(self, *args, **kwargs):

        self.update_position()
        x_pos = self._position['X'] # stores the current position
        x_pos -= self.xyz_step_size # adds a step size to the current position

        if(self.check_for_valid_move(x_pos, 'X')): # if the future position is a valid move 
                self.move({'X': x_pos}, speed=self.check_speed(self.xyz_step_size))  # move to the indicated position
        # else:
        #     print("\nRequested move is not valid!\n")

    def step_x_motor_right(self, *args, **kwargs):

        self.update_position()
        x_pos = self._position['X'] # stores the current position
        x_pos += self.xyz_step_size # adds a step size to the current position

        if(self.check_for_valid_move(x_pos, 'X')): # if the future position is a valid move 
                self.move({'X': x_pos}, speed=self.check_speed(self.xyz_step_size)) # move to the indicated position
        # else:
        #     print("\nRequested move is not valid!\n")

    def step_y_motor_forward(self, *args, **kwargs):  

        self.update_position()
        y_pos = self._position['Y'] # stores the current position
        y_pos += self.xyz_step_size # adds a step size to the current position

        if(self.check_for_valid_move(y_pos, 'Y')): # if the future position is a valid move 
                self.move({'Y': y_pos}, speed=self.check_speed(self.xyz_step_size)) # move to the indicated position
        # else:
        #     print("\nRequested move is not valid!\n") 

    def step_y_motor_back(self, *args, **kwargs):

        self.update_position()
        y_pos = self._position['Y'] # stores the current position
        y_pos -= self.xyz_step_size # adds a step size to the current position

        if(self.check_for_valid_move(y_pos, 'Y')): # if the future position is a valid move 
                self.move({'Y': y_pos}, speed=self.check_speed(self.xyz_step_size)) # move to the indicated position
        # else:
        #     print("\nRequested move is not valid!\n")

    def step_z_motor_up(self, *args, **kwargs):
        self.update_position()
        if self.side == LEFT:
            z_pos = self._position['Z'] # stores the current position
            z_pos += self.xyz_step_size # adds a step size to the current position
            if(self.check_for_valid_move(z_pos, 'Z')): # if the future position is a valid move 
                self.move({'Z': z_pos}, speed=self.check_speed(self.xyz_step_size)) # move to the indicated position
            else:
                print("\nRequested move is not valid!\n")
        elif self.side == RIGHT:
            a_pos = self._position['A'] # stores the current position
            a_pos += self.xyz_step_size # adds a step size to the current position
            if(self.check_for_valid_move(a_pos, 'A')): # if the future position is a valid move 
                    self.move({'A': a_pos}, speed=self.check_speed(self.xyz_step_size)) # move to the indicated position
            # else:
            #     print("\nRequested move is not valid!\n")
        else:
            print(f"Side ({self.side}) not recognized.")   

    def step_z_motor_down(self, *args, **kwargs):
        self.update_position()
        if self.side == LEFT:
            z_pos = self._position['Z'] # stores the current position
            z_pos -= self.xyz_step_size # adds a step size to the current position
            if(self.check_for_valid_move(z_pos, 'Z')): # if the future position is a valid move 
                    self.move({'Z': z_pos}, speed=self.check_speed(self.xyz_step_size)) # move to the indicated position
            else:
                print("\nRequested move is not valid!\n")
        elif self.side == RIGHT:
            a_pos = self._position['A'] # stores the current position
            a_pos -= self.xyz_step_size # adds a step size to the current position
            if(self.check_for_valid_move(a_pos, 'A')): # if the future position is a valid move 
                    self.move({'A': a_pos}, speed=self.check_speed(self.xyz_step_size)) # move to the indicated position
            # else:
                # print("\nRequested move is not valid!\n")
        else:
            print(f"Side ({self.side}) not recognized.")   

    def step_syringe_motor_up(self, *args, **kwargs):
        '''
        Takes arguments of volume in nL and speed in nL/min
        Converts these into mm and mm/s
        '''

        if "speed" in kwargs:
            mm_per_s = self.uL_to_mm(float(kwargs["speed"])/60000) # nL/min ---> uL/s ---> mm/s 
        else:
            mm_per_s = DEFAULT_SYRINGE_SPEED # mm/s

        if "volume" in kwargs:
            mm = self.uL_to_mm(float(kwargs["volume"])/1000)  
        else:
            mm = DEFAULT_SYRINGE_STEP # mm 

        now_pos = self.get_syringe_location()
        move_pos = now_pos + mm
        
        if self.side == LEFT:
            if(self.check_for_valid_move(move_pos, 'B')): # if the future position is a valid move 
                self.move({'B': move_pos}, speed=mm_per_s) # move to the indicated position
        elif self.side == RIGHT:
            if(self.check_for_valid_move(move_pos, 'C')): # if the future position is a valid move 
                self.move({'C': move_pos}, speed=mm_per_s) # move to the indicated position
        else:
            print("Side not recognized.")

    def step_syringe_motor_down(self, *args, **kwargs):
        '''
        Takes arguments of volume in nL and speed in nL/min
        Converts these into mm and mm/s
        '''

        if "speed" in kwargs:
            mm_per_s = self.uL_to_mm(float(kwargs["speed"])/60000) # nL/min ---> uL/s ---> mm/s 
        else:
            mm_per_s = DEFAULT_SYRINGE_SPEED # mm/s 

        if "volume" in kwargs:
            mm = self.uL_to_mm(float(kwargs["volume"])/1000)  
        else:
            mm = DEFAULT_SYRINGE_STEP # mm
            
        now_pos = self.get_syringe_location()
        move_pos = now_pos - mm

        if self.side == LEFT:
            if(self.check_for_valid_move(move_pos, 'B')): # if the future position is a valid move 
                self.move({'B': move_pos}, speed=mm_per_s) # move to the indicated position
        elif self.side == RIGHT:
            if(self.check_for_valid_move(move_pos, 'C')): # if the future position is a valid move 
                self.move({'C': move_pos}, speed=mm_per_s) # move to the indicated position
        else:
            print("Side not recognized.")

    def move_to(self, location):
        '''
        This function breaks a location tuple into its respective pieces. 
        Then it checks with the motors for a real position update.
        Next it checks that each component of the move is an allowed movement (in bounds).
        Before moving to the desired location it moves the z and a axes out of the way.
        Then finally it sends the commands to move to the target location.
        '''

        x = location[0] 
        y = location[1] 
        z = location[2]

        self.update_position()
        current_z_pos = self._position['Z']
        current_a_pos = self._position['A']


        if(self.check_for_valid_move(y, 'Y')):            
            if(self.check_for_valid_move(x, 'X')):
                
                if self.side == LEFT:
                    if(self.check_for_valid_move(z, 'Z')):
                        self.move_safe_az(z)
                        self.move({'Y': y}, speed= MEDIUM_SPEED)
                        self.move({'X': x}, speed= MEDIUM_SPEED)
                        if (current_z_pos + 5) < self.z_max:
                            self.move({'Z': z + 5}, speed= MEDIUM_SPEED)
                        self.move({'Z': z}, speed= SLOW_SPEED)
                elif self.side == RIGHT:
                    if(self.check_for_valid_move(z, 'A')):
                        self.move_safe_az(z)
                        self.move({'Y': y}, speed= MEDIUM_SPEED)
                        self.move({'X': x}, speed= MEDIUM_SPEED)
                        if (current_a_pos + 5) < self.a_max:
                            self.move({'A': z + 5}, speed= MEDIUM_SPEED)
                        self.move({'A': z}, speed= SLOW_SPEED)

    def small_move_xy(self, location, move_speed=SLOW_SPEED):
        '''
        This function breaks a location tuple into its respective pieces. 
        Then it checks with the motors for a real position update.
        Next it checks that each component of the move is an allowed movement (in bounds).
        Before moving to the desired location it moves the z and a axes out of the way.
        Then finally it sends the commands to move to the target location.
        '''

        x = location[0] 
        y = location[1]
        z = location[2]

        self.update_position()

        self.move({'X': x, 'Y': y, 'Z': z}, speed=move_speed)
        # self.move({'X': x}, speed=move_speed)
                
    def move_syringe_to(self, location, vol_speed=3000): #nL/min
        mm_speed = self.uL_to_mm(vol_speed/1000)/60 #nL to uL
        self.update_position()
        if self.side == LEFT:
            if(self.check_for_valid_move(location, 'B')):
                self.move({'B': location}, speed= mm_speed)
        elif self.side == RIGHT:
            if(self.check_for_valid_move(location, 'C')):
                self.move({'C': location}, speed= mm_speed)
        else:
            print("Side not recognized.")


# Other

    def unassigned(self, *args, **kwargs):
        pass

    def close_motors_connection(self, *args):
        try:
            self.disconnect()
        except:
            print("Not Connected")

    def find_port(self):
        """
        This allows the class to connect to a port when called, this makes the calling chain cleaner. 
        It is basicaly a get_port_by_name from the driver_3_0_0 that does not work
        """
        ports = list_ports.comports()
        operating_system = os.name
        for p in ports:
            if operating_system == WINDOWS_OS and p.serial_number == WINDOWS_OT_SER:
                self._port = p.device
                print(f"\nOT2 connected to: {p}\n")
            elif operating_system == LINUX_OS:
                if p == LINUX_OT_PORT or p.device == MACBOOK_OT_PORT:
                    self._port = p.device
                    print(f"\nOT2 connected to: {p}\n")
            
    def connect_driver(self):
        """
        This function is called at the beginning of the class in the init function to connect the robot
        """
        self.find_port()
        if self._port not in self.myModules.used_stages.keys():
            self.connect(self._port)
            self.myModules.used_stages[self._port] = [self._connection]
            self.myModules.used_stages[self._port].append(self.side)
            self.home_all()
        else:
            self._connection = self.myModules.used_stages[self._port][0]
            self.myModules.used_stages[self._port].append(self.side)
            self.simulating = False
            self._setup()
            self.update_home_positions()
def test():
    robot = OT2_nanotrons_driver()
    robot.find_port()

if __name__ == '__main__':
    test()