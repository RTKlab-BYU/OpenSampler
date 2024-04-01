"""
MOVES CLASS 
    This class aids when automating displacements in the Zaber X-series motors
    Specifies a move provided 3 parameters:
    1. Device (motor index)
    2. Target Position/Displacement
    3. Speed with which to perform the motion

    This parameters are specified in the form of a string as follows:
    "[device_id] [target_position] [speed]"
"""

class Move:
    # Constructor - a whole string provided as: "[device_id] [target_position] [speed]"
    def __init__(self, command):   
        self.motor_id, self.position, self.speed, *filler = command.split()
        self.motor_id = int(self.motor_id)
        self.position = float(self.position)
        self.speed = float(self.speed)

    # Returns the device, target position, and speed of the stored move
    def get_move(self):
        return self.motor_id, self.position, self.speed
    
    # Prints the move
    def to_string(self, template = "Move{{ id:{}, pos:{}, speed:{} }}"):
        return template.format(self.motor_id, self.position, self.speed)


def testing():
    # Read from a file a list of commands and execute them accordingly
    # Each command comes to fill the values of the Moves class
    # The Moves class contains: motor ID, position, and speed

    # IMPORT COMMANDS FROM AN INPUT FILE ----------------------------------------

    commands = []
    for line in open("sample_commands.txt", "r"):
        command = Move(line)
        commands.append(command)
        # myid, pos, sp = command.get_move()
        # print("The received Move is: device: {}, position: {}, speed: {}".format(myid, pos, sp))

    # EXECUTE IMPORTED COMMANDS -------------------------------------------------

    myMotor = Motor(0, "COM11")
    myMotor.home()

    for command in commands:
        device, position, speed = command.get_move()
        print("Command being executed: device[ {} ], target_position[ {} ], speed[ {} ]".format(device, position, speed))
        myMotor.set_speed(speed)
        myMotor.move_to(position)

if __name__ == "__main__":
    testing()