import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
import json

ACTION_TYPES = {

"move_to_well": ["Stage Name", "Wellplate", "Well"],
"move_to_location": ["Stage Name", "Location Name"],
"aspirate_in_place": ["Stage Name", "Amount (nL)", "Speed (nL/min)"],
"dispense_in_place": ["Stage Name", "Amount (nL)", "Speed (nL/min)"],

"aspirate_from_wells": ["Stage Name", "Wellplate Index", "Well", "Amount (nL)", "Speed (nL/min)"],
"aspirate_from_location": ["Stage Name", "Location Name", "Amount (nL)", "Speed (nL/min)"],
"dispense_to_wells": ["Stage Name", "Wellplate Index", "Wells (CS)", "Amount (nL)", "Speed (nL/min)"],
"dispense_to_location": ["Stage Name", "Location Name", "Amount (nL)", "Speed (nL/min)"],

"syringe_to_min": ["Stage Name","Speed (nL/min)"],
"syringe_to_max": ["Stage Name","Speed (nL/min)"],
"syringe_to_rest": ["Stage Name","Speed (nL/min)"],

"valve_to_run": ["Valve Index (Starts at zero)"],
"valve_to_load": ["Valve Index (Starts at zero)"],
"move_selector": ["Valve Index (Starts at zero)", "Port (Valve Position)"],

"LC_contact_closure": ["Relay (Starts at zero)"],
"MS_contact_closure": ["Relay", "Input", "Serial Port (Starts at zero)"],

"wait": ["Time (s)"],
"run_sub_method": ["Method to Run (file path)"],
"set_tempdeck": ["Tempdeck Name", "Set Temperature"],

"aspirate_sample": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"aspirate_samples": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"dispense_to_sample": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"dispense_to_samples": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],

"Wait_Contact_Closure": ["State of Pin", "Input", "Serial Port (Starts at zero"],
"set_relay_side": ["Relay (Starts at zero)","Left or Right"],
"run_sub_method_simultaneously": ["Method to Run (include folder)"],
"start_sub_method": ["Method to Run (include folder)","Thread Index (starts with 0)"],
"wait_sub_method": ["Thread Index (starts with 0)"],

}

default_stage = ""

ACTION_DEFAULTS = {

"move_to_well": [default_stage, "0", ""],
"move_to_location": [default_stage, ""],
"aspirate_in_place": [default_stage, "", "3000"],
"dispense_in_place": [default_stage, "", "3000"],

"aspirate_from_wells": [default_stage, "", "", "", "3000"],
"aspirate_from_location": [default_stage, "", "", "3000"],
"dispense_to_wells": [default_stage, "", "", "", "3000"],
"dispense_to_location": [default_stage, "", "", "3000"],

"syringe_to_min": [default_stage,"3000"],
"syringe_to_max": [default_stage,"3000"],
"syringe_to_rest": [default_stage,"3000"],

"valve_to_run": ["0"],
"valve_to_load": ["0"],
"move_selector": ["0", ""],

"LC_contact_closure": ["0"],
"MS_contact_closure": ["1", "D14", "0"],

"wait": [""],
"run_sub_method": [""],
"set_tempdeck": ["", ""],

"dispense_to_sample": ["", "3000", "1"],
"dispense_to_samples": ["", "3000", "1"],
"collect_sample": ["", "3000", "1"],
"collect_samples": ["", "3000", "1"],

"Wait_Contact_Closure": ["True","D14","0"],
"set_relay_side": ["0","Left"],
"run_sub_method_simultaneously": ["methods/"],
"start_sub_method": ["methods/","0"],
"wait_sub_method": ["0"],

}

