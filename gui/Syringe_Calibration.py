import tkinter as tk
import time

LEFT = 'Left' #A
RIGHT = 'Right' #B

"""
Syringe calibration is used to set the syringe max, min, and rest (default) positions. 
These settings are not saved. They must be set each time the robot is run.
"""

class Syringe_Calibration(tk.Toplevel,):
    def __init__(self, coordinator, selected_stage, syringe_type):
        tk.Toplevel.__init__(self)    
      
        self.title("Syringe Clibration")
        self.geometry("500x500")
        self.myStage = coordinator.myModules.myStages[selected_stage]
        self.myStage.myLabware.set_syringe_model(syringe_type)
        self.min_set = False
        self.max_set = False
        self.rest_set = False
        self.coordinator = coordinator
        self.selected_stage = selected_stage        

        # buttons to start and stop joystick
        self.joyBar = tk.Frame(self)
        self.joyBar.pack(side=tk.TOP)
        self.joyButton = tk.Button(self.joyBar, text="Start Joystick", command=lambda: self.start_joystick(), justify=tk.LEFT)
        self.joyButton.grid(row=0,column=1)
        self.killButton = tk.Button(self.joyBar, text="Kill Joystick", command=lambda: self.kill_joystick(), justify=tk.LEFT)
        self.killButton.grid(row=0,column=2)
        self.killButton["state"] = "disabled"

        # these are the buttons that do everything
        self.setterBar = tk.Frame(self)
        self.setterBar.pack(side=tk.TOP)

        self.home_button = tk.Button(self.setterBar, text="Home Syringe", command=lambda: self.home_syringe())
        self.max_button = tk.Button(self.setterBar, text="Set Max", command=lambda: self.SetMax())
        self.rest_button = tk.Button(self.setterBar, text="Set Rest", command=lambda: self.SetRest())
        self.min_button = tk.Button(self.setterBar, text="Set Min", command=lambda: self.SetMin())

        self.home_button.grid(row=0, column=0)
        self.max_button.grid(row=0, column=1)
        self.rest_button.grid(row=0, column=2)
        self.min_button.grid(row=0, column=3)

        # specify speed and volume then click buttons for aspirate and dispense
        self.syringe_control = tk.Frame(self)
        self.syringe_control.pack()

        self.volume_var = tk.StringVar(self)  # nL
        self.volume_var.set("3500")
        self.volume_label = tk.Label(self.syringe_control, text="Volume (nL):")
        self.volume = tk.Entry(self.syringe_control, textvariable=self.volume_var)

        self.speed_var = tk.StringVar(self)  # nL per min
        self.speed_var.set("3000")
        self.speed_label = tk.Label(self.syringe_control, text="Speed (nL/min)")
        self.speed = tk.Entry(self.syringe_control, textvariable=self.speed_var)

        self.volume_label.grid(row=0, column=0)
        self.speed_label.grid(row=0, column=1)
        self.volume.grid(row=1, column=0)
        self.speed.grid(row=1, column=1)

        self.aspirate_button = tk.Button(self.syringe_control, text="Aspirate",command=lambda: self.Aspirate())
        self.dispense_button = tk.Button(self.syringe_control, text="Dispense",command=lambda: self.Dispense())
        self.aspirate_button.grid(row=0,column=2)
        self.dispense_button.grid(row=1,column=2)

        # display the syringe limits
        self.syringe_positions = tk.Frame(self)
        self.syringe_positions.pack(padx=20, pady=20)

        # get current limit to display
        self.current_position = tk.StringVar(self.syringe_positions, self.myStage.get_syringe_location())
        self.syringe_min = tk.StringVar(self.syringe_positions, self.myStage.myLabware.get_syringe_min())
        self.syringe_rest = tk.StringVar(self.syringe_positions, self.myStage.myLabware.get_syringe_rest())
        self.syringe_max = tk.StringVar(self.syringe_positions, self.myStage.myLabware.get_syringe_max())
        
        self.current_position_label = tk.Label(self.syringe_positions, text="Current Position: ")
        self.syringe_min_label = tk.Label(self.syringe_positions, text="Syringe Min: ")
        self.syringe_rest_label = tk.Label(self.syringe_positions, text="Syringe Rest: ")
        self.syringe_max_label = tk.Label(self.syringe_positions, text="Syringe Max: ")
        
        self.current_position_value = tk.Label(self.syringe_positions, textvariable=self.current_position)
        self.syringe_min_value = tk.Label(self.syringe_positions, textvariable=self.syringe_min)
        self.syringe_rest_value = tk.Label(self.syringe_positions, textvariable=self.syringe_rest)
        self.syringe_max_value = tk.Label(self.syringe_positions, textvariable=self.syringe_max)
        
        self.current_position_label.grid(row=0, column=0)
        self.syringe_min_label.grid(row=1, column=0)
        self.syringe_rest_label.grid(row=2, column=0)
        self.syringe_max_label.grid(row=3, column=0)
        
        self.current_position_value.grid(row=0, column=1)
        self.syringe_min_value.grid(row=1, column=1)
        self.syringe_rest_value.grid(row=2, column=1)
        self.syringe_max_value.grid(row=3, column=1)
        
        if self.myStage.stage_type == "Opentrons": #This stage type is more descriptive than the one fed into this method
            self.Create_Attach_Button()

        self.protocol('WM_DELETE_WINDOW', self.on_closing)






    # this just changes the state internally, could remake this to update button rather than destroy and remake but not high priority
    def Create_Attach_Button(self):
        if self.myStage.side == LEFT:
            self.syringeAttached = self.myStage.left_syringe_mount_attached
        elif self.myStage.side == RIGHT:
            self.syringeAttached = self.myStage.right_syringe_mount_attached
        else:
            print("ERROR, side not detected on opentrons")

        if self.syringeAttached:
            self.attachButton = tk.Button(self.setterBar,text="Remove Syringe",command=lambda: self.ToggleAttached(),justify=tk.LEFT)
            self.attachButton.grid(row=0,column=4)
        elif not self.syringeAttached:
            self.attachButton = tk.Button(self.setterBar,text="Attach Syringe",command=lambda: self.ToggleAttached(),justify=tk.LEFT)
            self.attachButton.grid(row=0,column=4)

    # changes state of pipette for current stage     
    def ToggleAttached(self):
        self.attachButton.destroy()    
        self.myStage.add_or_remove_syringe_mount()
        self.Create_Attach_Button()

    def SetMin(self):
        current_location = self.myStage.get_syringe_location()
        self.myStage.myLabware.set_syringe_min(current_location)
        self.min_set = True
        self.update_syringe_states()
    
    def SetMax(self):
        current_location = self.myStage.get_syringe_location()
        self.myStage.myLabware.set_syringe_max(current_location)
        self.max_set = True
        self.update_syringe_states()
    
    def SetRest(self):
        current_location = self.myStage.get_syringe_location()
        self.myStage.myLabware.set_syringe_rest(current_location)
        self.rest_set = True
        self.update_syringe_states()

    def set_syringe_speed(self, speed):
        self.speed_var = speed

    def set_target_volume(self, volume):
        self.volume_var = volume

    def update_syringe_states(self):
        if self.min_set and self.max_set and self.rest_set:
            print("Syringe positions defined!")

        self.current_position.set(self.myStage.get_syringe_location())
        self.syringe_min.set(self.myStage.myLabware.get_syringe_min())
        self.syringe_rest.set(self.myStage.myLabware.get_syringe_rest())
        self.syringe_max.set(self.myStage.myLabware.get_syringe_max())

    def start_joystick(self):
        self.coordinator.start_joystick(self.selected_stage)
        self.killButton["state"] = "normal"
        self.joyButton["state"] = "disabled"

    def kill_joystick(self):
        self.coordinator.stop_joystick()
        self.killButton["state"] = "disabled"
        self.joyButton["state"] = "normal"
        
    def on_closing(self):
        self.kill_joystick()
        # time.sleep(3)
        self.destroy()
        





