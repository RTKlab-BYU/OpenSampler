"""
JOYSTICK CLASS 
    This implements the methods needed to read the inputs from an Xbox 360 controller. It also
    handles operational discrepancies of pygame 1.9.6 between Windows and Raspberry OS (any linux
    OS really )
"""
from os import environ 
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # this line keeps pygame from printing a message when initiated 
import pygame
import time

# JOYSTICK BUTTONS MAPPING
BUTTONS_DICT_W = { 0:"A", 1:"B", 2:"X", 3:"Y", 4:"LB", 
                 5:"RB", 6:"BACK", 7:"START", 8:"LSTICK", 
                 9:"RSTICK" }

BUTTONS_DICT_R = { 0:"A", 1:"B", 2:"X", 3:"Y", 4:"LB", 
                 5:"RB", 6:"BACK", 7:"START", 8:"XBOX", 9:"LSTICK", 
                 10:"RSTICK" }


# only the vertical and horizontal inputs are used, not the diagonal combinations
HATS_USED_DICT = { (0,1):"HAT_UP", (0,-1):"HAT_DOWN", (-1,0):"HAT_LEFT", (1,0):"HAT_RIGHT"} 

AXES_DICT = {(0,-1):"L_STICK_LEFT",(0,1):"L_STICK_RIGHT",(1,1):"L_STICK_DOWN",(1,-1):"L_STICK_UP",
             (2,-1):"R_STICK_LEFT",(2,1):"R_STICK_RIGHT",(3,1):"R_STICK_DOWN",(3,-1):"R_STICK_UP",
             (4,1):"L_TRIGGER",(5,1):"R_TRIGGER"}


WINDOWS_OS = "w"
RASPBERRY_OS = "r"
THRESHOLD = 0.2 # This is the minimum value a joystick axes has to be to be read, otherwise it's considered 0

