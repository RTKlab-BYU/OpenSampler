import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
import json

from Classes.coordinator import Coordinator

'''
Method_Creator is the main class for method creation. 
Method_Command_Row is used inside Method_Creator.
Command_Parameter_is used inside Method_Command Row.
'''




ACTION_TYPES = {

"aspirate_samples": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"dispense_to_samples": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"pool_samples": ["Amount (nL)", "Speed (nL/min)", "Spread (mm)" , "Delay (s)"],

"aspirate_from_wells": ["Stage Name", "Wellplate Index", "Well", "Amount (nL)", "Speed (nL/min)"],
"dispense_to_wells": ["Stage Name", "Wellplate Index", "Wells (CS)", "Amount (nL)", "Speed (nL/min)"],
"aspirate_from_location": ["Stage Name", "Location Name", "Amount (nL)", "Speed (nL/min)"],
"dispense_to_location": ["Stage Name", "Location Name", "Amount (nL)", "Speed (nL/min)"],

"move_to_well": ["Stage Name", "Wellplate", "Well"],
"move_to_location": ["Stage Name", "Location Name"],
"aspirate_in_place": ["Stage Name", "Amount (nL)", "Speed (nL/min)"],
"dispense_in_place": ["Stage Name", "Amount (nL)", "Speed (nL/min)"],

"-": [],

"syringe_to_min": ["Stage Name","Speed (nL/min)"],
"syringe_to_max": ["Stage Name","Speed (nL/min)"],
"syringe_to_rest": ["Stage Name","Speed (nL/min)"],

"valve_to_run": ["Valve Index (Starts at zero)"],
"valve_to_load": ["Valve Index (Starts at zero)"],
"move_selector": ["Valve Index (Starts at zero)", "Port (Valve Position)"],

"wait": ["Time (s)"],
"run_sub_method": ["Method to Run (file path)"],
"set_tempdeck": ["Tempdeck Name", "Set Temperature"],

"LC_contact_closure": ["Relay (Starts at zero)"],
"MS_contact_closure": ["Relay", "Input", "Serial Port (Starts at zero)"],
"Wait_Contact_Closure": ["State of Pin", "Input", "Serial Port (Starts at zero"],
"set_pin": ["Pin", "High/Low", "Port"],

"--": [],

"set_relay_side": ["Relay (Starts at zero)","Left or Right"],
"run_sub_method_simultaneously": ["Method to Run (include folder)"],
"start_sub_method": ["Method to Run (include folder)","Thread Index (starts with 0)"],
"wait_sub_method": ["Thread Index (starts with 0)"],

}

default_stage = ""

ACTION_DEFAULTS = {

"aspirate_samples": ["", "3000", "1"],
"dispense_to_samples": ["", "3000", "1"],
"pool_samples": ["3000", "3000", "0.7" , "1"],

"aspirate_from_wells": [default_stage, "", "", "", "3000"],
"dispense_to_wells": [default_stage, "", "", "", "3000"],
"aspirate_from_location": [default_stage, "", "", "3000"],
"dispense_to_location": [default_stage, "", "", "3000"],

"move_to_well": [default_stage, "0", ""],
"move_to_location": [default_stage, ""],
"aspirate_in_place": [default_stage, "", "3000"],
"dispense_in_place": [default_stage, "", "3000"],

"-": [],

"syringe_to_min": [default_stage,"3000"],
"syringe_to_max": [default_stage,"3000"],
"syringe_to_rest": [default_stage,"3000"],

"valve_to_run": ["0"],
"valve_to_load": ["0"],
"move_selector": ["0", ""],

"wait": [""],
"run_sub_method": [""],
"set_tempdeck": ["", ""],

"LC_contact_closure": ["0"],
"MS_contact_closure": ["1", "D14", "0"],
"Wait_Contact_Closure": ["True","D14","0"],
"set_pin": ["", "High", "0"],

"--": [],

"set_relay_side": ["0","Left"],
"run_sub_method_simultaneously": ["methods/"],
"start_sub_method": ["methods/","0"],
"wait_sub_method": ["0"],

}

