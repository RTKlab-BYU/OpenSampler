from gui.Labware_Selection import Labware_Selection
from gui.Syringe_Selection import Syringe_Selection
from gui.Create_Labware import Create_Labware

import tkinter as tk
from tkinter import ttk

class WellPlate_Row(tk.Frame,):
    def __init__(self, frame, coordinator, stage, labware_name, row):
        self.row= row
        tk.Label(frame.wellplateBox, text=labware_name).grid(row=self.row,column=1)
        tk.Button(frame.wellplateBox, text="Delete", command=lambda: self.DeleteRow(frame, coordinator, stage)).grid(row=self.row, column=0)

    def DeleteRow(self, frame, coordinator, stage):
        coordinator.myModules.myStages[stage].myLabware.plate_list.pop(self.row - 1)
        frame.UpdateLabware(coordinator)



class Nickname_Row(tk.Frame,):
    def __init__(self, frame, coordinator, stage, nickname_name, row):
        self.row= row
        tk.Label(frame.nicknameBox, text=nickname_name).grid(row=self.row,column=1)
        print('\n',coordinator.myModules.myStages[stage].myLabware.custom_locations[nickname_name],'\n')
        x, y, z = coordinator.myModules.myStages[stage].myLabware.custom_locations[nickname_name]
        location_string = f"{x}, {y}, {z}"
        tk.Label(frame.nicknameBox, text=location_string).grid(row=self.row,column=2)
        tk.Button(frame.nicknameBox, text="Delete", command=lambda: self.DeleteRow(frame, coordinator, stage, nickname_name)).grid(row=self.row, column=0)

    def DeleteRow(self, frame, coordinator, stage, nickname_name):
        coordinator.myModules.myStages[stage].myLabware.custom_locations.pop(nickname_name) # does this work on a dictionary?
        frame.UpdateLabware(coordinator)

