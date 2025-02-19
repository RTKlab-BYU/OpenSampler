"""
LABWARE CLASS
    This class allows for labware (Chip and Plate) components management, like adding, deleting, and getting parameters
    from each of them.
"""

from Classes.module_files.plate import Plate

import os
import json

RELATIVE_PATH = "saved_labware"
# LABWARE_CHIP = "C"
# LABWARE_PLATE = "W"
DEFAULT_SYRINGE_MODEL = "Not Selected"

LINUX_OS = 'posix'
WINDOWS_OS = 'nt'

class Labware:

    def __init__(self, syringe_min, syringe_max, syringe_rest_position):
        self.syringe_model = DEFAULT_SYRINGE_MODEL
        self.syringe_default_min = syringe_min
        self.syringe_default_max = syringe_max
        self.default_rest_location = syringe_rest_position
        self.plate_list = []
        self.reset_syringe_settings()
        self.custom_locations = {}




    """
    SETTERS SECTION
    """

    def remove_plate(self, plate_index):
        self.plate_list.pop(plate_index)

    def set_syringe_model(self, model_name):
        self.syringe_model = model_name
    
    def reset_syringe_settings(self):
        self.syringe_rest_position = self.default_rest_location
        self.syringe_model = DEFAULT_SYRINGE_MODEL
        self.syringe_min = self.syringe_default_min
        self.syringe_max = self.syringe_default_max
    
    def set_syringe_min(self, new_min):
        self.syringe_min = new_min

    def set_syringe_max(self, new_max):
        self.syringe_max = new_max

    def set_syringe_rest(self, new_rest):
        self.syringe_rest_position = new_rest

    def add_custom_location(self, custom_location_name: str, location: tuple):
        self.custom_locations[custom_location_name] = location

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
    
    def get_plate_models(self):
        models = []
        for plate in self.plate_list:
            models.append(plate.get_model_name())
        
        return models

    def get_custom_locations(self):
        return self.custom_locations.keys()

    def get_current_labware(self):
        labware = dict()
        # labware["chips"] = self.get_chip_models()
        labware["plates"] = self.get_plate_models()
        labware["syringe"] = self.get_syringe_model()
        labware["custom_locations"] = self.get_custom_locations()
        return labware

    
    def get_well_location(self, plate, well) -> tuple: 
        location = self.plate_list[plate].get_location_by_nickname(well)
        return location


    """
    Useful Functions
    """

    # String input looks like: "w 1E3" or "c 1B3" : "[component] [component_index][well/wellplate_well nickname]"
    def check_well_exists(self, wellplate, well):
        # Unpack variables from the input string

        # index = int(container.split(" ")[0])
        # nickname = container.split(" ")[1]

        return self.plate_list[wellplate].verify_nickname_existence(well)
    
    def check_custom_location_exists(self, nickname):
        
        return nickname in self.custom_locations.keys()


    # Create a new plate object from calibration 
    def create_new_plate(self, properties):
        new_plate = Plate()
        new_plate.compile_plate_properties(properties)
        self.plate_list.append(new_plate)


    # This method parses the list of chips and plates and outputs a dictionary with all the parameters of all the labware components
    def labware_to_dictionary(self):
        labware_dictionary = {}
        labware_dictionary["chips"] = list()
        labware_dictionary["plates"] = list()
        labware_dictionary["custom_locations"] = self.custom_locations


        # Iterate through plates list, extract properties of each plate, and store in labware_dictionary
        for plate in self.plate_list:
            plate_properties = plate.export_plate_properties()
            labware_dictionary["plates"].append(plate_properties)

        

        # print(f"Labware dictionary: {labware_dictionary}")
        return labware_dictionary

    def dictionary_to_labware(self, labware_dictionary):
        # print(f"Current Labware before additions: {self.get_current_labware()}")
        
        plates_list = labware_dictionary["plates"] # This is a list of dictionaries, each of which containes prooperties for a given plate
        locations_list = labware_dictionary["custom_locations"]

        # Iterate through plates_list and create a Plate object out of each dictionary
        for plate_properties in plates_list:
            new_plate = Plate()
            new_plate.compile_plate_properties(plate_properties)
            self.plate_list.append(new_plate)

        for custom_location in locations_list.keys():
            self.custom_locations[custom_location] = locations_list[custom_location]
            
        # print(f"Current Labware after additions: {self.get_current_labware()}")

    def get_path_to_saved_labware_folder(self):
        current_path = os.getcwd() # Returns a string representing the location of this file
        path_of_interest = os.path.join(current_path, RELATIVE_PATH) # Joins the current location with the name of the folder thhat contains all the saved labware setup files
        return path_of_interest

    def save_labware_to_file(self, file_name):
        # Path
        folder_path = self.get_path_to_saved_labware_folder()
        file_path = os.path.join(folder_path, file_name) # Add the name of the file of interest to that path string

        # Create a json file
        output_file = open(file_path, "w")

        # Create a dictionary out of the current labware 
        labware_dictionary = self.labware_to_dictionary()

        # Dump the labware dictionary into the json file
        json.dump(labware_dictionary, output_file)

    def load_labware_from_file(self, file_name):
        # Path
        folder_path = self.get_path_to_saved_labware_folder()
        file_path = os.path.join(folder_path, file_name) # Add the name of the file of interest to that path string

        # Open an existing json file
        input_file = open(file_path, "r")

        # Create a dictionary out of the data in the specified json file
        labware_dictionary = json.load(input_file)

        # Create labware out of the dictionary
        self.dictionary_to_labware(labware_dictionary)
        
    def available_saved_labware_files(self):
        return os.listdir(self.get_path_to_saved_labware_folder())