class Command_Parameter():

    def __init__(self, master_frame, parameter, parameter_value, parameter_index, coordinator, toplevel_frame, command_row):
        self.command_row: Method_Command_Row = command_row
        self.command_grid: tk.Frame = master_frame
        self.coordinator: Coordinator = coordinator
        self.main_frame: Method_Creator = toplevel_frame
        self.parameter_index = parameter_index
        self.row_index = self.command_row.row_index
        self.static_columns = 6
        self.parameter_var = tk.StringVar(value=parameter_value)
        self.parameter = parameter
        
        self.param_label = tk.Label(self.command_grid, text=parameter)
        self.param_label.grid(row=self.row_index, column=parameter_index*2+self.static_columns)

        if self.parameter == "Stage Name":          
            stage_options = list(self.coordinator.myModules.myStages.keys())
            self.parameter_entry = ttk.Combobox(self.command_grid, values=stage_options, textvariable=self.parameter_var)
            self.command_row.selected_stage = self.parameter_var.get()
                      
        elif self.parameter == "Location Name":
            try:
                location_options = list(self.coordinator.myModules.myStages[self.command_row.selected_stage].myLabware.custom_locations.keys())
            except:
                location_options = []
            self.parameter_entry = ttk.Combobox(self.command_grid, values=location_options, textvariable=self.parameter_var)
            
        elif parameter == "Tempdeck Name":
            tempdeck_options = list(self.coordinator.myModules.myTempDecks.keys())
            self.parameter_entry = ttk.Combobox(self.command_grid, values=tempdeck_options, textvariable=self.parameter_var)

        else:
            self.parameter_entry = tk.Entry(self.command_grid, textvariable=self.parameter_var)
        
        self.parameter_entry.grid(row=self.row_index, column=parameter_index*2+self.static_columns+1)
        self.parameter_var.trace_add("write", self.update_parameter)

        if parameter == ACTION_TYPES["run_sub_method"][0]:
            self.parameter_entry.bind('<Double-Button-1>', lambda x: self.select_method(x))

    def update_parameter(self, *args):
        if self.parameter == "Stage Name":
            self.command_row.selected_stage = self.parameter_var.get()
        self.main_frame.commands_list[self.row_index]["parameters"][self.parameter_index] = self.parameter_var.get()

    def select_method(self, event):
        filetypes = (
            ('JSON files', '*.json'),
            ('All files', '*')
        )

        file_path = fd.askopenfilename(parent=self.command_grid, title='Open a file', initialdir='methods', filetypes=filetypes)
        
        if file_path == "":  # in the event of a cancel 
            return
        
        self.parameter_var.set(file_path)


