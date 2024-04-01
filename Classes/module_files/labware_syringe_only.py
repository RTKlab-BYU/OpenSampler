"""
LABWARE CLASS
    This class allows for labware (Chip and Plate) components management, like adding, deleting, and getting parameters
    from each of them.
"""

RELATIVE_PATH = "saved_labware"
# LABWARE_CHIP = "C"
# LABWARE_PLATE = "W"
DEFAULT_SYRINGE_MODEL = "None"

LINUX_OS = 'posix'
WINDOWS_OS = 'nt'

class Labware:

    def __init__(self, syringe_min, syringe_max, syringe_rest_position):
        self.syringe_default_min = syringe_min
        self.syringe_default_max = syringe_max
        self.default_rest_location = syringe_rest_position
        self.reset_syringe_settings()

    """
    SETTERS SECTION
    """
    def set_syringe_model(self, model_name):
        self.syringe_model = model_name
    
    def reset_syringe_settings(self):
        self.syringe_model = self.default_rest_location
        self.syringe_min = self.syringe_default_min
        self.syringe_max = self.syringe_default_max
    
    def set_syringe_min(self, new_min):
        self.syringe_min = new_min

    def set_syringe_max(self, new_max):
        self.syringe_max = new_max

    def set_syringe_rest(self, new_rest):
        self.syringe_rest_position = new_rest

    """
    GETTERS SECTION
    """
    def get_syringe_model(self):
        return self.syringe_model
    
    def get_syringe_min(self):
        return self.syringe_min
    
    def get_syringe_max(self):
        return self.syringe_max
    
    def get_syringe_rest(self):
        return self.syringe_rest_position


    