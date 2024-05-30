from gui.Calibration import Calibration
from gui.Custom_Location_Page import Custom_Location
from gui.Syringe_Calibration import Syringe_Calibration

import tkinter as tk
from tkinter import ttk


class Labware_Selection(tk.Toplevel,):
    def __init__(self, coordinator, selected_stage):
        tk.Toplevel.__init__(self) 
        self.selected_stage = selected_stage
        self.coordinator = coordinator 
      
        self.title("Add Labware Type")
        self.type_select_label = tk.Label(self, text="Select Labware Type: ")
        self.type_select_label.pack(side=tk.TOP)
        self.geometry("750x750")

        self.wellplate_calibration_page = None
        self.custom_location_page = None
        self.syringe_calibration_page = None

        self.type_bar = tk.Frame(self)
        self.type_bar.pack(side=tk.TOP)

        self.option_selected = tk.StringVar(self.type_bar)
        self.option_selected.set(0)
        self.option_selected.trace("w", lambda x,y,z: self.update_options())
        
        self.selected_model = ttk.Combobox(self, state='readonly')
        self.selected_model.pack(side=tk.TOP)
        self.selected_model["values"] = []

        self.start_calibration = tk.Button(self, text="Calibrate", command= self.open_sub_window,justify=tk.LEFT)
        self.start_calibration.pack(side=tk.TOP)
        self.start_calibration["state"] =  "disable"
        self.selected_model.bind("<<ComboboxSelected>>", lambda x: self.enable_submit()) 

        tk.Radiobutton(self.type_bar, text="Wellplate", padx = 20, variable=self.option_selected, value="wellplate", command=self.update_options).grid(row=0,column=0)
        tk.Radiobutton(self.type_bar, text="Custom", padx = 20, variable=self.option_selected, value="custom", command=self.update_options).grid(row=0,column=1)
        tk.Radiobutton(self.type_bar, text="Syringe", padx = 20, variable=self.option_selected, value="syringe", command=self.update_options).grid(row=0,column=2)

    def open_wellplate_calibration_page(self):
        if not self.wellplate_calibration_page or not self.wellplate_calibration_page.winfo_exists():
            self.wellplate_calibration_page = Calibration(self.coordinator, self.selected_stage, model_name=self.selected_model.get())
        else:
            self.syringe_calibration_page.deiconify()

    def open_custom_location_page(self):
        if not self.custom_location_page or not self.custom_location_page.winfo_exists():
            self.custom_location_page = Custom_Location(self.coordinator, self.selected_stage)
        else:
            self.syringe_calibration_page.deiconify()

    def open_syringe_calibration_page(self):
        if not self.syringe_calibration_page or not self.syringe_calibration_page.winfo_exists():
            self.syringe_calibration_page = Syringe_Calibration(self.coordinator, self.selected_stage, self.selected_model.get())
        else:
            self.syringe_calibration_page.deiconify()
        
    def update_options(self):
        
        if self.option_selected.get() == "wellplate":
            self.selected_model.set("")
            self.disable_submit()
            self.selected_model["values"] = self.coordinator.myModules.myStages[self.selected_stage].myModelsManager.get_stored_models()["plates"]
        
        elif self.option_selected.get() == "custom":
            self.selected_model.set("")
            self.enable_submit()
            self.selected_model["values"] = []
        
        elif self.option_selected.get() == "syringe":
            self.selected_model.set("HAMILTON_1701")
            self.disable_submit()
            self.selected_model["values"] = self.coordinator.myModules.myStages[self.selected_stage].myModelsManager.get_stored_models()["syringes"]
        else:
            print("Error, invalid labware type: " + str(self.option_selected.get()))
        print(self.option_selected.get())

    def enable_submit(self):
        self.start_calibration["state"] = "normal"

    def disable_submit(self):
        self.start_calibration["state"] = "disable"

    def open_sub_window(self):
        if self.option_selected.get() == "wellplate":
            self.open_wellplate_calibration_page()
        elif self.option_selected.get() == "custom":
            self.open_custom_location_page()
        elif self.option_selected.get() == "syringe":
            self.open_syringe_calibration_page()