class Method_Command_Row():

    def __init__(self, master_frame, row_index, command, coordinator, toplevel_frame):
        self.row_index = row_index
        self.command_grid = master_frame
        self.main_frame: Method_Creator = toplevel_frame
        self.coordinator = coordinator
        self.selected_stage = ""
        self.insert_button = tk.Button(self.command_grid, text="Insert", command= self.InsertRow)
        self.insert_button.grid(row=self.row_index, column=0)
        self.delete_button = tk.Button(self.command_grid, text="Delete", command=self.DeleteRow)
        self.delete_button.grid(row=self.row_index, column=1)
        self.up_button = tk.Button(self.command_grid, text="Up", command=self.MoveUp)
        self.up_button.grid(row=self.row_index, column=2)
        self.down_button = tk.Button(self.command_grid, text="Down", command=self.MoveDown)
        self.down_button.grid(row=self.row_index, column=3)
        self.command_label = tk.Label(self.command_grid, text="Command Type: ")
        self.command_label.grid(row=self.row_index,column=4)
        self.type_var = tk.StringVar()
        self.type_box = ttk.Combobox(self.command_grid, state='readonly', textvariable=self.type_var)
        self.type_box.grid(row=self.row_index,column=5)
        self.type_box["values"] = [*ACTION_TYPES.keys()]
        self.type_var.set(command["type"])
        self.type_box.bind("<<ComboboxSelected>>", lambda x: self.update_command_grid())
        #first two are type
        

        if len(ACTION_TYPES[command["type"]]) == len(command["parameters"]):
            parameter_index = 0
            for parameter in ACTION_TYPES[command["type"]]:

                Command_Parameter(self.command_grid, parameter, command["parameters"][parameter_index], parameter_index, self.coordinator, self.main_frame, self)
                parameter_index += 1  # 2 columns are used for each command parameter
        else:
            print("Invalid Command! Command Parameters")

    def update_command_grid(self):
        new_type = self.type_box.get()
        
        if not self.main_frame.commands_list[self.row_index]["type"].__eq__(str(new_type)):
            self.main_frame.commands_list[self.row_index]["type"] = new_type
            self.main_frame.commands_list[self.row_index]["parameters"] = list(ACTION_DEFAULTS.get(new_type))
        self.main_frame.update_command_grid()

    def InsertRow(self):
        new_key = list(ACTION_TYPES.keys())[0]
        self.main_frame.commands_list.insert(self.row_index, {"type": new_key, "parameters": list(ACTION_DEFAULTS.get(new_key))})
        self.main_frame.update_command_grid()

    def MoveUp(self):
        row_to_move = self.main_frame.commands_list.pop(self.row_index)
        self.main_frame.commands_list.insert((self.row_index - 1), row_to_move)
        self.main_frame.update_command_grid()

    def MoveDown(self):
        row_to_move = self.main_frame.commands_list.pop(self.row_index)
        self.main_frame.commands_list.insert(abs(self.row_index + 1),row_to_move)
        self.main_frame.update_command_grid()
    
    def DeleteRow(self):
        self.main_frame.commands_list.pop(self.row_index)
        self.main_frame.update_command_grid()