class Command_Parameter():

    def __init__(self, frame, parameter, default_value, row_index, parameter_index):
        self.master_frame: Method_Command_Row = frame
        self.parameter_index = parameter_index
        self.row_index = row_index
        self.static_columns = 6
        self.parameter_var = tk.StringVar()
        self.parameter = parameter
        
        self.param_label = tk.Label(self.master_frame.command_grid, text=parameter)
        self.param_label.grid(row=row_index, column=parameter_index*2+self.static_columns)
        if self.parameter == "Stage Name":
            # pass
            stage_options = list(self.master_frame.coordinator.myModules.myStages.keys())
            self.parameter_entry = ttk.Combobox(self.master_frame, values=stage_options, textvariable=self.parameter_var)
        elif parameter == "Location Name":
            # pass
            location_options = list(self.master_frame.coordinator.myModules.myStages[self.selected_stage].myLabware.custom_locations.keys())
            self.parameter_entry = ttk.Combobox(self.master_frame, values=location_options, textvariable=self.parameter_var)
        elif parameter == "Tempdeck Name":
            # pass
            tempdeck_options = list(self.master_frame.coordinator.myModules.myTempDecks.keys())
            self.parameter_entry = ttk.Combobox(self.master_frame, values=tempdeck_options, textvariable=self.parameter_var)
        else:
            self.parameter_entry = tk.Entry(self.master_frame.command_grid, textvariable=self.parameter_var)
        
        # self.parameter_entry = tk.Entry(self.master_frame.command_grid, textvariable=self.parameter_var)
        
        self.parameter_entry.insert(tk.END,string=default_value)
        self.parameter_entry.grid(row=row_index, column=parameter_index*2+self.static_columns+1)
        self.parameter_var.trace_add("write", self.UpdateParameter())

        if parameter == ACTION_TYPES["run_sub_method"][0]:
            self.parameter_entry.bind('<Double-Button-1>', lambda x: self.select_method(x))

    def UpdateParameter(self):
        if self.parameter == "Stage Name":
            self.master_frame.selected_stage = self.parameter_entry.get()
        self.master_frame.commands_list[self.row_index]["parameters"][self.parameter_index] = self.parameter_var.get()

    def select_method(self, event):
        filetypes = (
            ('JSON files', '*.json'),
            ('All files', '*')
        )

        file_path = fd.askopenfilename(parent=self, title='Open a file', initialdir='methods', filetypes=filetypes)
        
        if file_path == "":  # in the event of a cancel 
            return
        
        self.parameter_var.set(file_path)


class Method_Command_Row():

    def __init__(self, frame, row_index, command):
        self.row = row_index
        self.master_frame = frame
        self.coordinator = self.master_frame.coordinator
        self.selected_stage = ""
        self.insert_button = tk.Button(self.master_frame.command_grid, text="Insert", command= self.InsertRow)
        self.insert_button.grid(row=self.row, column=0)
        self.delete_button = tk.Button(self.master_frame.command_grid, text="Delete", command=self.DeleteRow)
        self.delete_button.grid(row=self.row, column=1)
        self.up_button = tk.Button(self.master_frame.command_grid, text="Up", command=self.MoveUp)
        self.up_button.grid(row=self.row, column=2)
        self.down_button = tk.Button(self.master_frame.command_grid, text="Down", command=self.MoveDown)
        self.down_button.grid(row=self.row, column=3)
        self.command_label = tk.Label(self.master_frame.command_grid, text="Command Type: ")
        self.command_label.grid(row=self.row,column=4)
        self.type_box = ttk.Combobox(self.master_frame.command_grid, state='readonly')
        self.type_box.grid(row=self.row,column=5)
        self.type_box["values"] = [*ACTION_TYPES.keys()]
        self.type_box.set(command["type"])
        self.type_box.bind("<<ComboboxSelected>>", lambda x: self.UpdateCommandGrid())
        #first two are type
        if len(ACTION_TYPES[command["type"]]) == len(command["parameters"]):
            parameter_index = 0
            for parameter in ACTION_TYPES[command["type"]]:

                Command_Parameter(self.master_frame, parameter, command["parameters"][parameter_index], self.row, parameter_index)
                parameter_index += 1  # 2 columns are used for each command parameter
        else:
            print("Invalid Command! Command Parameters")

    def UpdateCommandGrid(self):
        new_type = self.type_box.get()
        
        if not self.master_frame.commands_list[self.row]["type"].__eq__(str(new_type)):
            #print("different")
            self.master_frame.commands_list[self.row]["type"] = new_type
            self.master_frame.commands_list[self.row]["parameters"] = list(ACTION_DEFAULTS.get(new_type))
        self.master_frame.UpdateCommandGrid()

    def InsertRow(self):
        new_key = list(ACTION_TYPES.keys())[0]
        self.master_frame.commands_list.insert(self.row, {"type": new_key, "parameters": list(ACTION_DEFAULTS.get(new_key))})
        self.master_frame.UpdateCommandGrid()

    def MoveUp(self):
        row_to_move = self.master_frame.commands_list.pop(self.row)
        self.master_frame.commands_list.insert(abs(self.row - 1),row_to_move)
        self.master_frame.UpdateCommandGrid()

    def MoveDown(self):
        row_to_move = self.master_frame.commands_list.pop(self.row)
        self.master_frame.commands_list.insert(abs(self.row + 1),row_to_move)
        self.master_frame.UpdateCommandGrid()
    
    def DeleteRow(self):
        self.master_frame.commands_list.pop(self.row)
        self.master_frame.UpdateCommandGrid()