class XboxJoystick:
    """
    INITIAL VALUES 
    """
    def __init__(self, operating_system):
        # Store the value of the OS string given in the argument
        self.os = operating_system # Either the string "w" for windows or "r" for raspberry pi

        self.pygame_running = False
        self.joystick_1 = None
        self.stop_joystick = False

        self.axes = []
        self.hats = []
        self.buttons = []

        self.pressed_buttons = []
        self.pressed_hats = []
        self.pressed_axes = []

        if self.os == WINDOWS_OS:
            self.buttons_dict = BUTTONS_DICT_W

        elif self.os == RASPBERRY_OS:
            self.buttons_dict = BUTTONS_DICT_R

        else:
            print("Operating System not recognized by joystick!")

        self.should_sleep = True
        
    # this function is used to reset the values of pressed inputs lists before adding new ones
    def reset_values(self):
        self.pressed_buttons = []
        self.pressed_hats = []
        self.pressed_axes = [] 

    # initializes pygame, pygame.joystick, and an instance of the controller (xbox style controller) 
    def start_pygame(self):

        if self.pygame_running == False:
            pygame.init()
            # pygame.joystick.init()
            self.joystick_1 = pygame.joystick.Joystick(0)
            self.pygame_running = True
            self.initial_buttons = [self.joystick_1.get_button(i) for i in range(self.joystick_1.get_numbuttons())]
            self.initial_hats = [self.joystick_1.get_hat(i) for i in range(self.joystick_1.get_numhats())]
            self.initial_axes = [int(self.joystick_1.get_axis(i)) for i in range(self.joystick_1.get_numaxes())]
            self.buttons = self.initial_buttons
            self.hats = self.initial_hats
            self.axes = self.initial_axes

    # deinitializes pygame, pygame.joystick, and an instance of the controller (xbox style controller)
    def end_pygame(self):
        
        if self.pygame_running == True:
            pygame.quit()
            # pygame.joystick.quit()
            self.pygame_running = False
    
    # this function prevents light/unintended axis events from calling axis commands
    def false_axes_event_filter(self, axes):
        for axis in range(len(axes)):
            if abs(axes[axis]) < THRESHOLD:
                axes[axis] = 0
            else:
                pass
        return axes

    # this function is used to retrieve the pressed inputs lists
    def deliver_controller_inputs(self):
        return self.pressed_buttons, self.pressed_hats, self.pressed_axes

    """
    LISTEN SECTION
    """

    # Listens to the controller's input, meant to be used inside a thread
    def listening(self, stage_type=""):
        '''
        This function is designed to be run inside a thread to monitor pygame for joystick activity.
        When inputs trigger a pygame event, they are evaluated for validity.
        Valid inputs are packages as tuples containing:
            (1) input string name 
            (2) respective index value
        The tuples are appended to lists according to input type.
        The lists can be accessed and reset by Coordinator.
        '''

        if stage_type == "Opentrons":
            self.should_sleep = True
        else:
            self.should_sleep = False
        # print(f"should i sleep: {self.should_sleep}")
        self.start_pygame()
        self.stop_joystick = False
        listening = True

        while listening:
            
            if self.stop_joystick == True:
                self.end_pygame()
                listening = False
                return listening

            for event in pygame.event.get(): # retrieves the most recent joystick inputs from pygame  
                if self.stop_joystick == True:
                    self.end_pygame()
                    listening = False
                    return listening

                # Button down events, just like it sounds (when you press a button)
                elif event.type == pygame.JOYBUTTONDOWN:
                    previous_buttons = self.buttons
                    self.buttons = [self.joystick_1.get_button(index) for index in range(self.joystick_1.get_numbuttons())]
                    if (self.buttons != self.initial_buttons and previous_buttons == self.initial_buttons):

                        for button_index in range(len(self.buttons)):
                            if self.buttons[button_index] != 0:
                                button_name = self.buttons_dict[button_index]
                                if self.should_sleep:
                                    self.pressed_buttons = [(button_name, button_index)]
                                    time.sleep(0.5)
                                else:
                                    self.pressed_buttons.append((button_name, button_index))

                        

                # Releasing buttons are treated as separate events from pressing them down, updates position values
                elif event.type == pygame.JOYBUTTONUP:
                    self.buttons = [self.joystick_1.get_button(index) for index in range(self.joystick_1.get_numbuttons())]

                # Hat motion events (aka D-pad)
                elif event.type == pygame.JOYHATMOTION:
                    previous_hats = self.hats
                    self.hats = [self.joystick_1.get_hat(index) for index in range(self.joystick_1.get_numhats())]
                    if (self.hats != self.initial_hats) and (previous_hats == self.initial_hats):

                        for hat_index in range(len(self.hats)):
                            if self.hats[hat_index] in HATS_USED_DICT.keys():
                                hat_name = HATS_USED_DICT[self.hats[hat_index]]
                                if self.should_sleep:
                                    self.pressed_hats = [(hat_name, hat_index)]
                                    time.sleep(0.5)
                                else:
                                    self.pressed_hats.append((hat_name, hat_index))

                # Axis motion events (aka triggers and thumbsticks)
                elif event.type == pygame.JOYAXISMOTION:
                    previous_axes = self.axes
                    axes = []
                    for index in range(self.joystick_1.get_numaxes()):
                        axis_value = self.joystick_1.get_axis(index)

                        # change trigger values to range 0-1
                        if index == 4 or index == 5:
                            axis_value = (axis_value+1)/2
                            
                        axes.append(axis_value)
                    
                    self.axes = self.false_axes_event_filter(axes)

                    if (self.axes != self.initial_axes):
                        for axis_index in range(len(self.axes)):

                            #  which direction
                            if  self.axes[axis_index] > 0 and previous_axes[axis_index] == 0:
                                axis_key = (axis_index,1)
                                if self.should_sleep:
                                    self.pressed_axes = [(AXES_DICT[axis_key], axis_index)]
                                    time.sleep(0.5)
                                else:
                                    self.pressed_axes.append((AXES_DICT[axis_key], axis_index))

                            elif self.axes[axis_index] < 0 and previous_axes[axis_index] == 0:
                                axis_key = (axis_index,-1)
                                if self.should_sleep:
                                    self.pressed_axes = [(AXES_DICT[axis_key], axis_index)]
                                    time.sleep(0.5)
                                else:
                                    self.pressed_axes.append((AXES_DICT[axis_key], axis_index))
                       
                else: 
                    pass

                

    # this function triggers the termination of an thread using the listening function
    def stop_listening(self):
        self.stop_joystick = True


