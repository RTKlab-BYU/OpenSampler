
import tkinter as tk
import threading
import numpy as np
import time

from Classes.coordinator import Coordinator


class Calibrator:

    def __init__(self) -> None:
        self.back_left_point = (0,0,0)
        self.front_left_point = (0,0,0)
        self.back_right_point = (0,0,0)
        self.fourth_point = (0,0,0)
        self.well_locations = []
        self.well_nicknames = []

        
        self.tested = False 
        
    # This method receives three calibration (fiducial) points and compiles the 4th
    def guess_fourth_calibration_point(self):

        # make points into np arrays
        blp = np.array(self.back_left_point)
        brp = np.array(self.back_right_point)
        flp = np.array(self.front_left_point)

        # Construct vectors
        row_vector = brp - blp
        column_vector = flp - blp

        # Calculate 4th point
        frp = blp + row_vector + column_vector
        x,y,z = frp[0],frp[1],frp[2]
        self.fourth_point = (x,y,z)


    # This method compiles all the nicknames (A1, A2...) as a continuous single list from a list of lists
    def compile_nicknames(self, nicknames_list) -> list:
        for index in range(len(nicknames_list)):
            self.well_nicknames += nicknames_list[index]


    # This method takes the parameters of the plate plus its calibration points and returns a list of the locations of all the wellplate_wells in that plate
    def map_out_wells(self, stage_type, parameters):
        
        # Extract useful information from plate_parameters
        grid = parameters["grid"]
        # wellplate_well_distance = plate_parameters["wellplate_wellDistance"]
        welldepth = parameters["well_depth"]
        if stage_type == "Zaber_XYZ":
            welldepth = -1*welldepth #flipped z axis, tip is stationary
        offset = float(parameters["fiducialDisplacement"])
        
        # make points into np arrays
        blp = np.array(self.back_left_point)
        brp = np.array(self.back_right_point)
        flp = np.array(self.front_left_point)

        # unit vectors
        row_uv = (brp - blp) / (grid[1] + offset*2 - 1)  # accounts for offset spacing
        column_uv = (flp - blp) / (grid[0] - 1)

        # location of well "A1"
        start_point = blp + row_uv * offset  # start at first well, not calibration point 

        # Go through each row and column, create locations, and append them to the locations list
            # NOTICE: the order in which they are stored is row by row from left to right
        for row in range(grid[0]):
            row_start_point = start_point + (column_uv * row)  # doesn't change first time since row = 0, moves down a row each time after
            for column in range(grid[1]):
                location = row_start_point + (row_uv * column)  # adds appropriate distance from A1 accross row 
                x,y,z = location  # remove values from numpy array
                z = z - welldepth # Go to the bottom of the wellS
                self.well_locations.append((x,y,z))  # add tuple location to list





