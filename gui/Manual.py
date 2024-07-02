import tkinter as tk
from tkinter import ttk
import threading

class Manual(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Manual Movement")
        self.geometry("500x500")

        self.coordinator = coordinator
        self.thread = threading.Thread(target=self.do_nothing,args=(30,))
            
        self.joyBar = tk.Frame(self)
        self.joyBar.pack(side=tk.TOP)

        stageOptions = coordinator.myModules.myStages.keys()
        self.loaded_labware_bar = tk.Frame(self)
        self.loaded_labware_bar.pack(side=tk.TOP)
        self.settingsFileLabel = tk.Label(self.loaded_labware_bar, text="Select Stage: ",justify=tk.LEFT)
        self.settingsFileLabel.grid(row=0,column=0)
        if(len(stageOptions)>0):
            self.loadedMotorSeries = ttk.Combobox(self.loaded_labware_bar, state='readonly')
            self.loadedMotorSeries.grid(row=0,column=1)
            self.loadedMotorSeries["values"] = [*stageOptions]
            self.loadedMotorSeries.bind("<<ComboboxSelected>>", lambda x: self.UpdateSelectedMotors(coordinator))
        
        # self.joystick = ttk.Combobox(self.joyBar, state='readonly')
        # self.joystick.grid(row=0,column=0)
        # self.joystick["values"] = [*coordinator.myModules.myJoystickProfiles.keys()]
        self.joyButton = tk.Button(self.joyBar,text="Start Joystick",command=lambda: self.StartJoystick(coordinator),justify=tk.LEFT)
        self.joyButton.grid(row=0,column=1)
        self.joyButton["state"] = "disabled"
        self.killButton = tk.Button(self.joyBar,text="Kill Joystick",command=lambda: self.KillJoystick(coordinator),justify=tk.LEFT)
        self.killButton.grid(row=0,column=2)
        self.killButton["state"] = "disabled"
        self.selected_labware_type = tk.StringVar(self,None)
        self.selected_labware = tk.StringVar(self,None)
        self.past_type = None
        self.past_motor = None
        self.past_labware = None

        self.protocol('WM_DELETE_WINDOW', self.on_closing)

    def on_closing(self):
        if self.thread.is_alive():
            self.KillJoystick(self.coordinator)
        self.destroy()

    def do_nothing(self, *args):
        pass
        #do nothing

    def StartJoystick(self, coordinator):
        self.selected_stage = self.loadedMotorSeries.get()
        # self.selected_joystick = self.joystick.get()
        self.thread = threading.Thread(target=coordinator.start_joystick,args=(self.selected_stage,))
        self.thread.start()
        self.killButton["state"] = "normal"
        self.joyButton["state"] = "disabled"

    def KillJoystick(self, coordinator):
        coordinator.stop_joystick()
        self.killButton["state"] = "disabled"
        self.joyButton["state"] = "normal"

    def UpdateSelectedMotors(self, coordinator):
        self.selected_stage = self.loadedMotorSeries.get()
        self.joyButton["state"] = "normal"
        tk.Label(self.loaded_labware_bar, text="Select Type: ",justify=tk.LEFT).grid(row=1,column=0)
        self.selected_labware_type = tk.StringVar(self)
        if self.past_motor != None:
            self.selected_labware_type_box.destroy()
        self.selected_labware_type_box = ttk.Combobox(self.loaded_labware_bar, state='readonly')
        self.selected_labware_type_box.grid(row=1,column=1)
        if "Syringe_Only" not in coordinator.myModules.myStages[self.selected_stage].stage_type:
            self.selected_labware_type_box["values"] = ["Wellplate","Named Location"]
        elif "Syringe_Only" in coordinator.myModules.myStages[self.selected_stage].stage_type:
            self.selected_labware_type_box["values"] = []
        self.selected_labware_type_box.bind("<<ComboboxSelected>>", lambda x: self.UpdateSelectedType(coordinator))

        if self.past_type != None:
            self.selected_labware = tk.StringVar(self,None)
            self.selected_labware_box.destroy()
            self.selected_labware_label.destroy()
            if self.past_type == "Wellplate":
                self.wellName.destroy()
                if self.past_labware != None:
                    self.moveButton.destroy()
                    self.wellLabel.destroy()

        self.past_type = None
        self.past_motor = self.selected_stage
        self.past_labware = None

    def UpdateSelectedType(self, coordinator):
        self.selected_labware_type = self.selected_labware_type_box.get()
        
        self.loaded_labware = []
        if self.past_type != None:
            self.selected_labware = tk.StringVar(self,None)
            self.selected_labware_box.destroy()
            self.selected_labware_label.destroy()
            if self.past_type == "Wellplate":
                if self.past_labware != None:
                    self.moveButton.destroy()
                    self.wellLabel.destroy()
                    self.wellName.destroy()
                
        self.past_type = self.selected_labware_type
        self.past_labware = None

        self.PopulateLabware(coordinator)

    def PopulateLabware(self, coordinator):
        match self.selected_labware_type:
            case "Wellplate":
                i = 0
                for eachWellplate in coordinator.myModules.myStages[self.selected_stage].myLabware.plate_list:
                    self.loaded_labware.append(str(i) + ": " + eachWellplate.model)
                    i = i + 1
                self.selected_labware_box = ttk.Combobox(self.loaded_labware_bar, state='readonly')
                self.selected_labware_box.grid(row=2,column=1)
                self.selected_labware_box["values"] = [*self.loaded_labware]
                self.selected_labware_box.bind("<<ComboboxSelected>>", lambda x: self.UpdateSelectedLabware())
                self.selected_labware_label = tk.Label(self.loaded_labware_bar, text="Select Wellplate Index: ",justify=tk.LEFT)
                self.selected_labware_label.grid(row=2,column=0)
            
            case "Named Location":
                for eachLocation in coordinator.myModules.myStages[self.selected_stage].myLabware.custom_locations:
                    self.loaded_labware.append(eachLocation)
                self.selected_labware_box = ttk.Combobox(self.loaded_labware_bar, state='readonly')
                self.selected_labware_box.grid(row=2,column=1)
                self.selected_labware_box["values"] = [*self.loaded_labware]
                self.selected_labware_box.bind("<<ComboboxSelected>>", lambda x: self.UpdateSelectedLabware())

    def UpdateSelectedLabware(self, *args):
        self.selected_labware = self.selected_labware_box.get()
        self.past_labware = self.selected_labware
        self.wellName =tk.Entry(self.loaded_labware_bar)
        self.wellName.grid(row=1,column=4)
        self.wellName.destroy()
        match self.selected_labware_type:
            case "Wellplate":
                self.wellLabel = tk.Label(self.loaded_labware_bar, text="Well: ")
                self.wellLabel.grid(row=3,column=0)
                self.wellName = tk.Entry(self.loaded_labware_bar)
                self.wellName.grid(row=3,column=1)
                self.moveButton = tk.Button(self.loaded_labware_bar, text="Go To Well", command=lambda: self.GoToWell(self.coordinator))
                self.moveButton.grid(row=4,column=1)

            case "Named Location":
                # this isn't finished 
                self.moveButton = tk.Button(self.loaded_labware_bar, text="Go To Location", command=lambda: self.GoToLocation(self.coordinator))
                self.moveButton.grid(row=1,column=3)
    
    def GoToWell(self, coordinator):
        match self.selected_labware_type:
            case "Wellplate":
                location = coordinator.myModules.myStages[self.selected_stage].myLabware.get_well_location(int(self.selected_labware[0]), self.wellName.get())
                coordinator.myModules.myStages[self.selected_stage].move_to(location)           

    def GoToLocation(self, coordinator):
        # this isn't finished
        self.coordinator.actionOptions.move_to_location(self.selected_stage, self.selected_labware)