class Method_Creator(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)
        self.coordinator = coordinator    
      
        self.title("Create a Method")

        # sets the geometry of toplevel
        self.geometry("1000x1800")
        self.state("zoomed")

        self.header_bar = tk.Frame(self)
        self.header_bar.pack(side=tk.TOP)
        tk.Button(self.header_bar, text="Save Method", command=self.save_method).grid(row=0, column=0)
        tk.Button(self.header_bar, text="Load Method", command=self.load_method).grid(row=0, column=1)
        tk.Button(self.header_bar, text="Append Commands", command=self.append_commands).grid(row=0, column=2)        

        self.commands_list = []

        self.scrollbar = tk.Scrollbar(self, orient="vertical")
        self.scrollbar.pack( side = tk.RIGHT, fill = tk.Y )
        
        self.xscrollbar = tk.Scrollbar(self, orient="horizontal")
        self.xscrollbar.pack(side = tk.BOTTOM, fill = tk.X)

        self.Canv = tk.Canvas(self, width=4000, height = 1800,
                         scrollregion=(0,0,4000,1800)) #width=1256, height = 1674)
        self.Canv.pack(fill="both", expand=True) #added sticky

        self.command_grid = tk.Frame(self.Canv)
        self.command_grid.bind(
            "<Configure>",
            lambda e: self.Canv.configure(
                scrollregion=self.Canv.bbox("all")
            )
        )
        interior_id = self.Canv.create_window((0, 0), window=self.command_grid,
                                           anchor=tk.NW)
        self.Canv.config(yscrollcommand = self.scrollbar.set,xscrollcommand = self.xscrollbar.set)
        self.xscrollbar.config()
        self.scrollbar.config(command=self.Canv.yview)
        self.rowconfigure(0, weight=1) 
        self.columnconfigure(0, weight=1)

        self.UpdateCommandGrid()
    
    def reset_scrollregion(self, event):
        self.Canv.configure(scrollregion=self.Canv.bbox("all"))
        #print("Resized")

    def LoadFromFile(self):

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

        my_dict = self.LoadFromFile()

        self.commands_list = my_dict["commands"]

        self.UpdateCommandGrid()

    def append_commands(self):
        
        my_dict = self.LoadFromFile()
        
        self.commands_list = self.commands_list + my_dict["commands"]
        
        self.UpdateCommandGrid()

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
        
    def UpdateCommandGrid(self):
        self.Canv.destroy()
        self.Canv = tk.Canvas(self, width=1000, height = 1800,
                         scrollregion=(0,0,1000,1800)) #width=1256, height = 1674)
        self.Canv.pack(fill="both", expand=True) #added sticky

        self.command_grid = tk.Frame(self.Canv)
        
        self.PopulateCommandGrid()
        self.command_grid.bind(
            "<Configure>",
            self.reset_scrollregion
        )
        # interior_id = self.Canv.create_window((0, 0), window=self.command_grid,
        #                                    anchor=tk.NW)
     
        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.Canv.config(xscrollcommand = self.xscrollbar.set)
        self.xscrollbar.config(command=self.Canv.xview)
        
    def PopulateCommandGrid(self):        
        self.command_grid = tk.Frame(self.Canv)
        self.command_grid.pack(side=tk.TOP)
        self.command_rows = []
        row_index = 0
        for command in self.commands_list:
            self.command_rows.append(Method_Command_Row(row_index, command))
            row_index += 1

        tk.Button(self.command_grid, text="Add Row", command=lambda: self.add_row(row_index)).grid(row=row_index, column=1)

    def add_row(self, row):
        new_key = list(ACTION_TYPES.keys())[0]
        parameters = list(ACTION_DEFAULTS.get(new_key)) # if you don't make it changes the default dictionary when updated
        self.commands_list.append({"type": new_key, "parameters": parameters})
        self.UpdateCommandGrid()
