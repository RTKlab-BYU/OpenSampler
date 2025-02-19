import tkinter as tk
from tkinter import ttk
import threading
import time

class Manual(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Manual Control")
        self.geometry("1200x800")

        self.coordinator = coordinator

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
        self.selected_stage = tk.StringVar(value="")
        self.previous_selected_stage = "None"
        self.stage_drop_box = ttk.Combobox(self.stage_selection, textvariable=self.selected_stage, state="readonly")
        self.stage_drop_box.pack(side="left")
        stageOptions = list(self.coordinator.myModules.myStages.keys())
        stageOptions.insert(0,"")
        self.stage_drop_box["values"] = [*stageOptions]
        if "Left_OT" in stageOptions:
            self.stage_drop_box.current(stageOptions.index("Left_OT"))
        else:
            self.stage_drop_box.current(0)
        self.stage_drop_box.bind("<<ComboboxSelected>>", lambda x: self.update_options)


        # inside xyz_controls
        self.xyz_settings = tk.Frame(self.xyz_controls, highlightbackground="black", highlightthickness=2)
        self.xyz_move_buttons = tk.Frame(self.xyz_controls, highlightbackground="black", highlightthickness=2)

        self.xyz_settings.pack(pady=5)
        self.xyz_move_buttons.pack(fill="x", pady=5)

        self.joy_label = tk.Label(self.xyz_settings, text="Joystick", background="red")
        self.step_size_label = tk.Label(self.xyz_settings, text="Step Size (mm)")
        self.step_speed_label = tk.Label(self.xyz_settings, text="Speed (mm/s)")

        self.joystick_running = False
        self.joy_on_off = tk.StringVar(self.xyz_settings, value="Turn On")
        self.joy_button = tk.Button(self.xyz_settings, state="disabled", textvariable=self.joy_on_off, command=self.update_joystick)

        self.step_size = tk.StringVar(value=10)
        self.step_size_dropbox = ttk.Combobox(self.xyz_settings, textvariable=self.step_size)
        self.step_size_dropbox["values"] = [0.01, 0.1, 1, 5, 10, 25, 50]
        self.step_size_dropbox.bind("<<ComboboxSelected>>", self.update_step_size)

        self.step_speed = tk.StringVar(self.xyz_settings, value=9001)
        self.step_speed_dropbox = tk.Entry(self.xyz_settings, textvariable=self.step_speed, state="readonly")

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

        self.x_left = tk.Button(self.xy_buttons, text="X Left", command=self.move_x_left)
        self.x_right = tk.Button(self.xy_buttons, text="X Right", command=self.move_x_right)
        self.y_back = tk.Button(self.xy_buttons, text="Y Back", command=self.move_y_forward)
        self.y_front = tk.Button(self.xy_buttons, text="Y Front", command=self.move_y_back)
        self.z_up = tk.Button(self.z_buttons, text="Z Up", command=self.move_z_up)
        self.z_down = tk.Button(self.z_buttons, text="Z Down", command=self.move_z_down)

        self.x_left.grid(row=1, column=0, padx=5, pady=5)
        self.x_right.grid(row=1, column=2, padx=5, pady=5)
        self.y_back.grid(row=0, column=1, padx=5, pady=5)
        self.y_front.grid(row=2, column=1, padx=5, pady=5)
        self.z_up.grid(row=0, column=0, padx=5, pady=5)
        self.z_down.grid(row=1, column=0, padx=5, pady=5)


        # inside syringe controls
        self.max_rest_min_buttons = tk.Frame(self.syringe_controls, pady=5)
        self.asp_disp_control = tk.Frame(self.syringe_controls, padx=5)
        self.syringe_model_box = tk.Frame(self.syringe_controls, pady=5)

        self.max_rest_min_buttons.grid(row=0, column=0)
        self.asp_disp_control.grid(row=1, column=0)
        self.syringe_model_box.grid(row=2, column=0)

        self.max_frame = tk.Frame(self.max_rest_min_buttons)
        self.rest_frame = tk.Frame(self.max_rest_min_buttons, padx=10)
        self.min_frame = tk.Frame(self.max_rest_min_buttons)
        self.max_frame.pack(side="left", fill="x")
        self.rest_frame.pack(side="left", fill="x")
        self.min_frame.pack(side="left", fill="x")

        self.syringe_max_button = tk.Button(self.max_frame, text="Max", padx=5, command=self.syringe_to_max)
        self.syringe_rest_button = tk.Button(self.rest_frame, text="Rest", padx=5, command=self.syringe_to_rest)
        self.syringe_min_button = tk.Button(self.min_frame, text="Min", padx=5, command=self.syringe_to_min)

        self.syringe_max_button.grid(row=0, column=0, sticky="E")
        self.syringe_rest_button.grid(row=0, column=1)
        self.syringe_min_button.grid(row=0, column=2, sticky="W")
        
        self.aspirate_button = tk.Button(self.asp_disp_control, text="Aspirate", command=self.aspirate)
        self.dispense_button = tk.Button(self.asp_disp_control, text="Dispense", command=self.dispense)

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

        current_model = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.get_syringe_model()
        self.syringe_model = tk.StringVar(value= "Syringe Model: " + current_model)
        self.syringe_model_label = tk.Label(self.syringe_model_box, textvariable=self.syringe_model)

        self.syringe_model_label.pack()


        # inside coordinates_box
        self.x_label = tk.Label(self.coordinates_box, text="X")
        self.y_label = tk.Label(self.coordinates_box, text="Y")
        self.z_label = tk.Label(self.coordinates_box, text="Z")
        self.syringe_pos_label = tk.Label(self.coordinates_box, text="Syringe")
        self.max_label = tk.Label(self.coordinates_box, text="Max")
        self.current_label = tk.Label(self.coordinates_box, text="Current")
        self.min_label = tk.Label(self.coordinates_box, text="Min")

        self.x_max = tk.StringVar(self, value="")
        self.x_current = tk.StringVar(self, value="")
        self.x_min = tk.StringVar(self, value="")
        self.y_max = tk.StringVar(self, value="")
        self.y_current = tk.StringVar(self, value="")
        self.y_min = tk.StringVar(self, value="")
        self.z_max = tk.StringVar(self, value="")
        self.z_current = tk.StringVar(self, value="")
        self.z_min = tk.StringVar(self, value="")
        self.syringe_max = tk.StringVar(self, value="")
        self.syringe_current = tk.StringVar(self, value="")
        self.syringe_min = tk.StringVar(self, value="")

        self.x_max_label = tk.Label(self.coordinates_box, textvariable=self.x_max) 
        self.x_current_label = tk.Label(self.coordinates_box, textvariable=self.x_current)
        self.x_min_label = tk.Label(self.coordinates_box, textvariable=self.x_min)
        self.y_max_label = tk.Label(self.coordinates_box, textvariable=self.y_max)
        self.y_current_label = tk.Label(self.coordinates_box, textvariable=self.y_current)
        self.y_min_label = tk.Label(self.coordinates_box, textvariable=self.y_min)
        self.z_max_label = tk.Label(self.coordinates_box, textvariable=self.z_max) 
        self.z_current_label = tk.Label(self.coordinates_box, textvariable=self.z_current)
        self.z_min_label = tk.Label(self.coordinates_box, textvariable=self.z_min) 
        self.syringe_max_label = tk.Label(self.coordinates_box, textvariable=self.syringe_max)
        self.syringe_current_label = tk.Label(self.coordinates_box, textvariable=self.syringe_current)
        self.syringe_min_label = tk.Label(self.coordinates_box, textvariable=self.syringe_min) 

        self.x_label.grid(row=0, column=1)
        self.y_label.grid(row=0, column=2)
        self.z_label.grid(row=0, column=3)
        self.syringe_pos_label.grid(row=0, column=4)
        self.max_label.grid(row=1, column=0)
        self.current_label.grid(row=2, column=0)
        self.min_label.grid(row=3, column=0)

        self.x_max_label.grid(row=1, column=1)
        self.x_current_label.grid(row=2, column=1)
        self.x_min_label.grid(row=3, column=1)
        self.y_max_label.grid(row=1, column=2)
        self.y_current_label.grid(row=2, column=2)
        self.y_min_label.grid(row=3, column=2)
        self.z_max_label.grid(row=1, column=3)
        self.z_current_label.grid(row=2, column=3)
        self.z_min_label.grid(row=3, column=3)
        self.syringe_max_label.grid(row=1, column=4)
        self.syringe_current_label.grid(row=2, column=4)
        self.syringe_min_label.grid(row=3, column=4)

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
        self.move_string_1 = tk.StringVar(self.move_to_box)
        self.move_string_2 = tk.StringVar(self.move_to_box)
        self.move_dropbox_1 = ttk.Combobox(self.move_to_box, textvariable=self.move_string_1, values=[""], state='readonly') 
        self.move_dropbox_2 = ttk.Combobox(self.move_to_box, textvariable=self.move_string_2, values=[""], state='readonly') 
        self.move_string_1.set("")
        self.move_string_2.set("")

        self.go_button = tk.Button(self.move_to_box, text="Go", command=self.go_to_location, state="disabled") 

        self.move_dropbox_1.bind("<<ComboboxSelected>>", self.update_sub_options)
        self.move_dropbox_2.bind("<<ComboboxSelected>>", self.enable_go_button)

        self.move_dropbox_1.grid(row=0, column=0, sticky="WE")
        self.move_dropbox_2.grid(row=1, column=0, sticky="WE")
        self.go_button.grid(row=2, column=0)

        

        # tempdeck control

        self.temp_deck_control = tk.Frame(self.temp_deck_frame)
        self.temp_deck_control.pack()

        self.tempdeck_label = tk.Label(self.temp_deck_control, text="Tempdeck")
        self.selected_tempdeck = tk.StringVar(self.temp_deck_control, value="")
        tempdeck_options = list(self.coordinator.myModules.myTempDecks.keys())
        self.tempdeck_dropbox = ttk.Combobox(self.temp_deck_control, textvariable=self.selected_tempdeck, values=tempdeck_options)
        self.temperature_label = tk.Label(self.temp_deck_control, text="Temperature (C)")
        self.temperature_entry = tk.Entry(self.temp_deck_control)
        self.set_temp_button = tk.Button(self.temp_deck_control, text="Set", padx=10, command=self.set_tempdeck)
        self.tempdeck_off_button = tk.Button(self.temp_deck_control, text="Deactivate", command=self.tempdeck_off)

        self.temperature_entry.insert(tk.END, "15")

        self.tempdeck_label.pack(side="left")
        self.tempdeck_dropbox.pack(side="left")
        self.temperature_label.pack(side="left")
        self.temperature_entry.pack(side="left")
        self.set_temp_button.pack(side="left")
        self.tempdeck_off_button.pack(side="left")

        self.updating_positions = False
        self.position_thread = threading.Thread(target=self.enable_coordinates)

        self.update_options()

        self.protocol('WM_DELETE_WINDOW', self.on_closing)



    def update_step_speed(self, step_size):
        speed = self.coordinator.myModules.myStages[self.selected_stage.get()].check_speed(step_size)
        self.step_speed.set(str(speed))

    def check_step_size(self):
        step_size = self.coordinator.myModules.myStages[self.selected_stage.get()].xyz_step_size
        self.step_size.set(str(step_size))
        self.update_step_speed(step_size)

    def update_step_size(self, *args):
        step_size = int(self.step_size.get())
        self.coordinator.myModules.myStages[self.selected_stage.get()].xyz_step_size = step_size
        self.update_step_speed(step_size)

    def update_options(self):
        if self.selected_stage.get() != self.previous_selected_stage:
            self.previous_selected_stage = self.selected_stage.get()
            if not self.selected_stage.get() == "":
                # turn on position tracking
                if not self.updating_positions:
                    self.position_thread = threading.Thread(target=self.enable_coordinates)
                    self.position_thread.start()
                self.enable_xyz()
                self.enable_syringe
                self.update_move_to_options()
                
            else:
                self.disable_coordinates()
                self.disable_xyz()
                self.disable_syringe
                self.update_move_to_options()

        if not self.selected_tempdeck.get() == "":
            self.set_temp_button["state"] = "normal"
            # add current temp report
    
    def enable_coordinates(self):
        self.updating_positions = True

        stage_type = self.coordinator.myModules.myStages[self.selected_stage.get()].stage_type
        
        if stage_type == "Opentrons":
            x_max = self.coordinator.myModules.myStages[self.selected_stage.get()].x_max
            x_min = self.coordinator.myModules.myStages[self.selected_stage.get()].x_min
            y_max = self.coordinator.myModules.myStages[self.selected_stage.get()].y_max
            y_min = self.coordinator.myModules.myStages[self.selected_stage.get()].y_min
            z_max = self.coordinator.myModules.myStages[self.selected_stage.get()].z_max
            z_min = self.coordinator.myModules.myStages[self.selected_stage.get()].z_min
            syringe_max = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.get_syringe_max()
            syringe_min = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.get_syringe_min()

            self.x_max.set(str(round(x_max, 2)))
            self.x_min.set(str(round(x_min, 2)))
            self.y_max.set(str(round(y_max, 2)))
            self.y_min.set(str(round(y_min, 2)))
            self.z_max.set(str(round(z_max, 2)))
            self.z_min.set(str(round(z_min, 2)))
            self.syringe_max.set(str(round(syringe_max, 2)))
            self.syringe_min.set(str(round(syringe_min, 2)))
        
        while self.updating_positions == True:
            x,y,z = self.coordinator.myModules.myStages[self.selected_stage.get()].get_motor_coordinates()
            s = self.coordinator.myModules.myStages[self.selected_stage.get()].get_syringe_location()
            self.x_current.set(str(round(x, 2)))
            self.y_current.set(str(round(y, 2)))
            self.z_current.set(str(round(z, 2)))
            self.syringe_current.set(str(round(s, 2)))

            time.sleep(1)

            # Also check for change in driver step size
            self.check_step_size()

            # Also checck for change in syringe model
            current_syringe_model = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.get_syringe_model()
            self.syringe_model.set("Syringe Model: " + current_syringe_model)
            
            if self.updating_positions == False:
                break
            
    def disable_coordinates(self):
        self.updating_positions = False
        self.x_max.set("")
        self.x_current.set("")
        self.x_min.set("")
        self.y_max.set("")
        self.y_current.set("")
        self.y_min.set("")
        self.z_max.set("")
        self.z_current.set("")
        self.z_min.set("")
        self.syringe_max.set("")
        self.syringe_current.set("")
        self.syringe_min.set("")

    def enable_xyz(self):
        # enable joystick button
        self.update_joystick(case="reset")
        self.joy_button["state"] = "normal"
        # enable xyz 
        self.x_left["state"] = "normal"
        self.x_right["state"] = "normal"
        self.y_back["state"] = "normal"
        self.y_front["state"] = "normal"
        self.z_up["state"] = "normal"
        self.z_down["state"] = "normal"

    def disable_xyz(self):
        # enable joystick button
        self.update_joystick(case="kill")
        self.joy_button["state"] = "disabled"
        # enable xyz and syringe buttons
        self.x_left["state"] = "disabled"
        self.x_right["state"] = "disabled"
        self.y_back["state"] = "disabled"
        self.y_front["state"] = "disabled"
        self.z_up["state"] = "disabled"
        self.z_down["state"] = "disabled"

    def enable_syringe(self):
        my_syringe = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.syringe_model
        # enable syringe buttons
        if my_syringe != "Not Selected":
            self.syringe_max_button["state"] = "normal"
            self.syringe_min_button["state"] = "normal"
            self.syringe_rest_button["state"] = "normal"
            self.aspirate_button["state"] = "normal"
            self.dispense_button["state"] = "normal"
        else:
            print("No Syringe Selected. Add to Labware!")

    def disable_syringe(self):
        # enable syringe buttons
        self.syringe_max_button["state"] = "disabled"
        self.syringe_min_button["state"] = "disabled"
        self.syringe_rest_button["state"] = "disabled"
        self.aspirate_button["state"] = "disabled"
        self.dispense_button["state"] = "disabled"


    # move_to handling 
    def update_move_to_options(self):
        self.go_button["state"] = "disabled"
        
        if not self.selected_stage.get() == "":
            self.move_options_list = [""]
            self.wellplate_dict = {} # used to look up plate index from model name
            for index, plate in enumerate(self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.plate_list):
                self.move_options_list.append(str(plate.model))
                self.wellplate_dict[plate.model] = index 
        
            self.my_2_pos_valves = []
            for index, valve in enumerate(self.coordinator.myModules.my2PosValves):
                self.my_2_pos_valves.append(valve)
                option = f"{index}, 2-Position"  # first character is valve index within valve group
                self.move_options_list.append(option)

            self.my_selector_valves = []
            for index, valve in enumerate(self.coordinator.myModules.mySelectors):
                self.my_selector_valves.append(valve)
                option = f"{index}, Selector"  # first character is valve index within valve group
                self.move_options_list.append(option)


                self.move_options_list.append(option)

            self.move_options_list.insert(0, "Named Location")

        else: # reset
            self.move_options_list = [""]
            self.move_string_1.set("")
            self.update_sub_options()

        self.move_dropbox_1["values"] = self.move_options_list

    def update_sub_options(self, *args):
        if not self.selected_stage.get() == "":

            if self.move_string_1.get() == "Named Location":
                self.sub_options_list = list(self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.custom_locations.keys())

            elif "2-Position" in self.move_string_1.get():
                self.sub_options_list = ["Position A", "Position B"]   

            elif "Selector" in self.move_string_1.get():
                valve = self.my_selector_valves[self.move_string_1.get()[0]]  # retrieve valve from local list based on index
                max_position = valve.max_position  # get number of ports on selector valve

                self.sub_options_list = []   
                for index in range(0, max_position):
                    option = f"Position {index+1}"
                    self.sub_options_list.append(option)

            else:
                plate_index = self.wellplate_dict[self.move_string_1.get()]
                self.sub_options_list = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.plate_list[plate_index].nicknames

            self.sub_options_list.insert(0, "")
            self.move_dropbox_2["values"] = self.sub_options_list
        else:
            self.sub_options_list = [""]
            
        self.move_string_2.set("")

    def enable_go_button(self, *args): # gets enabled on selection of second dropbox
        if not self.move_string_2.get() == "":
            self.go_button["state"] = "normal"

    def go_to_location(self):
        if self.move_string_1.get() == "Named Location":
            location = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.custom_locations[self.move_string_2.get()]

        elif "2-Position" in self.move_string_1.get():
            valve = self.my_2_pos_valves[self.move_string_1.get()[0]]  # retrieve valve from local list based on index
            position = self.move_string_2.get()[-1]

            if position == "A":
                valve.to_runPosition()
            elif position == "B":
                valve.to_loadPosition()

        elif "Selector" in self.move_string_1.get():
            valve = self.my_selector_valves[self.move_string_1.get()[0]]  # retrieve valve from local list based on index
            position = self.move_string_2.get()[-1]
            
            valve.move_to_position(position)

        else:
            plate_index = self.wellplate_dict[self.move_string_1.get()]
            well = self.move_string_2.get()
            location: tuple = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.get_well_location(plate_index, well)
        
        self.coordinator.myModules.myStages[self.selected_stage.get()].move_to(location)

    
    # xyz moves
    def move_x_left(self):
        self.coordinator.myModules.myStages[self.selected_stage.get()].step_x_motor_left()

    def move_x_right(self):
        self.coordinator.myModules.myStages[self.selected_stage.get()].step_x_motor_right()    

    def move_y_back(self):
        self.coordinator.myModules.myStages[self.selected_stage.get()].step_y_motor_back()

    def move_y_forward(self):
        self.coordinator.myModules.myStages[self.selected_stage.get()].step_y_motor_forward()

    def move_z_up(self):
        self.coordinator.myModules.myStages[self.selected_stage.get()].step_z_motor_up()

    def move_z_down(self):
        self.coordinator.myModules.myStages[self.selected_stage.get()].step_z_motor_down()

    # Syringe methods
    def aspirate(self):
        volume = float(self.syringe_volume_entry.get())
        speed = float(self.syringe_speed_entry.get())
        self.coordinator.myLogger.info(f"Aspirating {volume} nL at speed {speed} nL/min")
        self.coordinator.myModules.myStages[self.selected_stage.get()].step_syringe_motor_up(volume=volume, speed=speed)

    def dispense(self):
        volume = float(self.syringe_volume_entry.get())
        speed = float(self.syringe_speed_entry.get())
        self.coordinator.myLogger.info(f"Dispensing {volume} nL at speed {speed} nL/min")
        self.coordinator.myModules.myStages[self.selected_stage.get()].step_syringe_motor_down(volume=volume, speed=speed)

    def syringe_to_max(self):
        speed = float(self.syringe_speed_entry.get())
        max_position = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.get_syringe_max()
        self.coordinator.myModules.myStages[self.selected_stage.get()].move_syringe_to(max_position, speed)

    def syringe_to_min(self):
        speed = float(self.syringe_speed_entry.get())
        min_position = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.get_syringe_min()
        self.coordinator.myModules.myStages[self.selected_stage.get()].move_syringe_to(min_position, speed)
    
    def syringe_to_rest(self):        
        speed = float(self.syringe_speed_entry.get())
        rest_position = self.coordinator.myModules.myStages[self.selected_stage.get()].myLabware.get_syringe_rest()
        self.coordinator.myModules.myStages[self.selected_stage.get()].move_syringe_to(rest_position, speed)

    # Joystick Methods
    def update_joystick(self, case="none"):

        if case == "reset":
            self.kill_joystick()
            if self.joystick_running == True:
                self.start_joystick()

        elif case == "kill":
            self.kill_joystick()
            self.joystick_running = False
            self.joy_label["background"] = "red"
            self.joy_on_off.set("Turn On")

        elif self.joystick_running == True:
            self.kill_joystick()
            self.joystick_running = False
            self.joy_label["background"] = "red"
            self.joy_on_off.set("Turn On")

        elif self.joystick_running == False:
            self.start_joystick()
            self.joystick_running = True
            self.joy_label["background"] = "green"
            self.joy_on_off.set("Turn Off")

    def start_joystick(self):
        self.coordinator.start_joystick(self.selected_stage.get())

    def kill_joystick(self):
        self.coordinator.stop_joystick()

    # Tempdeck Methods
    def set_tempdeck(self):
        try:
            temperature = self.temperature_entry.get()
            self.coordinator.myModules.myTempDecks[self.selected_tempdeck.get()].start_set_temperature(temperature)
        except:
            print("Tempdeck Not Responding")

    def tempdeck_off(self):
        try:
            self.coordinator.myModules.myTempDecks[self.selected_tempdeck.get()].deactivate()
        except:
            print("Tempdeck Not Responding")


    def on_closing(self):
        self.kill_joystick()
        self.destroy()