class Method_Creator(tk.Toplevel,):
    

    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)
        self.coordinator = coordinator    
      
        self.title("Create a Method")

        # sets the geometry of toplevel
        self.geometry("1000x1800")
        self.state("zoomed")

        self.header_bar = tk.Frame(self)
        self.header_bar.pack(side="top")
        self.clear_button = tk.Button(self.header_bar, text="Clear", command=self.clear_command_grid)
        self.save_button = tk.Button(self.header_bar, text="Save", command=self.save_method)
        self.load_button = tk.Button(self.header_bar, text="Load", command=self.load_method)
        self.append_button = tk.Button(self.header_bar, text="Append", command=self.append_commands)
        self.clear_button.grid(row=0, column=0)
        self.save_button.grid(row=0, column=1)
        self.load_button.grid(row=0, column=2)
        self.append_button.grid(row=0, column=3)

        self.commands_list = []

        # Canvas for scrolling command grid

        self.canvas = tk.Canvas(self, width=4000, height=1800, scrollregion=(0,0,4000,1800))
        canvas_width = self.canvas.winfo_width()
        self.command_grid = tk.Frame(self.canvas, width=canvas_width)

        self.y_scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.x_scrollbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)   
        self.canvas.config(yscrollcommand=self.y_scrollbar.set, xscrollcommand=self.x_scrollbar.set)

        self.y_scrollbar.pack(side="right", fill="y")
        self.x_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(fill="both", expand=True) 

        self.command_grid_window = self.canvas.create_window((4,4), window=self.command_grid, anchor="nw", tags="self.command_grid")
        self.command_grid.bind("<Configure>", lambda event: self.reset_scroll_region(event))

        self.inner_command_grid = tk.Frame(self.command_grid)
        self.inner_command_grid.pack(fill="x", expand=True)

        self.add_row_button = tk.Button(self.command_grid, text="Add Row", command=lambda: self.add_row())
        self.add_row_button.pack(anchor="nw")

        
        self.update()
        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.command_grid_window, width = canvas_width-3)

        # Reconfigure que when reconfiguring window
        self.bind("<Configure>", lambda x: self.reset_scroll_region(x))

        # add initial row
        self.add_row()
    
    def reset_scroll_region(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.command_grid_window, width = canvas_width-4)

    def load_from_file(self):

        filetypes = (
            ('json files', '*.json'),
            ('All files', '*')
        )

        new_file = fd.askopenfile(parent=self, title='Open a file', initialdir='methods', filetypes=filetypes)

        if new_file == None:  # in the event of a cancel 
            return

        my_dict = json.load(new_file)
        return my_dict

    def load_method(self):

        my_dict = self.load_from_file()

        try:
            self.commands_list = my_dict["commands"]

            # replace old commands with current ones
            for command in self.commands_list:
                if command["type"] == "move_to_custom_location":
                    command["type"] = "move_to_location"
                elif command["type"] == "aspirate_from_well":
                    command["type"] = "aspirate_from_wells"
                elif command["type"] == "dispense_to_well":
                    command["type"] = "dispense_to_wells"
                elif command["type"] == "collect_sample":
                    command["type"] = "aspirate_samples"
                elif command["type"] == "aspirate_sample":
                    command["type"] = "aspirate_samples"
                else:
                    pass
        except:
            pass

        self.update_command_grid()

    def append_commands(self):
        
        my_dict = self.load_from_file()
        
        self.commands_list = self.commands_list + my_dict["commands"]
        for command in self.commands_list:
            if command["type"] == "move_to_custom_location":
                command["type"] = "move_to_location"
            elif command["type"] == "aspirate_from_well":
                command["type"] = "aspirate_from_wells"
            elif command["type"] == "dispense_to_well":
                command["type"] = "dispense_to_wells"
            elif command["type"] == "collect_sample":
                command["type"] = "aspirate_samples"
            elif command["type"] == "aspirate_sample":
                command["type"] = "aspirate_samples"
            else:
                pass
        
        self.update_command_grid()

    def save_method(self):
        my_dict = {}
        my_dict["commands"] = self.commands_list

        filetypes = (
            ('json files', '*.json'),
            ( 'All files', '*')
        )

        new_file = fd.asksaveasfile(parent=self, title='Save a file', initialdir='methods', filetypes=filetypes)
        
        if new_file == None:  # in the event of a cancel 
            return
        
        if new_file.name.endswith(".json"):
            new_file = new_file.name.replace(".json","") + ".json" #  but why though?
        else:
            new_file = new_file.name + ".json"
        # Create a json file
        output_file = open(new_file, "w")

        # Dump the labware dictionary into the json file
        json.dump(my_dict, output_file)
        
    
    def clear_command_grid(self):
        self.add_row_button.pack_forget()
        self.inner_command_grid.destroy()
        self.inner_command_grid = tk.Frame(self.command_grid) 
        self.inner_command_grid.pack(fill="x", expand=True)
        self.add_row_button.pack(anchor="nw")        
        self.command_rows = []
        self.commands_list = []
        self.add_row()

    def update_command_grid(self):
        self.add_row_button.pack_forget()
        self.inner_command_grid.destroy()
        self.inner_command_grid = tk.Frame(self.command_grid)
        self.inner_command_grid.pack(fill="x", expand=True)
        self.add_row_button.pack(anchor="nw")       
        self.command_rows = []
        row_index = 0
        for command in self.commands_list: 
            self.command_rows.append(Method_Command_Row(self.inner_command_grid, row_index, command, self.coordinator, self))
            row_index += 1

    def add_row(self):
        new_key = list(ACTION_TYPES.keys())[0]
        parameters = list(ACTION_DEFAULTS.get(new_key)) # if you don't make it changes the default dictionary when updated
        self.commands_list.append({"type": new_key, "parameters": parameters})
        self.update_command_grid()
