import tkinter as tk
import threading

class Custom_Location(tk.Toplevel,):
    def __init__(self, coordinator, selectedStage):
        tk.Toplevel.__init__(self)    
      
        self.title("Calibrate New Location")
        self.geometry("500x500")

        self.coordinator = coordinator
        self.thread = threading.Thread(target=self.do_nothing,args=(30,))

        self.joyBar = tk.Frame(self)
        self.joyBar.pack(side=tk.TOP)
        self.joyButton = tk.Button(self.joyBar,text="Start Joystick",command=lambda: self.StartJoystick(coordinator, selectedStage),justify=tk.LEFT)
        self.joyButton.grid(row=0,column=1)
        self.killButton = tk.Button(self.joyBar,text="Kill Joystick",command=lambda: self.KillJoystick(coordinator),justify=tk.LEFT)
        self.killButton.grid(row=0,column=2)
        self.killButton["state"] = "disabled"

        tk.Label(self, text="New Name",justify=tk.LEFT).pack(side=tk.TOP)
        self.newNickname = tk.Entry(self)
        self.newNickname.pack(side=tk.TOP)
        
        tk.Label(self, text="Current Location",justify=tk.LEFT).pack(side=tk.TOP)
        self.LocationFrame = tk.Frame(self)
        self.LocationFrame.pack(side=tk.TOP)
        tk.Label(self.LocationFrame, text="x",justify=tk.LEFT).grid(row=0,column=0)
        tk.Label(self.LocationFrame, text="y",justify=tk.LEFT).grid(row=0,column=1)
        tk.Label(self.LocationFrame, text="z",justify=tk.LEFT).grid(row=0,column=2)
        x,y,z = coordinator.myModules.myStages[selectedStage].get_motor_coordinates()
        self.xLoc = tk.DoubleVar(self,value=x)
        self.xLab = tk.Label(self.LocationFrame, textvariable=self.xLoc, justify=tk.LEFT)
        self.xLab.grid(row=1,column=0)
        self.yLoc = tk.DoubleVar(self,value=y)
        self.yLab =tk.Label(self.LocationFrame, textvariable=self.yLoc, justify=tk.LEFT)
        self.yLab.grid(row=1,column=1)
        self.zLoc = tk.DoubleVar(self,value=z)
        self.zLab =tk.Label(self.LocationFrame, textvariable=self.zLoc, justify=tk.LEFT)
        self.zLab.grid(row=1,column=2)   
    
        x,y,z = coordinator.myModules.myStages[selectedStage].get_motor_coordinates()
        self.xLoc.set(x)
        self.yLoc.set(y)
        self.zLoc.set(z)
        tk.Button(self,text="Save Named Location",command=lambda: self.CreateNickname(coordinator, selectedStage),justify=tk.LEFT).pack(side=tk.TOP)

        self.protocol('WM_DELETE_WINDOW', self.on_closing)

    def CreateNickname(self, coordinator, selectedStage: int):
        location_name = self.newNickname.get()
        location: tuple = coordinator.myModules.myStages[selectedStage].get_motor_coordinates()
        coordinator.myModules.myStages[selectedStage].myLabware.add_custom_location(location_name, location)
        if self.thread.is_alive():
            self.KillJoystick(coordinator)
        while self.thread.is_alive():
            # print("*")
            pass
        self.destroy()

    def on_closing(self):
        if self.thread.is_alive():
            self.KillJoystick(self.coordinator)
        self.destroy()

    def do_nothing(self, *args):
        pass
        #do nothing

    def GetPositions(self, coordinator, selectedStage):
        i = 0
        while (self.thread.is_alive() or i < 1):
            x,y,z = coordinator.myModules.myStages[selectedStage].get_motor_coordinates()
            self.xLoc.set(x)
            self.yLoc.set(y)
            self.zLoc.set(z)
            i = i + 1
    
    def StartJoystick(self, coordinator, selectedStage):
        self.thread = threading.Thread(target=coordinator.start_joystick,args=(selectedStage,))
        self.thread.start()
        self.killButton["state"] = "normal"
        self.joyButton["state"] = "disabled"
        
        threading.Thread(target=self.GetPositions, args=[coordinator,selectedStage]).start()


    def KillJoystick(self, coordinator):
        coordinator.stop_joystick()
        self.killButton["state"] = "disabled"
        self.joyButton["state"] = "normal"

            