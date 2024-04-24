import tkinter as tk
import threading
import time

from Classes.coordinator import Coordinator
from Classes.module_files.labware import Labware

class Custom_Location(tk.Toplevel,):
    def __init__(self, coordinator, selected_stage):
        tk.Toplevel.__init__(self)    
      
        self.title("Calibrate New Location")
        self.geometry("500x500")

        self.coordinator: Coordinator = coordinator
        self.selected_stage = selected_stage
        self.my_labware: Labware = self.coordinator.myModules.myStages[selected_stage].myLabware

        self.joyBar = tk.Frame(self)
        self.joyBar.pack(side=tk.TOP)
        self.joyButton = tk.Button(self.joyBar,text="Start Joystick",command=self.start_joystick,justify=tk.LEFT)
        self.joyButton.grid(row=0,column=1)
        self.killButton = tk.Button(self.joyBar,text="Kill Joystick",command=self.kill_joystick,justify=tk.LEFT)
        self.killButton.grid(row=0,column=2)
        self.killButton["state"] = "disabled"

        tk.Label(self, text="New Name",justify=tk.LEFT).pack(side=tk.TOP)
        self.newNickname = tk.Entry(self)
        self.newNickname.pack(side=tk.TOP)
        
        # current location of stage motors
        tk.Label(self, text="Current Location",justify=tk.LEFT).pack(side=tk.TOP)
        self.LocationFrame = tk.Frame(self)
        self.LocationFrame.pack(side=tk.TOP)

        x,y,z = self.coordinator.myModules.myStages[self.selected_stage].get_motor_coordinates()

        self.x_var = tk.DoubleVar(self,value=x)
        self.y_var = tk.DoubleVar(self,value=y)
        self.z_var = tk.DoubleVar(self,value=z)

        x_lab = tk.Label(self.LocationFrame, text="x",justify=tk.LEFT)
        y_lab = tk.Label(self.LocationFrame, text="y",justify=tk.LEFT)
        z_lab = tk.Label(self.LocationFrame, text="z",justify=tk.LEFT)
        x_lab.grid(row=0,column=0)
        y_lab.grid(row=0,column=1)
        z_lab.grid(row=0,column=2)

        self.x_loc = tk.Label(self.LocationFrame, textvariable=self.x_var, justify=tk.LEFT)
        self.y_loc =tk.Label(self.LocationFrame, textvariable=self.y_var, justify=tk.LEFT)
        self.z_loc =tk.Label(self.LocationFrame, textvariable=self.z_var, justify=tk.LEFT)
        self.x_loc.grid(row=1,column=0)
        self.y_loc.grid(row=1,column=1)
        self.z_loc.grid(row=1,column=2)  
    
        self.x_var.set(x)
        self.y_var.set(y)
        self.z_var.set(z)

        self.save_button = tk.Button(self,text="Save Named Location",command=lambda: self.CreateNickname(),justify=tk.LEFT)
        self.save_button.pack(side=tk.TOP)

        self.position_thread = threading.Thread(target=self.update_positions)

        self.protocol('WM_DELETE_WINDOW', self.on_closing)

    def CreateNickname(self):
        location_name = self.newNickname.get()
        location: tuple = self.coordinator.myModules.myStages[self.selected_stage].get_motor_coordinates()
        self.my_labware.add_custom_location(location_name, location)
        self.on_closing()

    # this method is run inside a thread
    def update_positions(self):
        self.updating_positions = True
        cnt = 0

        while self.updating_positions:
            x,y,z = self.coordinator.myModules.myStages[self.selected_stage].get_motor_coordinates()
            self.x_var.set(x)
            self.y_var.set(y)
            self.z_var.set(z)
            cnt += 1
            if cnt == 10:
                cnt = 0
                print("Thread is live: ", self.updating_positions)
            time.sleep(1)

        print("done with position thread")


    # sets flag to false, then waits until position_thread has ended to proceed
    def stop_updating_positions(self):
        self.updating_positions = False
        while self.position_thread.is_alive():
            print("I'm not dead yet!")
            time.sleep(1)
    
    def start_joystick(self):
        print("checkpoint 1")
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

            