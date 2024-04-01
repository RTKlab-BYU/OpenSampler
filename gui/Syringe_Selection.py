from gui.Syringe_Calibration import Syringe_Calibration

import tkinter as tk
from tkinter import ttk


class Syringe_Selection(tk.Toplevel,):
    def __init__(self, coordinator, selectedStage):
        tk.Toplevel.__init__(self) 
        self.selectedStage = selectedStage 
      
        self.title("Select Syringe Type")
        self.settingsFileLabel = tk.Label(self, text="Select Syringe Type: ",justify=tk.LEFT)
        self.settingsFileLabel.pack(side=tk.TOP)
        self.geometry("750x750")
        self.selectedModel = ttk.Combobox(self, state='readonly')
        self.selectedModel.pack(side=tk.TOP)
        self.selectedModel["values"] = []
        self.loadButton = tk.Button(self, text="Calibrate",command=lambda: self.OpenWindow(coordinator),justify=tk.LEFT)
        self.loadButton.pack(side=tk.TOP)
        self.loadButton["state"] =  "disable"
        self.selectedModel.bind("<FocusIn>", lambda x: self.EnableSubmit())
        self.TypeVar = "syringe"
        self.selectedModel.set("")
        self.selectedModel["values"] = coordinator.myModules.myStages[self.selectedStage].myModelsManager.get_stored_models()["syringes"]

    def EnableSubmit(self):
        self.loadButton["state"] =  "normal"

    def OpenWindow(self,coordinator):
        Syringe_Calibration(coordinator, self.selectedStage, self.selectedModel.get())