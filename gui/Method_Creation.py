import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
import json

ACTION_TYPES = {
"dispense_to_sample": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"dispense_to_samples": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"collect_sample": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"collect_samples": ["Amount (nL)", "Speed (nL/min)", "Delay (s)"],
"aspirate_from_well": ["Stage Name", "Wellplate Index", "Well", "Amount (nL)", "Speed (nL/min)"],
"dispense_to_well": ["Stage Name", "Wellplate Index", "Well", "Amount (nL)", "Speed (nL/min)"],
"dispense_to_wells": ["Stage Name", "Wellplate Index", "Wells (CS)", "Amount (nL)", "Speed (nL/min)"],
"syringe_to_min": ["Stage Name","Speed (nL/min)"],
"syringe_to_max": ["Stage Name","Speed (nL/min)"],
"syringe_to_rest": ["Stage Name","Speed (nL/min)"], #need for step LC only and make version for no selector
"move_to_custom_location": ["Stage Name", "Location Name"],
"move_to_well": ["Stage Name", "Wellplate", "Well"],
"run_sub_method": ["Method to Run (file path)"],
"run_sub_method_simultaneously": ["Method to Run (include folder)"],
"start_sub_method": ["Method to Run (include folder)","Thread Index (starts with 0)"],
"wait_sub_method": ["Thread Index (starts with 0)"],
"aspirate_in_place": ["Stage Name", "Amount (nL)", "Speed (nL/min)"],
"dispense_in_place": ["Stage Name", "Amount (nL)", "Speed (nL/min)"],
"wait": ["Time (s)"],
"valve_to_run": ["Valve Index (Starts at zero)"],
"valve_to_load": ["Valve Index (Starts at zero)"],
"move_selector": ["Valve Index (Starts at zero)", "Port (Valve Position)"],
"LC_contact_closure": ["Relay (Starts at zero)"],
"MS_contact_closure": ["Relay", "Input", "Serial Port (Starts at zero)"],
"Wait_Contact_Closure": ["State of Pin", "Input", "Serial Port (Starts at zero"],
"set_relay_side": ["Relay (Starts at zero)","Left or Right"],
"set_tempdeck": ["TempDeck Name", "Set Temperature"],
}

default_stage = ""

ACTION_DEFAULTS = {
"dispense_to_sample": ["", "3000", "1"],
"dispense_to_samples": ["", "3000", "1"],
"collect_sample": ["", "3000", "1"],
"collect_samples": ["", "3000", "1"],
"aspirate_from_well": [default_stage, "", "", "", "3000"],
"dispense_to_well": [default_stage, "", "", "", "3000"],
"dispense_to_wells": [default_stage, "", "", "", "3000"],
"syringe_to_min": [default_stage,"3000"],
"syringe_to_max": [default_stage,"3000"],
"syringe_to_rest": [default_stage,"3000"],
"move_to_custom_location": [default_stage, ""],
"move_to_well": [default_stage, "0", ""],
"run_sub_method": [""],
"run_sub_method_simultaneously": ["methods/"],
"start_sub_method": ["methods/","0"],
"wait_sub_method": ["0"],
"aspirate_in_place": [default_stage,"","3000"],
"dispense_in_place": [default_stage,"","3000"],
"wait": [""],
"valve_to_run": ["0"],
"valve_to_load": ["0"],
"move_selector": ["0", ""],
"LC_contact_closure": ["0"],
"MS_contact_closure": ["1", "D14", "0"],
"Wait_Contact_Closure": ["True","D14","0"],
"set_relay_side": ["0","Left"],
"set_tempdeck": ["", ""],
}

class Protocol_Parameter_Instance(tk.Frame,):
    def __init__(self, frame, value_name, value, row, column):
        index = int(column/2) #column changes by two each time
        self.master_frame: Method_Creator = frame
        #print(index)

        self.value_name = value_name
        this_type = self.master_frame.commands_list[row]["type"]
        # print(index)
        tk.Label(self.master_frame.command_grid, text=ACTION_TYPES[this_type][index]).grid(row=row, column=column + 6)
        self.this_valuebox = tk.Entry(self.master_frame.command_grid)
        self.this_valuebox.insert(tk.END,string=value)
        self.this_valuebox.grid(row=row,column=column + 7)
        self.this_valuebox.bind('<FocusOut>',lambda x: self.UpdateParameter(self.master_frame, row, index))
        
    def UpdateParameter(self, frame, row, index):
        self.master_frame.commands_list[row]["parameters"][index] = self.this_valuebox.get()