class Syringe_Row(tk.Frame,):
    def __init__(self, frame, coordinator, stage, nickname_name, row):
        self.row= row
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
        
        # Options Bar
        self.optionsBar = tk.Frame(self)
        self.optionsBar.pack(side=tk.TOP)
        self.addButton = tk.Button(self.optionsBar, text="Add Labware",command=lambda: Labware_Selection(coordinator,self.selected_stage),justify=tk.LEFT)#
        self.addButton.grid(row=0,column=0)
        self.addButton["state"] =  "disable"
        self.saveButton = tk.Button(self.optionsBar, text="Save Labware",command=lambda: self.SaveLabware(coordinator),justify=tk.LEFT)
        self.saveButton.grid(row=0,column=2)
        self.saveButton["state"] =  "disable"
        self.loadButton = tk.Button(self.optionsBar, text="Load Labware",command=lambda: self.LoadLabware(coordinator),justify=tk.LEFT)
        self.loadButton.grid(row=0,column=3)
        self.loadButton["state"] =  "disable"
        self.createButton = tk.Button(self.optionsBar, text="Create New Model",command=Create_Labware,justify=tk.LEFT)
        self.createButton.grid(row=0,column=4)
        
        # stage selection
        stageOptions = list(coordinator.myModules.myStages.keys())
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

        self.cow = []
    

        if(len(stageOptions)>0):
            self.loadedMotorSeries = ttk.Combobox(self.loaded_stage_bar, state='readonly')
            self.loadedMotorSeries.grid(row=0,column=1)
            self.loadedMotorSeries["values"] = stageOptions
            if "Left_OT" in stageOptions:
                self.loadedMotorSeries.current(stageOptions.index("Left_OT"))
            else:
                self.loadedMotorSeries.current(0)
            self.loadedMotorSeries.bind("<<ComboboxSelected>>", lambda x: self.UpdateSelectedMotors(coordinator))


    def LoadLabware(self, coordinator):
        filetypes = (
            ('json files', '*.json'),
            ('All files', '*')
        )

        new_file =tk.filedialog.askopenfilename(
            title='Open a file',
            initialdir='Calibrations',
            filetypes=filetypes)
        
        coordinator.load_labware_setup(new_file,self.selected_stage)

        self.UpdateLabware(coordinator)
        
        

    def UpdateSelectedMotors(self, coordinator):
        self.selected_stage = self.loadedMotorSeries.get()
        stage_type = coordinator.myModules.myStages[self.selected_stage].stage_type 
        if stage_type == "Zaber_XYZ" or stage_type == "Opentrons":
            self.stage_type = "XYZ_Stage"
        elif stage_type == "Zaber_Syringe_Only":
            self.stage_type = "Zaber_Syringe_Only"
        else:
            self.stage_type = "None"

        self.addButton["state"] = "normal"
        if self.stage_type == "XYZ_Stage":
            self.saveButton["state"] =  "normal"
            self.loadButton["state"] =  "normal"
        elif self.stage_type == "Zaber_Syringe_Only":
            self.saveButton["state"] =  "disable"
            self.loadButton["state"] =  "disable"

        self.UpdateLabware(coordinator)


    def SaveLabware(self, coordinator):
        self.UpdateSelectedMotors(coordinator)
        filetypes = (
            ('json files', '*.json'),
            ( 'All files', '*')
        )

        new_file =tk.filedialog.asksaveasfile(
            title='Save a file',
            initialdir='Calibrations',
            filetypes=filetypes)
        
        if new_file.name.endswith(".json"):
            new_file = new_file.name.replace(".json","") + ".json"
        else:
            new_file = new_file.name + ".json"
        
        
        if (len(coordinator.myModules.myStages[self.selected_stage].myLabware.plate_list)+len(coordinator.myModules.myStages[self.selected_stage].myLabware.custom_locations)>0):
            
            coordinator.save_labware_setup(self.selected_stage, new_file)
            
    def UpdateLabware(self, coordinator):
        self.wellplateBox.destroy()

        self.addButton.destroy()

        self.nicknameBox.destroy()
        self.cow = []

        self.syringeBox.destroy()

        self.PopulateLabware(coordinator)

    def PopulateLabware(self, coordinator):
        if self.stage_type == "XYZ_Stage":
            self.wellplateBox = tk.Frame(self)
            self.wellplateBox.pack(side=tk.TOP)
            tk.Label(self.wellplateBox,font="Helvetica 20", text="Loaded Wellplates").grid(row = 0, column = 1)
            
            self.addButton = tk.Button(self.optionsBar, text="Add Labware",command=lambda: Labware_Selection(coordinator,self.selected_stage),justify=tk.LEFT)#
            self.addButton.grid(row=0,column=0)
            self.nicknameBox = tk.Frame(self)
            self.nicknameBox.pack(side=tk.TOP)

            tk.Label(self.nicknameBox,font="Helvetica 24",text="Custom Locations").grid(row = 0, column = 1)
            i = 1 #0 is the label
            for eachWellplate in coordinator.myModules.myStages[self.selected_stage].myLabware.plate_list:
                self.cow.append(WellPlate_Row(self, coordinator, self.selected_stage, eachWellplate.model, i))
                i = i + 1
            

            mySyringe = coordinator.myModules.myStages[self.selected_stage].myLabware.syringe_model
            i = 1
            for eachLocation in coordinator.myModules.myStages[self.selected_stage].myLabware.custom_locations.keys():
                self.cow.append(Nickname_Row(self, coordinator, self.selected_stage, eachLocation, i))
                i = i + 1
        elif self.stage_type == "Zaber_Syringe_Only":
            self.addButton = tk.Button(self.optionsBar, text="Calibrate Syringe",command=lambda: Syringe_Selection(coordinator,self.selected_stage),justify=tk.LEFT)#
            self.addButton.grid(row=0,column=0)
            mySyringe = coordinator.myModules.myStages[self.selected_stage].myLabware.syringe_model
        else:
            print(self.stage_type)
            
        
        self.syringeBox = tk.Frame(self)
        self.syringeBox.pack(side=tk.TOP)
        tk.Label(self.syringeBox,font="Helvetica 24",text="Syringe").grid(row = 0, column = 1)
       
        self.cow.append(Syringe_Row(self, coordinator, self.selected_stage, mySyringe, row=1))
        

