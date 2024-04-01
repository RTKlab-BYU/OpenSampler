"""
PLATE CLASS
    This class serves the purpose of encapsulating each plate with its intuitive parameters such as well plate types, well locations,
     and names of custom locations. wellplate_well is defined as the container that can hold a vial containing reagent.
    The indeces of each wellplate_well (in the well_locations list) correspond to their geographical location on a rectangle 
    laying down on its long side, going from left to right on each row, and going row by row from top to bottom
"""

class Plate:
    # Plate can be either partially constructed with basic parameters (model and grid) and be calibrated/populated later or fully constructed with a dictionary of pre-recorded parameters
    def __init__(self):
        # Normal initialization (no properties dictionary provided)
        self.model = []
        self.grid = []
        self.well_locations = []
        self.well_depth = [] # This will say how deep is a wellplate_well
        self.nicknames = [] # Assigns a nickname to each well given their index
        self.nicknames_inv = {} # Maps the nicknames to a specific well index

    def export_plate_properties(self):
        plate_properties = {}
        plate_properties["model"] = self.model # Load model name
        plate_properties["grid"] = self.grid # Load grid
        plate_properties["well_locations"] = self.well_locations # Load well_locations
        plate_properties["well_depth"] = self.well_depth # Load well_types
        plate_properties["nicknames"] = self.nicknames # Load well_nicknames

        return plate_properties

    # This method receives a dictionary with plate properties and fills up the internal variables of the instance of Plate with those
    def compile_plate_properties(self, plate_properties):
        self.model = plate_properties["model"] # Load model name
        self.grid = plate_properties["grid"] # Load grid
        self.well_depth = plate_properties["well_depth"] # Load well_depth
        self.nicknames = plate_properties["nicknames"] # Load nicknames
        self.well_locations = plate_properties["well_locations"] # Load well_locations
        self.nicknames_inv = {}
        for index in range(len(self.nicknames)):
            self.nicknames_inv[self.nicknames[index]] = index

    # Stores the location of a specified wellplate_well
    def set_locations(self, locations: list):
        self.well_locations = locations
    
    # Stores the nickname of a specified wellplate_well
    def set_nicknames(self, nicknames):
        self.nicknames = nicknames
        for index in range(len(self.nicknames)):
            self.nicknames_inv[self.nicknames[index]] = index

    # Stores the depth of the speficied wellplate_well
    def set_well_depth(self, well_depth):
        self.well_depth= well_depth

    

    # Gets the nickname stored for the specified wellplate_well
    def get_nickname(self, wellplate_well_index):
        return self.nicknames[wellplate_well_index]
    
    # Gets the depth of the speficied wellplate_well 
    def get_wellplate_well_depth(self, wellplate_well_index):
        return self.well_depth[wellplate_well_index]

    # Gets the grid arrangement speficied on initialization
    def get_grid(self):
        return self.grid
    
    # Returns the xyz coordinates of a given wellplate_well specified by its nickname    
    def get_location_by_nickname(self, well):
        return self.well_locations[self.nicknames_inv[well]]

    # Returns the location of a given wellplate_well specified by its index
    def get_location_by_index(self, wellplate_well_index):
        return self.well_locations[wellplate_well_index]

    # Checks if a specified alphanumeric well designation exists in the Plate object
    def verify_nickname_existence(self, nickname):
        # print(self.nicknames)
        return nickname in self.nicknames

    # Returns the model stored during initialization of the object
    def get_model_name(self):
        return self.model




