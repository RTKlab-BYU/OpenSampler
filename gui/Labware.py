from gui.Labware_Selection import Labware_Selection
from gui.Syringe_Selection import Syringe_Selection
from gui.Create_Labware import Create_Labware

import tkinter as tk
from tkinter import ttk, filedialog

class WellPlate_Row(tk.Frame,):
    def __init__(self, frame, coordinator, stage, labware_name, row):
        super().__init__(frame)
        self.row = row
        tk.Label(frame.wellplateBox, text=labware_name).grid(row=self.row,column=1)
        tk.Button(frame.wellplateBox, text="Delete", command=lambda: self.DeleteRow(frame, coordinator, stage)).grid(row=self.row, column=0)

    def DeleteRow(self, frame, coordinator, stage):
        coordinator.myModules.myStages[stage].myLabware.plate_list.pop(self.row - 1)
        frame.UpdateLabware(coordinator)



class Nickname_Row(tk.Frame,):
    def __init__(self, frame, coordinator, stage, nickname_name, row):
        super().__init__(frame)
        self.row = row
        tk.Label(frame.nicknameBox, text=nickname_name).grid(row=self.row,column=1)
        x, y, z = coordinator.myModules.myStages[stage].myLabware.custom_locations[nickname_name]
        location_string = f"{x}, {y}, {z}"
        tk.Label(frame.nicknameBox, text=location_string).grid(row=self.row,column=2)
        tk.Button(frame.nicknameBox, text="Delete", command=lambda: self.DeleteRow(frame, coordinator, stage, nickname_name)).grid(row=self.row, column=0)

    def DeleteRow(self, frame, coordinator, stage, nickname_name):
        coordinator.myModules.myStages[stage].myLabware.custom_locations.pop(nickname_name) 
        frame.UpdateLabware(coordinator)

class Syringe_Row(tk.Frame,):
    def __init__(self, frame, coordinator, stage, nickname_name, row):
        super().__init__(frame)
        self.row = row
        tk.Label(frame.syringeBox, text=nickname_name).grid(row=self.row,column=1)
        tk.Button(frame.syringeBox, text="Reset", command=lambda: self.ResetSyringe(frame, coordinator, stage)).grid(row=self.row, column=0)

    def ResetSyringe(self, frame, coordinator, stage):
        coordinator.myModules.myStages[stage].myLabware.reset_syringe_settings()
        
        frame.UpdateLabware(coordinator)


