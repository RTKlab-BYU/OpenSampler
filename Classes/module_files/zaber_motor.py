"""
MOTOR CLASS 
    This class implements the basic functionalities of a Zaber X-series device and abstracts all the low level functions to a more
    intuitive and user-friendly interface. All the units are set to mm, mm/s, mm/s^2 by default
"""

import time

from zaber_motion import Library
from zaber_motion.ascii import Connection,SettingConstants
from zaber_motion import Units

MIN_GEAR = 0
MAX_GEAR = 2
GEARBOX = [0.2,1,4]

class Motor:
    # CONSTRUCTOR ---------------------------------------------------------------------
    def __init__(self, device, max_speed, tray_length, motor_type):
        self.homed = False # Boolean data member, allows for checking if device is homed at runtime
        self.script = [] # List of Move objects for automated execution
        self.scriptReceived = False
        self.axis = device.get_axis(1) # Gets the axis of motion to perfom displacements
        self.axis_settings = self.axis.settings # Gets the settings of the axis for manipulation
        self.tray_length = float(tray_length)
        self.axis_settings.set(setting=SettingConstants.LIMIT_MAX,value=self.tray_length,unit=Units.LENGTH_MILLIMETRES)
        self.motor_type = motor_type

        self.max_speed = float(max_speed)
        self.base_speed = 0 
        self.gear = MIN_GEAR
        self.gearbox = GEARBOX

        self.set_default_speed(self.max_speed)
        self.set_base_speed()

        # INITIALIZATION MOTION (OPTIONAL)
        # self.move_to(10)
        # self.move_to(0)

    # GETTERS ---------------------------------------------------------------------
    def get_id(self):
        return self.axis.identity.peripheral_id 

    def get_position(self):
        return self.axis.get_position(unit = Units.LENGTH_MILLIMETRES)

    def get_speed(self):
        return self.axis_settings.get("maxspeed", unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)

    def get_acceleration(self):
        return self.axis_settings.get("accel", unit = Units.ACCELERATION_MILLIMETRES_PER_SECOND_SQUARED)

    def get_script_status(self):
        return self.scriptReceived

    def get_gear(self):
        return self.gear + 1

    def get_gearbox(self):
        return self.gearbox

    # def get_base_speed(self):
    #     return self.base_speed

    def get_max_speed(self):
        return self.max_speed

    # This checks if the motor has been homed (AKA has a set reference point)
    def is_homed(self):
        return self.homed
    
    # SETTERS ---------------------------------------------------------------------
    def set_default_speed(self, speed):
        self.axis_settings.set("maxspeed", speed, unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)

    # base_speed * gearbox[max_gear] = max_speed
    def set_base_speed(self):
        self.base_speed = self.max_speed / self.gearbox[MAX_GEAR]

    def set_acceleration(self, accel):
        self.axis_settings.set("accel", accel, unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)

    # def set_gearbox(self, gear_list):
    #     self.gearbox = gear_list
    #     self.set_base_speed() # This needs to be reset, since the base speed depends on the gearbox configuration
    
    def reset_gear(self):
        self.gear = MIN_GEAR

    # GEAR FUNCTIONS --------------------------------------------------------------
    def shift_gear_up(self):
        if (self.gear < MAX_GEAR):
            self.gear = self.gear + 1
            return True
        else:
            return False

    def shift_gear_down(self):
        if (self.gear > MIN_GEAR):
            self.gear = self.gear - 1
            return True
        else:
            return False

    # MOVES ---------------------------------------------------------------------
    # Moves the stage to the 0 position and defines it as the reference point for future displacements
    def home(self):
        self.set_default_speed(self.max_speed)
        self.axis.home() 
        self.homed = True

    # Performs an absolute displacement to the given position
    def move_to(self, position):
        self.axis.move_absolute(position, unit = Units.LENGTH_MILLIMETRES, wait_until_idle = True)

    # Performs a relative displacement with the provided or default (1 mm) step value 
    def move_step(self, step = 1):
        negative_step = step < 0
        c1 = ( (self.get_position() - abs(step) ) >= 0 )
        c2 = ( (self.get_position() + abs(step)) <= self.tray_length)
        
        if ( (negative_step and c1) or (not(negative_step) and c2) ):
            self.axis.move_relative(step, unit = Units.LENGTH_MILLIMETRES, wait_until_idle = True)
        else:
            print(self.tray_length)
            print(step)
            print("Step too big, if performed motor will go beyond boundary. Cannot perform step")

    # Performs an indefinite displacement at a given speed (providing a modifier [0-1] measurement)
    def move_speed(self, modifier=1):
        speed = self.base_speed * self.gearbox[self.gear] * modifier
        self.axis.move_velocity(speed, unit = Units.VELOCITY_MILLIMETRES_PER_SECOND)

    # This is the digital equivalent to pressing the button on the motor. Erases the reference point
    # so the device needs to be homed again after this function is called
    def stop(self):
        self.axis.stop(wait_until_idle = True)
        self.homed = False
    
    """
    SCRIPTING FUNCTIONS (AUTOMATED MOTION) ---------------------------------------------------------
        This won't be used from the ZaberMotorSeries class. This is just for the purpose of testing individual motors
        if it's ever necessary. For the purpose of allowing for simpler coordination between motors, there will 
        only be a "Master Script" that will be run from the ZaberMotorSeries class and will execute each command or
        simultaneous commands sequentially. Again, this sections is ONLY for testing individual motors if ever 
        needed
    """
    
#     # Receives a script as a list of Move objects
#     def load_script(self, script):
#         self.script = script
#         self.scriptReceived = True

#     def print_script(self):
#         for command in range(len(self.script)):
#             print(self.script[command].to_string())

#     # Runs a sequence of commands specified in a list of Move objects
#     # Returns a boolean signifying if the motor has a script to run or not
#     # CATCH: scripts can only be run once, then they need to be reloaded
#     def run_script(self):
#         if(self.scriptReceived):
#             for command in self.script:
#                 self.set_speed(command.speed)
#                 self.move_to(command.position)
#             self.scriptReceived = False # Reset the script boolean (script only runs once)
#             return True # Returns True to signify that the Motor has a loaded script and just run it. Whoever calls this function can then print a status message with the name of the Motor
#         else:
#             return False # Returns False to signify that the Motor doesn't have a loaded script


# def testing():
#     # Open serial communication through the COM port
#     Library.enable_device_db_store() 
#     com_port = "COM11"
#     connection = Connection.open_serial_port(com_port)
#     print("{} port succesfully opened".format(com_port))
#     device_list = connection.detect_devices()
#     device = device_list[0]
#     # initialize a motor
#     myMotor1 = Motor(device)
#     # myMotor1.home()
#     # myMotor1.move_to(20)
#     # print("myMotor1 id: ", myMotor1.get_id())
#     # print("myMotor1 position: ", myMotor1.get_position(), "mm")
#     # print("myMotor1 speed: ", myMotor1.get_speed(), "mm/s")
#     # print("myMotor1 acceleration: ", myMotor1.get_acceleration(), "mm/s^2")
#     # myMotor1.set_speed(23)
#     # myMotor1.move_to(100)
#     myMotor1.home()
#     print("myMotor1 is homed: ", myMotor1.is_homed())
#     myMotor1.move_to(10)

#     print("Starting move_speed() test")
#     for i in range(5):
#         myMotor1.move_speed(5*i)
#         time.sleep(.5)
#     for i in range(5):
#         myMotor1.move_speed(5*-i)
#         time.sleep(.5)

# if __name__ == "__main__":
#     testing()