from gui.Syringe_Calibration import Syringe_Calibration

import tkinter as tk
from tkinter import ttk


class Syringe_Selection(tk.Toplevel,):
    def __init__(self, coordinator, selectedStage):
        tk.Toplevel.__init__(self) 
        self.selectedStage = selectedStage 
        self.coordinator = coordinator
      
        self.title("Syringe Selection")
        self.settingsFileLabel = tk.Label(self, text="Select Syringe Type: ",justify=tk.LEFT)
        self.settingsFileLabel.pack(side=tk.TOP)
        self.geometry("750x750")

        self.syringe_calibration_page = None

        self.syringe_models = coordinator.myModules.myStages[self.selectedStage].myModelsManager.get_stored_models()["syringes"]

        self.syringe_model = tk.StringVar()
        self.syringe_model_selection = ttk.Combobox(self, state='readonly', textvariable=self.syringe_model, values=self.syringe_models)
        self.syringe_model_selection.pack(side=tk.TOP)
        self.syringe_model_selection.bind("<<ComboboxSelected>>", lambda x: self.enable_calibration())

        self.calibrate_button = tk.Button(self, text="Calibrate",command=self.open_syringe_calibration_page, state="disabled")
        self.calibrate_button.pack(side=tk.TOP)
        

    def enable_calibration(self):
        if self.syringe_model != "":
            self.calibrate_button["state"] =  "normal"

    def open_syringe_calibration_page(self):
        if not self.syringe_calibration_page or not self.syringe_calibration_page.winfo_exists():
            self.syringe_calibration_page = Syringe_Calibration(self.coordinator, self.selectedStage, self.syringe_model.get())
        else:
            self.syringe_calibration_page.deiconify()
        