class Protocol_Row(tk.Frame,):
    def __init__(self, frame, row, command):
        self.master_frame: Method_Creator = frame
        self.row = row
        self.protocol_parameters = command["parameters"]
        tk.Button(self.master_frame.command_grid, text="Insert", command=lambda: self.InsertRow(self.master_frame)).grid(row=self.row, column=0)
        tk.Button(self.master_frame.command_grid, text="Delete", command=lambda: self.DeleteRow(self.master_frame)).grid(row=self.row, column=1)
        tk.Button(self.master_frame.command_grid, text="Up", command=lambda: self.MoveUp(self.master_frame)).grid(row=self.row, column=2)
        tk.Button(self.master_frame.command_grid, text="Down", command=lambda: self.MoveDown(self.master_frame)).grid(row=self.row, column=3)
        tk.Label(self.master_frame.command_grid, text="Command Type: ").grid(row=self.row,column=4)
        self.type_box = ttk.Combobox(self.master_frame.command_grid, state='readonly')
        self.type_box.grid(row=self.row,column=5)
        self.type_box["values"] = [*ACTION_TYPES.keys()]
        self.type_box.set(command["type"])
        self.type_box.bind("<<ComboboxSelected>>", lambda x: self.UpdateCommandGrid(self.master_frame, self.row))
        #first two are type
        if len(ACTION_TYPES[command["type"]]) == len(self.protocol_parameters):
            i = 0
            for eachParameter in ACTION_TYPES[command["type"]]:
                #print(command)
                Protocol_Parameter_Instance(self.master_frame, eachParameter, command["parameters"][int(i/2)], self.row, i )
                i = i + 2
        else:
            for eachParameter in list(ACTION_DEFAULTS.get(command["type"])[len(self.protocol_parameters):]):
                command["parameters"].append(eachParameter)
                self.protocol_parameters = command["parameters"]
            i = 0
            for eachParameter in self.protocol_parameters:
                #print(command)
                Protocol_Parameter_Instance(self.master_frame, eachParameter, command["parameters"][int(i/2)], self.row, i )
                i = i + 2




    def UpdateCommandGrid(self, frame, row):
        new_type = self.type_box.get()
        frame: Method_Creator = frame

        if not frame.commands_list[row]["type"].__eq__(str(new_type)):
            #print("different")
            frame.commands_list[row]["type"] = new_type
            frame.commands_list[row].pop("parameters")
            frame.commands_list[row]["parameters"] = list(ACTION_DEFAULTS.get(new_type))
        frame.UpdateCommandGrid()

    def InsertRow(self, frame):
        new_key = list(ACTION_TYPES.keys())[0]
        self.master_frame.commands_list.insert(self.row, {"type": new_key, "parameters": list(ACTION_DEFAULTS.get(new_key))})
        self.master_frame.UpdateCommandGrid()

    def MoveUp(self, frame):
        row_to_move = self.master_frame.commands_list.pop(self.row)
        self.master_frame.commands_list.insert(abs(self.row - 1),row_to_move)
        self.master_frame.UpdateCommandGrid()

    def MoveDown(self, frame):
        row_to_move = frame.commands_list.pop(self.row)
        self.master_frame.commands_list.insert(abs(self.row + 1),row_to_move)
        self.master_frame.UpdateCommandGrid()

    def DeleteRow(self, frame):
        self.master_frame.commands_list.pop(self.row)
        self.master_frame.UpdateCommandGrid()

class Method_Creator(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Create a Method")
        # sets the geometry of toplevel
        self.geometry("1000x1800")
        self.state("zoomed")

        self.header_bar = tk.Frame(self)
        self.header_bar.pack(side=tk.TOP)
        tk.Button(self.header_bar, text="Save Method", command=self.save_method).grid(row=0, column=0)
        tk.Button(self.header_bar, text="Load Method", command=self.load_method).grid(row=0, column=1)
        tk.Button(self.header_bar, text="Add to Method", command=self.append_commands).grid(row=0, column=2)        

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

    def LoadFromFile(self, file):

        # Create a dictionary out of the data in the specified json file
        labware_dictionary = json.load(file)

        return labware_dictionary

    def load_method(self):

        filetypes = (
            ('json files', '*.json'),
            ('All files', '*')
        )

        new_file = fd.askopenfile(parent=self, title='Open a file', initialdir='methods', filetypes=filetypes)
        
        if new_file == None:  # in the event of a cancel 
            return

        my_dict = self.LoadFromFile(new_file)

        self.commands_list = my_dict["commands"]

        self.UpdateCommandGrid()

    def append_commands(self):
        filetypes = (
            ('json files', '*.json'),
            ('All files', '*')
        )

        new_file = fd.askopenfile(parent=self, title='Open a file', initialdir='methods', filetypes=filetypes)
        
        if new_file == None:  # in the event of a cancel 
            return
        else:
            print(new_file)

        my_dict = self.LoadFromFile(new_file)
        
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
        self.cow = []
        i = 0
        for eachCommand in self.commands_list:
            self.cow.append(Protocol_Row(self, i, eachCommand))
            i = i + 1

        tk.Button(self.command_grid, text="Add Row", command=lambda: self.AddRow(i)).grid(row=i, column=1)

    def AddRow(self, row):
        new_key = list(ACTION_TYPES.keys())[0]
        parameters = list(ACTION_DEFAULTS.get(new_key)) # if you don't make it changes the default dictionary when updated
        self.commands_list.append({"type": new_key, "parameters": parameters})
        self.UpdateCommandGrid()