class Calibration(tk.Toplevel,):
    def __init__(self, coordinator, selected_stage: int, model_name: str):
        tk.Toplevel.__init__(self)    
      
        self.title("Calibrate New Location")
        tk.Label(self, text=model_name, font="Helvetica 18",justify=tk.LEFT).pack(side=tk.TOP)
        self.component_type = "W"
        self.selected_stage = selected_stage
        self.coordinator: Coordinator = coordinator 
        self.model_parameters = self.coordinator.myModules.myStages[self.selected_stage].myModelsManager.get_model_parameters(self.component_type, model_name)
        
        self.calibrator = Calibrator()
        self.model_name = model_name
        self.geometry("700x450")
        
        # buttons to start and stop joystick
        self.joyBar = tk.Frame(self)
        self.joyBar.pack(side=tk.TOP)
        self.joyButton = tk.Button(self.joyBar,text="Start Joystick",command=lambda: self.start_joystick(),justify=tk.LEFT)
        self.joyButton.grid(row=0,column=1)
        self.killButton = tk.Button(self.joyBar,text="Kill Joystick",command=lambda: self.kill_joystick(),justify=tk.LEFT)
        self.killButton.grid(row=0,column=2)
        self.killButton["state"] = "disabled"


        # this section sort of shows the layout... 
        back_right_well = self.model_parameters["nicknames"][0][-1]
        back_left_well = self.model_parameters["nicknames"][0][0]
        front_left_well = self.model_parameters["nicknames"][-1][0]
        front_right_well = self.model_parameters["nicknames"][-1][-1]
        self.previewGrid = tk.Frame(self, bg="gray")
        self.previewGrid.pack(side=tk.TOP)
        tk.Label(self.previewGrid, text="Back Left: " + back_left_well).grid(row=0,column=0)
        tk.Label(self.previewGrid, text="Back Right: " + back_right_well).grid(row = 0,column=6)
        tk.Label(self.previewGrid, text="Front Left: " + front_left_well).grid(row = 3,column = 0)
        tk.Label(self.previewGrid, text="Front Right: " + front_right_well).grid(row = 3,column = 6)
        for rw in range(0,4):
            for col in range(1,5):
                tk.Label(self.previewGrid,text="o").grid(row=rw,column=col)
        
        # these are current coordinates
        x,y,z = coordinator.myModules.myStages[self.selected_stage].get_motor_coordinates()

        # display the current location of the stage being used
        tk.Label(self, text="Current Location",justify=tk.LEFT).pack(side=tk.TOP)
        self.LocationFrame = tk.Frame(self,bg="black")
        self.LocationFrame.pack(side=tk.TOP)
        self.current_x = tk.DoubleVar(self, x)
        self.current_y = tk.DoubleVar(self, y)
        self.current_z = tk.DoubleVar(self, z)
        self.current_x_label = tk.Label(self.LocationFrame, textvariable=self.current_x,justify=tk.LEFT,bg="black",fg="green")
        self.current_y_label =tk.Label(self.LocationFrame, textvariable=self.current_y,justify=tk.LEFT,bg="black",fg="green")
        self.current_z_label =tk.Label(self.LocationFrame, textvariable=self.current_z,justify=tk.LEFT,bg="black",fg="green")
        self.x_now = tk.Label(self.LocationFrame, text="current x",justify=tk.LEFT,bg="black",fg="green")
        self.y_now = tk.Label(self.LocationFrame, text="current y",justify=tk.LEFT,bg="black",fg="green")
        self.z_now = tk.Label(self.LocationFrame, text="current z",justify=tk.LEFT,bg="black",fg="green")
        self.x_now.grid(row=0,column=0)
        self.y_now.grid(row=0,column=1)
        self.z_now.grid(row=0,column=2)
        self.current_x_label.grid(row=1,column=0)
        self.current_y_label.grid(row=1,column=1)
        self.current_z_label.grid(row=1,column=2)

        # Column Labels
        self.pointsGrid = tk.Frame(self,bg="gray")
        self.pointsGrid.pack(side="top")
        tk.Label(self.pointsGrid, text="", justify=tk.LEFT,bg="gray").grid(row=0,column=0)
        tk.Label(self.pointsGrid, text="X", justify=tk.LEFT,bg="gray").grid(row=0,column=1)
        tk.Label(self.pointsGrid, text="Y", justify=tk.LEFT,bg="gray").grid(row=0,column=2)
        tk.Label(self.pointsGrid, text="Z", justify=tk.LEFT,bg="gray").grid(row=0,column=3)
        tk.Label(self.pointsGrid, text="", justify=tk.LEFT,bg="gray").grid(row=0,column=4)

        # Back Right Calibration Row
        self.x_1 = tk.DoubleVar(self, 0.0)
        self.y_1 = tk.DoubleVar(self, 0.0)
        self.z_1 = tk.DoubleVar(self, 0.0)
        self.set_br =  tk.Button(self.pointsGrid, text="Save Back Right", bg="gray", command=lambda: self.set_cal_point("Back Right"))
        self.x_1_lab = tk.Label(self.pointsGrid, textvariable=self.x_1, bg="gray")
        self.y_1_lab = tk.Label(self.pointsGrid, textvariable=self.y_1, bg="gray")
        self.z_1_lab = tk.Label(self.pointsGrid, textvariable=self.z_1, bg="gray")
        self.move_br = tk.Button(self.pointsGrid, text="Move to Back Right", bg="gray", command=lambda: self.move_to_point("Back Right"))
        self.set_br.grid(row=1,column=0)
        self.x_1_lab.grid(row=1,column=1)
        self.y_1_lab.grid(row=1,column=2)
        self.z_1_lab.grid(row=1,column=3)
        self.move_br.grid(row=1,column=4)

        # Back Left Calibration Row
        self.x_2 = tk.DoubleVar(self, 0.0)
        self.y_2 = tk.DoubleVar(self, 0.0)
        self.z_2 = tk.DoubleVar(self, 0.0)
        self.set_bl =  tk.Button(self.pointsGrid, text="Save Back Left", bg="gray", command=lambda: self.set_cal_point("Back Left"))
        self.x_2_lab = tk.Label(self.pointsGrid, textvariable=self.x_2, bg="gray")
        self.y_2_lab = tk.Label(self.pointsGrid, textvariable=self.y_2, bg="gray")
        self.z_2_lab = tk.Label(self.pointsGrid, textvariable=self.z_2, bg="gray")
        self.move_bl = tk.Button(self.pointsGrid, text="Move to Back Left", bg="gray", command=lambda: self.move_to_point("Back Left"))
        self.set_bl.grid(row=2,column=0)
        self.x_2_lab.grid(row=2,column=1)
        self.y_2_lab.grid(row=2,column=2)
        self.z_2_lab.grid(row=2,column=3)
        self.move_bl.grid(row=2,column=4)

        # Front Left Calibration Row
        self.x_3 = tk.DoubleVar(self, 0.0)
        self.y_3 = tk.DoubleVar(self, 0.0)
        self.z_3 = tk.DoubleVar(self, 0.0)
        self.set_fl =  tk.Button(self.pointsGrid, text="Save Front Left", bg="gray", command=lambda: self.set_cal_point("Front Left"))
        self.x_3_lab = tk.Label(self.pointsGrid, textvariable=self.x_3, bg="gray")
        self.y_3_lab = tk.Label(self.pointsGrid, textvariable=self.y_3, bg="gray")
        self.z_3_lab = tk.Label(self.pointsGrid, textvariable=self.z_3, bg="gray")
        self.move_fl = tk.Button(self.pointsGrid, text="Move to Front Left", bg="gray", command=lambda: self.move_to_point("Front Left"))
        self.set_fl.grid(row=3,column=0)
        self.x_3_lab.grid(row=3,column=1)
        self.y_3_lab.grid(row=3,column=2)
        self.z_3_lab.grid(row=3,column=3)
        self.move_fl.grid(row=3,column=4)

        # 4th point row - 4th point is determined by other three points
        self.x_4 = tk.DoubleVar(self, 0.000)
        self.y_4 = tk.DoubleVar(self, 0.000)
        self.z_4 = tk.DoubleVar(self, 0.000)
        self.fr_lab = tk.Label(self.pointsGrid, text="Front Right", justify=tk.LEFT)
        self.x_4_label = tk.Label(self.pointsGrid, textvariable=self.x_4, bg="gray")
        self.y_4_label = tk.Label(self.pointsGrid, textvariable=self.y_4, bg="gray")
        self.z_4_label = tk.Label(self.pointsGrid, textvariable=self.z_4, bg="gray")
        self.test_button = tk.Button(self.pointsGrid, text="Test Calibration", bg="red2", state="disabled", command=lambda: self.test_calibration())
        self.fr_lab.grid(row=4,column=0)
        self.x_4_label.grid(row=4,column=1)
        self.y_4_label.grid(row=4,column=2)
        self.z_4_label.grid(row=4,column=3)
        self.test_button.grid(row=4,column=4)

        # this button triggers the creation of a labware object using the gathered locations, starts disabled
        self.save_button = tk.Button(self,text="Save Labware",command=lambda: self.add_plate_to_labware(), justify=tk.LEFT)
        self.save_button.pack(side=tk.TOP)
        self.save_button["state"] = "disabled"

        # modifies the close button protocol
        self.protocol('WM_DELETE_WINDOW', self.on_closing)    

    def set_cal_point(self, cal_point):
        x,y,z = self.coordinator.myModules.myStages[self.selected_stage].get_motor_coordinates()

        if cal_point == "Back Right":
            self.calibrator.back_right_point = (x,y,z)
            self.x_1.set(x)
            self.y_1.set(y)
            self.z_1.set(z)
        elif cal_point == "Back Left":
            self.calibrator.back_left_point = (x,y,z)
            self.x_2.set(x)
            self.y_2.set(y)
            self.z_2.set(z)
        elif cal_point == "Front Left":
            self.calibrator.front_left_point = (x,y,z)
            self.x_3.set(x)
            self.y_3.set(y)
            self.z_3.set(z)
        
        self.calibrator.tested = False
        self.update_states()    
        
    def move_to_point(self, cal_point):
        if cal_point == "Back Right":
            coordinates = (self.x_1.get(), self.y_1.get(), self.z_1.get())
        elif cal_point == "Back Left":
            coordinates = (self.x_2.get(), self.y_2.get(), self.z_2.get())
        elif cal_point == "Front Left":
            coordinates = (self.x_3.get(), self.y_3.get(), self.z_3.get())
        elif cal_point == "Front Right":
            coordinates = (self.x_4.get(), self.y_4.get(), self.z_4.get())
        self.coordinator.myModules.myStages[self.selected_stage].move_to(coordinates)

    def test_calibration(self):
        self.move_to_point("Front Right")
        self.calibrator.tested = True
        self.update_states()    

    def compile_plate_properties(self) ->  dict:
        stage_type = self.coordinator.myModules.myStages[self.selected_stage].stage_type
        self.calibrator.map_out_wells(stage_type, self.model_parameters)
        nicknames = self.model_parameters["nicknames"]
        self.calibrator.compile_nicknames(nicknames)
        plate_properties = {}
        plate_properties["model"] = self.model_name # Load model name
        plate_properties["grid"] = self.model_parameters["grid"] # Load grid
        plate_properties["well_locations"] = self.calibrator.well_locations # Load well_locations
        plate_properties["well_depth"] = self.model_parameters["well_depth"] # Load well_types
        plate_properties["nicknames"] = self.calibrator.well_nicknames # Load well_nicknames
        
        return plate_properties 

    def add_plate_to_labware(self):
        parameters = self.compile_plate_properties()
        self.coordinator.myModules.myStages[self.selected_stage].myLabware.create_new_plate(parameters)
        self.on_closing()

    # this is run inside a thread to keep the position labels and calibration states updated
    def update_positions(self):
        self.updating_positions = True
        
        while self.updating_positions:
            x,y,z = self.coordinator.myModules.myStages[self.selected_stage].get_motor_coordinates()
            self.current_x.set(x)
            self.current_y.set(y)
            self.current_z.set(z)
            time.sleep(1)

    def update_states(self):
        # if all calibration points have been saved, it uses them to calculate the fourth calibration point, and enables the test_button
        if (self.calibrator.back_left_point != (0,0,0)) and (self.calibrator.front_left_point != (0,0,0)) and (self.calibrator.back_right_point != (0,0,0)):
            self.calibrator.guess_fourth_calibration_point()
            self.test_button["state"] = "normal"
            self.test_button.configure(bg = "forest green")
            self.x_4.set(self.calibrator.fourth_point[0])
            self.y_4.set(self.calibrator.fourth_point[1])
            self.z_4.set(self.calibrator.fourth_point[2])

        # only allow saving labware after testing calibration ponts 
        if self.calibrator.tested == True:
            self.save_button["state"] = "normal"
        else:
            self.save_button["state"] = "disabled"

    # sets flag to false, then waits until position_thread has ended to proceed
    def stop_updating_positions(self):
        self.updating_positions = False
        
    
    def start_joystick(self):
        self.position_thread = threading.Thread(target=self.update_positions)
        self.position_thread.start()
        self.coordinator.start_joystick(self.selected_stage)
        self.killButton["state"] = "normal"
        self.joyButton["state"] = "disabled"

    def kill_joystick(self):
        self.coordinator.stop_joystick()
        self.stop_updating_positions()
        self.killButton["state"] = "disabled"
        self.joyButton["state"] = "normal"

    def on_closing(self):
        self.kill_joystick()
        self.destroy()

