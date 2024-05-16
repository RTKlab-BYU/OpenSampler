import tkinter as tk
from tkinter import filedialog
import json
LABWARE_PARAMETERS = ["wellplate_wellDistance","well_depth","fiducialDisplacement"]
LABWARE_PARAM_DEFAULTS = {"wellplate_wellDistance": "0","well_depth": "0","fiducialDisplacement": "0"}

LABWARE_GRID_PARAM_NAME = "grid"
LABWARE_WELLS_PARAM_NAME = "nicknames"

class Labware_Parameter_Instance():
    def __init__(self, frame, value_name, value, row):     
        self.value_name = value_name
        self.value = value
        tk.Label(frame.model_grid, text=value_name).grid(row=row, column=0)
        self.this_valuebox = tk.Entry(frame.model_grid)
        self.this_valuebox.insert(tk.END,string=self.value)
        self.this_valuebox.grid(row=row,column=1)
        self.this_valuebox.bind('<FocusOut>',lambda x: self.UpdateParameter(frame,value_name))
    def UpdateParameter(self, frame, parameter_name):
        self.value = self.this_valuebox.get()
        frame.new_model[parameter_name] = self.value

class Labware_Wells_Instance():
    def __init__(self, frame, row):
        tk.Label(frame.well_grid,text="Row Names, separated by commas, no spaces").grid(row=row, column=0)
        self.row_valuebox = tk.Entry(frame.well_grid)
        self.row_valuebox.insert(tk.END,string="")
        self.row_valuebox.grid(row=row,column=1)
        self.row_valuebox.bind('<FocusOut>',lambda x: self.UpdateWells(frame))
        tk.Label(frame.well_grid,text="column_Grid Names, separated by commas, no spaces").grid(row=row, column=2)
        self.col_valuebox = tk.Entry(frame.well_grid)
        self.col_valuebox.insert(tk.END,string="")
        self.col_valuebox.grid(row=row,column=3)
        self.col_valuebox.bind('<FocusOut>',lambda x: self.UpdateWells(frame))

    def UpdateWells(self, frame):
        rows = self.row_valuebox.get().split(",")
        num_rows = len(rows)
        cols = self.col_valuebox.get().split(",")
        num_cols = len(cols)
        frame.new_model[LABWARE_GRID_PARAM_NAME] = [num_rows,num_cols]
        wellnames = []
        for eachRow in rows:
            current = []
            for eachCol in cols:
                well = eachRow + eachCol
                current.append(well)
            wellnames.append(current)
        frame.new_model[LABWARE_WELLS_PARAM_NAME] = wellnames

        frame.Update_Well_Preview()
        

        

class Create_Labware(tk.Toplevel,):
    def __init__(self):
        tk.Toplevel.__init__(self)    
      
        self.title("Create Labware Model")
        self.geometry("1000x1000")
        self.model_grid = tk.Frame(self)
        self.model_grid.pack(side=tk.TOP)
        self.params = []
        self.new_model = {}
        i = 0
        for eachparameter in LABWARE_PARAMETERS:
            self.new_model[eachparameter] = LABWARE_PARAM_DEFAULTS[eachparameter]
            self.params.append(Labware_Parameter_Instance(self,eachparameter,LABWARE_PARAM_DEFAULTS[eachparameter], i))
            i = i + 1
        self.well_grid = tk.Frame(self)
        self.well_grid.pack(side=tk.TOP)
        self.preview_box = tk.Frame(self)
        self.preview_box.pack(side=tk.TOP)
        self.well_params = Labware_Wells_Instance(self, i)
        self.Save_Button = tk.Button(self.well_grid,text="Save",command=self.Save_Wells)
        self.Save_Button.grid(row=i+1,column=0)
        self.Save_Button["state"] = "disabled"

    def Update_Well_Preview(self):
        self.preview_box.destroy()
        self.preview_box = tk.Frame(self)
        self.preview_box.pack(side=tk.TOP)
        self.Populate_Well_Preview()
    
    def Populate_Well_Preview(self):
        i = 0
        self.Save_Button["state"] = "disabled"
        added_wells = []
        all_unique = True
        for eachRow in self.new_model[LABWARE_WELLS_PARAM_NAME]:
            j = 0
            for eachWell in eachRow:
                tk.Label(self.preview_box,text=eachWell).grid(row=i,column=j)
                j = j + 1
                if eachWell not in added_wells:
                    added_wells.append(eachWell)
                else:
                    all_unique = False
            i = i + 1
        if all_unique:
            self.Save_Button["state"] = "normal"
            

    def Save_Wells(self):
        filetypes = (
            ('json files', '*.json'),
            ( 'All files', '*')
        )

        all_numeric = True
        for each_parameter in LABWARE_PARAMETERS:
            try:
                self.new_model[each_parameter] = float(self.new_model[each_parameter])
            except:
                all_numeric = False

        if all_numeric:
            new_file = filedialog.asksaveasfile(parent=self, title='Save a file', initialdir='models/plates', filetypes=filetypes)
        
            if new_file == None:  # in the event of a cancel 
                return
        
            if new_file.name.endswith(".json"):
                new_file = new_file.name.replace(".json","") + ".json"
            else:
                new_file = new_file.name + ".json"

            output_file = open(new_file, "w")
        
                
            json.dump(self.new_model,output_file)
        else:
            print("ERROR: not all numeric")
        
        