class Labware(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Labware Setup")
        self.geometry("750x750")

        self.coordinator = coordinator
        
        # Options Bar
        self.optionsBar = tk.Frame(self)
        self.optionsBar.pack(side=tk.TOP)

        self.labware_selection_page = None
        self.create_labware_page = None
        self.syringe_selection_page = None


        self.addButton = tk.Button(self.optionsBar, text="Add Labware", command=self.open_labware_selection_page, state="disabled")
        self.saveButton = tk.Button(self.optionsBar, text="Save Labware", command=lambda: self.SaveLabware(coordinator), state="disabled")
        self.loadButton = tk.Button(self.optionsBar, text="Load Labware", command=lambda: self.LoadLabware(coordinator), state="disabled")
        self.createButton = tk.Button(self.optionsBar, text="Create New Model", command=self.open_create_labware_page)

        self.addButton.grid(row=0,column=0)
        self.saveButton.grid(row=0,column=1)
        self.loadButton.grid(row=0,column=2)
        self.createButton.grid(row=0,column=3)
        
        # stage selection
        self.loaded_stage_bar = tk.Frame(self)
        self.loaded_stage_bar.pack(side=tk.TOP)
        self.settingsFileLabel = tk.Label(self.loaded_stage_bar, text="Select Stage: ",justify=tk.LEFT)
        self.settingsFileLabel.grid(row=0,column=0)

        self.wellplateBox = tk.Frame(self)
        self.wellplateBox.pack(side=tk.TOP)
        tk.Label(self.wellplateBox,font="Helvetica 20", text="Loaded Wellplates").grid(row = 0, column = 1)

        self.nicknameBox = tk.Frame(self)
        self.nicknameBox.pack(side=tk.TOP)
        tk.Label(self.nicknameBox,font="Helvetica 24",text="Custom Locations").grid(row = 0, column = 1)

        self.syringeBox = tk.Frame(self)
        self.syringeBox.pack(side=tk.TOP)
        tk.Label(self.syringeBox,font="Helvetica 24",text="Syringe").grid(row = 0, column = 1)

        self.wellplate_list = []
        self.nickname_list = []
        self.syringe_list = []

        stageOptions = list(coordinator.myModules.myStages.keys())
        stageOptions.insert(0,"")
        self.selected_stage = tk.StringVar(value="")
        self.loadedMotorSeries = ttk.Combobox(self.loaded_stage_bar, values=stageOptions, textvariable=self.selected_stage, state='readonly')
        self.loadedMotorSeries.grid(row=0,column=1)
        if "Left_OT" in stageOptions:
            self.loadedMotorSeries.current(stageOptions.index("Left_OT"))
        else:
            self.loadedMotorSeries.current(0)
        self.loadedMotorSeries.bind("<<ComboboxSelected>>", lambda x: self.UpdateSelectedMotors(self.coordinator))
        self.UpdateSelectedMotors(self.coordinator)


    def open_labware_selection_page(self):
        if not self.labware_selection_page or not self.labware_selection_page.winfo_exists():
            self.labware_selection_page = Labware_Selection(self.coordinator, self.selected_stage.get())
        else:
            self.labware_selection_page.deiconify()

    def open_create_labware_page(self):
        if not self.create_labware_page or not self.create_labware_page.winfo_exists():
            self.create_labware_page = Create_Labware()
        else:
            self.create_labware_page.deiconify()

    def open_syringe_selection_page(self):
        if not self.syringe_selection_page or not self.syringe_selection_page.winfo_exists():
            self.syringe_selection_page = Syringe_Selection(self.coordinator, self.selected_stage.get())
            self.syringe_selection_page.deiconify()

    def LoadLabware(self, coordinator):
        filetypes = (
            ('json files', '*.json'),
            ('All files', '*')
        )

        file_path = filedialog.askopenfilename(parent=self, title='Open a file', initialdir='Calibrations', filetypes=filetypes)

        if file_path == "":  # in the event of a cancel 
            return
        
        coordinator.load_labware_setup(file_path, self.selected_stage.get())

        self.UpdateLabware(coordinator)

    def UpdateSelectedMotors(self, coordinator):

        if not self.selected_stage.get() == "":
            self.stage_type = coordinator.myModules.myStages[self.selected_stage.get()].stage_type
        else:
            self.stage_type = "None" 
        if self.stage_type == "Zaber_XYZ" or self.stage_type == "Opentrons":
            self.stage_type = "XYZ_Stage"
        
        if self.stage_type == "XYZ_Stage":
            self.addButton.config(text="Add Labware", command=self.open_labware_selection_page)
            self.addButton["state"] = "normal"
            self.saveButton["state"] =  "normal"
            self.loadButton["state"] =  "normal"
        elif self.stage_type == "Zaber_Syringe_Only":
            self.addButton.config(text="Calibrate Syringe", command=self.open_syringe_selection_page)
            self.addButton["state"] = "normal"
            self.saveButton["state"] =  "disable"
            self.loadButton["state"] =  "disable"

        self.UpdateLabware(coordinator)

    def SaveLabware(self, coordinator):
        self.UpdateSelectedMotors(coordinator)
        filetypes = (
            ('json files', '*.json'),
            ( 'All files', '*')
        )

        new_file = filedialog.asksaveasfile(parent=self, title='Save a file', initialdir='Calibrations', filetypes=filetypes)
        
        if new_file == None:  # in the event of a cancel 
            return
        
        if new_file.name.endswith(".json"):
            new_file = new_file.name.replace(".json","") + ".json"
        else:
            new_file = new_file.name + ".json"
        
        if (len(coordinator.myModules.myStages[self.selected_stage.get()].myLabware.plate_list)+len(coordinator.myModules.myStages[self.selected_stage.get()].myLabware.custom_locations)>0):
            
            coordinator.save_labware_setup(self.selected_stage.get(), new_file)
            
    def UpdateLabware(self, coordinator):
        for wellplate in self.wellplate_list:
            wellplate.destroy()
        self.wellplate_list = []
        for nickname in self.nickname_list:
            nickname.destroy()
        self.nickname_list = []
        for syringe in self.syringe_list:
            syringe.destroy()
        self.syringe_list = []

        self.PopulateLabware(coordinator)

    def PopulateLabware(self, coordinator):
        if self.stage_type == "XYZ_Stage":
            
            row = 1 # row 0 is the label
            for eachWellplate in coordinator.myModules.myStages[self.selected_stage.get()].myLabware.plate_list:
                self.wellplate_list.append(WellPlate_Row(self, coordinator, self.selected_stage.get(), eachWellplate.model, row))
                row += 1

            row = 1 # row 0 is the label
            for eachLocation in coordinator.myModules.myStages[self.selected_stage.get()].myLabware.custom_locations.keys():
                self.nickname_list.append(Nickname_Row(self, coordinator, self.selected_stage.get(), eachLocation, row))
                row += 1
                
            my_syringe = coordinator.myModules.myStages[self.selected_stage.get()].myLabware.syringe_model
            self.syringe_list = [Syringe_Row(self, coordinator, self.selected_stage.get(), my_syringe, row=1)]


        elif self.stage_type == "Zaber_Syringe_Only":
            my_syringe = coordinator.myModules.myStages[self.selected_stage.get()].myLabware.syringe_model
            self.syringe_list = [Syringe_Row(self, coordinator, self.selected_stage.get(), my_syringe, row=1)]

       
        

