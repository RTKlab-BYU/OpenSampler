import tkinter as tk
from tkinter import ttk
import threading

class Manual(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Manual Control")
        self.geometry("1200x800")

        self.coordinator = coordinator
        # self.thread = threading.Thread(target=self.do_nothing,args=(30,))

        self.main_frame = tk.Frame(self)
        self.main_frame.place(anchor="c", relx=.5, rely=.5)

        self.stage_controls = tk.Frame(self.main_frame)
        self.stage_controls.pack()
        self.temp_deck_frame = tk.Frame(self.main_frame, highlightbackground="black", highlightthickness=2, padx=5, pady=5)
        self.temp_deck_frame.pack(fill="x", pady=5)

        # stage has to be selected before controls work, goes above everything else
        self.stage_selection = tk.Frame(self.stage_controls)
        self.stage_controls_body = tk.Frame(self.stage_controls, highlightbackground="black", highlightthickness=2, padx=5, pady=5)
        self.stage_selection.pack(fill="x")
        self.stage_controls_body.pack()

        # inside stage_controls_body
        self.xyz_controls = tk.Frame(self.stage_controls_body, highlightbackground="black", highlightthickness=2, padx=5, pady=5)
        self.syringe_controls = tk.Frame(self.stage_controls_body, highlightbackground="black", highlightthickness=2, padx=5, pady=5)
        self.coordinates_box = tk.Frame(self.stage_controls_body, highlightbackground="black", highlightthickness=2, padx=5, pady=5)
        self.move_to_box = tk.Frame(self.stage_controls_body, highlightbackground="black", highlightthickness=2, padx=5, pady=5)

        self.xyz_label = tk.Label(self.stage_controls_body, text="XYZ")
        self.syringe_label = tk.Label(self.stage_controls_body, text="Syringe")
        self.coordinates_label = tk.Label(self.stage_controls_body, text="Coordinates")
        self.move_label = tk.Label(self.stage_controls_body, text="Move To")

        self.xyz_label.grid(row=0, column=0, sticky="W", padx=5)
        self.syringe_label.grid(row=0, column=1, sticky="W", padx=5)
        self.xyz_controls.grid(row=1, column=0, sticky="NSEW", padx=5)
        self.syringe_controls.grid(row=1, column=1, sticky="NSEW", padx=5)
        self.coordinates_label.grid(row=2, column=0, sticky="W", padx=5)
        self.move_label.grid(row=2, column=1, sticky="W", padx=5)
        self.coordinates_box.grid(row=3, column=0, sticky="NSEW", padx=5)
        self.move_to_box.grid(row=3, column=1, sticky="NSEW", padx=5)

        #######

        # stage selection
        self.stage_label = tk.Label(self.stage_selection, text="Stage: ")
        self.stage_label.pack(side="left")
        self.stage_drop_box = ttk.Combobox(self.stage_selection, state="readonly")
        self.stage_drop_box.pack(side="left")
        stageOptions = coordinator.myModules.myStages.keys()
        self.stage_drop_box["values"] = [*stageOptions]
        self.stage_drop_box.bind("<<ComboboxSelected>>", lambda x: self.UpdateSelectedMotors(coordinator))


        # inside xyz_controls
        self.xyz_settings = tk.Frame(self.xyz_controls, highlightbackground="black", highlightthickness=2)
        self.xyz_move_buttons = tk.Frame(self.xyz_controls, highlightbackground="black", highlightthickness=2)

        self.xyz_settings.pack(pady=5)
        self.xyz_move_buttons.pack(fill="x", pady=5)

        self.joy_label = tk.Label(self.xyz_settings, text="Joystick", background="red")
        self.step_size_label = tk.Label(self.xyz_settings, text="Step Size (mm)")
        self.step_speed_label = tk.Label(self.xyz_settings, text="Speed (mm/s)")

        self.joy_on_off = tk.StringVar(self.xyz_settings, value="Off")
        self.joy_button = tk.Button(self.xyz_settings, state="disabled", textvariable=self.joy_on_off)

        self.step_size = tk.StringVar(value=10)
        self.step_size_dropbox = ttk.Combobox(self.xyz_settings, textvariable=self.step_size)
        self.step_size_dropbox["values"] = [0.01, 0.1, 1, 5, 10, 25, 50]

        self.step_speed = tk.StringVar(self.xyz_settings, value=9001)
        self.step_speed_dropbox = ttk.Combobox(self.xyz_settings, textvariable=self.step_speed, state="readonly")
        self.step_speed_dropbox["values"] = [100, 500, 9001]

        self.joy_label.grid(row=0, column=0)
        self.step_size_label.grid(row=0, column=1)
        self.step_speed_label.grid(row=0, column=2)
        self.joy_button.grid(row=1, column=0)
        self.step_size_dropbox.grid(row=1, column=1)
        self.step_speed_dropbox.grid(row=1, column=2)

        self.xy_buttons = tk.Frame(self.xyz_move_buttons)
        self.z_buttons = tk.Frame(self.xyz_move_buttons)
        self.xy_buttons.grid(row=0, column=0, padx=5, pady=5)
        self.z_buttons.grid(row=0, column=1)
        self.xyz_move_buttons.columnconfigure(0, weight=4)
        self.xyz_move_buttons.columnconfigure(1, weight=3)

        self.x_left = tk.Button(self.xy_buttons, text="X Left")
        self.x_right = tk.Button(self.xy_buttons, text="X Left")
        self.y_back = tk.Button(self.xy_buttons, text="Y Back")
        self.y_front = tk.Button(self.xy_buttons, text="Y Front")
        self.z_up = tk.Button(self.z_buttons, text="Z Up")
        self.z_down = tk.Button(self.z_buttons, text="Z Down")

        self.x_left.grid(row=1, column=0, padx=5, pady=5)
        self.x_right.grid(row=1, column=2, padx=5, pady=5)
        self.y_back.grid(row=0, column=1, padx=5, pady=5)
        self.y_front.grid(row=2, column=1, padx=5, pady=5)
        self.z_up.grid(row=0, column=0, padx=5, pady=5)
        self.z_down.grid(row=1, column=0, padx=5, pady=5)


        # inside syringe controls
        self.max_rest_min_buttons = tk.Frame(self.syringe_controls, pady=5)
        self.asp_disp_control = tk.Frame(self.syringe_controls, padx=5)

        self.max_rest_min_buttons.grid(row=0, column=0)
        self.asp_disp_control.grid(row=1, column=0)

        self.max_frame = tk.Frame(self.max_rest_min_buttons)
        self.rest_frame = tk.Frame(self.max_rest_min_buttons, padx=10)
        self.min_frame = tk.Frame(self.max_rest_min_buttons)
        self.max_frame.pack(side="left", fill="x")
        self.rest_frame.pack(side="left", fill="x")
        self.min_frame.pack(side="left", fill="x")

        self.syringe_max_button = tk.Button(self.max_frame, text="Max", padx=5)
        self.syringe_rest_button = tk.Button(self.rest_frame, text="Rest", padx=5)
        self.syringe_min_button = tk.Button(self.min_frame, text="Min", padx=5)

        self.syringe_max_button.grid(row=0, column=0, sticky="E")
        self.syringe_rest_button.grid(row=0, column=1)
        self.syringe_min_button.grid(row=0, column=2, sticky="W")
        
        self.aspirate_button = tk.Button(self.asp_disp_control, text="Aspirate")
        self.dispense_button = tk.Button(self.asp_disp_control, text="Dispense")

        self.syringe_volume_label = tk.Label(self.asp_disp_control, text="Vol. (nL)")
        self.syringe_speed_label = tk.Label(self.asp_disp_control, text="Speed (nL/s)")

        self.syringe_volume_entry = tk.Entry(self.asp_disp_control)
        self.syringe_speed_entry = tk.Entry(self.asp_disp_control)
        self.syringe_volume_entry.insert(tk.END, "500")
        self.syringe_speed_entry.insert(tk.END, "3000")

        self.aspirate_button.grid(row=0, column=0, sticky="EW", padx=5)
        self.dispense_button.grid(row=0, column=1, sticky="EW", padx=5)
        self.syringe_volume_label.grid(row=1, column=0)
        self.syringe_speed_label.grid(row=1, column=1)
        self.syringe_volume_entry.grid(row=2, column=0)
        self.syringe_speed_entry.grid(row=2, column=1)


        # inside coordinates_box
        self.x_label = tk.Label(self.coordinates_box, text="X")
        self.y_label = tk.Label(self.coordinates_box, text="Y")
        self.z_label = tk.Label(self.coordinates_box, text="Z")
        self.syringe_pos_label = tk.Label(self.coordinates_box, text="Syringe")
        self.max_label = tk.Label(self.coordinates_box, text="Max")
        self.current_label = tk.Label(self.coordinates_box, text="Current")
        self.min_label = tk.Label(self.coordinates_box, text="Min")


        self.x_label.grid(row=0, column=1)
        self.y_label.grid(row=0, column=2)
        self.z_label.grid(row=0, column=3)
        self.syringe_pos_label.grid(row=0, column=4)
        self.max_label.grid(row=1, column=0)
        self.current_label.grid(row=2, column=0)
        self.min_label.grid(row=3, column=0)
        self.coordinates_box.columnconfigure(index=0, weight=1)
        self.coordinates_box.columnconfigure(index=1, weight=1)
        self.coordinates_box.columnconfigure(index=2, weight=1)
        self.coordinates_box.columnconfigure(index=3, weight=1)
        self.coordinates_box.columnconfigure(index=4, weight=1)
        self.coordinates_box.rowconfigure(index=0, weight=1)
        self.coordinates_box.rowconfigure(index=1, weight=1)
        self.coordinates_box.rowconfigure(index=2, weight=1)
        self.coordinates_box.rowconfigure(index=3, weight=1)
        


        # inside move_to_box
        self.target_1 = tk.StringVar(self.move_to_box)
        self.target_2 = tk.StringVar(self.move_to_box)
        self.move_dropbox_1 = ttk.Combobox(self.move_to_box, textvariable=self.target_1) 
        self.move_dropbox_2 = ttk.Combobox(self.move_to_box, textvariable=self.target_2)
        self.go_button = tk.Button(self.move_to_box, text="Go") 

        self.move_dropbox_1.grid(row=0, column=0, sticky="WE")
        self.move_dropbox_2.grid(row=1, column=0, sticky="WE")
        self.go_button.grid(row=2, column=0)

        

        # tempdeck control

        self.temp_deck_control = tk.Frame(self.temp_deck_frame)
        self.temp_deck_control.pack()

        self.tempdeck_label = tk.Label(self.temp_deck_control, text="Tempdeck")
        self.selected_tempdeck = tk.StringVar(self.temp_deck_control, value="")
        self.tempdeck_dropbox = ttk.Combobox(self.temp_deck_control, textvariable=self.selected_tempdeck)
        self.temperature_label = tk.Label(self.temp_deck_control, text="Temperature (C)")
        self.temperature_entry = tk.Entry(self.temp_deck_control)
        self.set_temp_button = tk.Button(self.temp_deck_control, text="Set", padx=10)

        self.temperature_entry.insert(tk.END, "15")

        self.tempdeck_label.pack(side="left")
        self.tempdeck_dropbox.pack(side="left")
        self.temperature_label.pack(side="left")
        self.temperature_entry.pack(side="left")
        self.set_temp_button.pack(side="left")





        # self.joyBar = tk.Frame(self)
        # self.joyBar.pack(side=tk.TOP)

        # stageOptions = coordinator.myModules.myStages.keys()
        # self.loaded_labware_bar = tk.Frame(self)
        # self.loaded_labware_bar.pack(side=tk.TOP)
        # self.settingsFileLabel = tk.Label(self.loaded_labware_bar, text="Select Stage: ",justify=tk.LEFT)
        # self.settingsFileLabel.grid(row=0,column=0)
        # if(len(stageOptions)>0):
        #     self.loadedMotorSeries = ttk.Combobox(self.loaded_labware_bar, state='readonly')
        #     self.loadedMotorSeries.grid(row=0,column=1)
        #     self.loadedMotorSeries["values"] = [*stageOptions]
        #     self.loadedMotorSeries.bind("<<ComboboxSelected>>", lambda x: self.UpdateSelectedMotors(coordinator))
        
        # # self.joystick = ttk.Combobox(self.joyBar, state='readonly')
        # # self.joystick.grid(row=0,column=0)
        # # self.joystick["values"] = [*coordinator.myModules.myJoystickProfiles.keys()]
        # self.joyButton = tk.Button(self.joyBar,text="Start Joystick",command=lambda: self.StartJoystick(coordinator),justify=tk.LEFT)
        # self.joyButton.grid(row=0,column=1)
        # self.joyButton["state"] = "disabled"
        # self.killButton = tk.Button(self.joyBar,text="Kill Joystick",command=lambda: self.KillJoystick(coordinator),justify=tk.LEFT)
        # self.killButton.grid(row=0,column=2)
        # self.killButton["state"] = "disabled"
        # self.selected_labware_type = tk.StringVar(self,None)
        # self.selected_labware = tk.StringVar(self,None)
        # self.past_type = None
        # self.past_motor = None
        # self.past_labware = None

        # self.protocol('WM_DELETE_WINDOW', self.on_closing)

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
                self.moveButton = tk.Button(self.loaded_labware_bar, text="Go To Well", command=lambda: self.GoToWell())
                self.moveButton.grid(row=4,column=1)

            case "Named Location":
                # this isn't finished 
                self.moveButton = tk.Button(self.loaded_labware_bar, text="Go To Location", command=lambda: self.GoToLocation())
                self.moveButton.grid(row=1,column=3)
    
    def GoToWell(self):
        match self.selected_labware_type:
            case "Wellplate":
                location = self.coordinator.myModules.myStages[self.selected_stage].myLabware.get_well_location(int(self.selected_labware[0]), self.wellName.get())
                self.coordinator.myModules.myStages[self.selected_stage].move_to(location)           

    def GoToLocation(self):
        # this isn't finished
        self.coordinator.actionOptions.move_to_location(self.selected_stage, self.selected_labware)