# Action Commands
    def home_syringe(self):
        print("\nHoming Syringe!")
        cnt = 0
        limit = 5
        while cnt < limit:
                cnt += 1
                self.myStage.home_syringe()
                current_position = self.myStage.get_syringe_location()
                if current_position == 18.0:
                    print("Syringe Homed")
                    self.update_syringe_states()
                    return
                
        print(f"Type: {type(current_position)}")
        print(f"Current Syringe Position: {current_position}")
        print("Cannot Home Syringe at this time.")

    def Aspirate(self):
        # print(f"stage index: {self.selected_stage}")
        # print(f"stage side: {self.coordinator.myModules.myStages[self.selected_stage].side}")
        self.coordinator.myLogger.info(f"Aspirating {self.volume_var.get()} nL at speed {self.speed_var.get()} nL/min")
        self.coordinator.myModules.myStages[self.selected_stage].step_syringe_motor_up(volume = float(self.volume_var.get()), speed = float(self.speed_var.get()))
        self.update_syringe_states()

    def Dispense(self):
        # print(f"stage index: {self.selected_stage}")
        # print(f"stage side: {self.coordinator.myModules.myStages[self.selected_stage].side}")
        self.coordinator.myLogger.info(f"Aspirating {self.volume_var.get()} nL at speed {self.speed_var.get()} nL/min")
        self.coordinator.myModules.myStages[self.selected_stage].step_syringe_motor_down(volume = float(self.volume_var.get()), speed = float(self.speed_var.get()))
        self.update_syringe_states()

    
