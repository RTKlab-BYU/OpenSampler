import tkinter as tk
from tkinter import ttk



class Nickname_Selection(tk.Toplevel,):
    '''
    UPDATE: This class has been removed from use, will delete after confirming with Kei.

    This Class is used to give wellplate wells nicknames. i.e. "Buffer A" for well A1.
    The nomenclature is currently confusing as there are also "custom locations" that are not bound to a wellplate,
    which were previously also known as "nicknames, and may still be in some parts of the code.
    Despite being created in 2 different ways, they are stored in the same list...
    '''
    def __init__(self, coordinator, stage):
        tk.Toplevel.__init__(self)    
      
        self.title("Nickname Well")
        self.geometry("500x500")
        self.my_labware = coordinator.myModules.myStages[stage].myLabware
        self.my_stage = coordinator.myModules.myStages[stage]

        self.loaded_labware = self.compile_labware_list()
        
        tk.Label(self, text="New Name",justify=tk.LEFT).pack(side=tk.TOP)
        self.newNickname = tk.Entry(self)
        self.newNickname.pack(side=tk.TOP)

        optionsBar = tk.Frame(self)
        optionsBar.pack(side=tk.TOP)
        tk.Label(optionsBar, text="Wellplate",justify=tk.LEFT).grid(row=0,column=0)
        tk.Label(optionsBar, text="Well",justify=tk.LEFT).grid(row=0,column=1)

        self.labware_dropdown = ttk.Combobox(optionsBar, state='readonly')
        self.labware_dropdown.grid(row=1,column=0)
        self.labware_dropdown["values"] = [*self.loaded_labware]
    
        self.wellName = tk.Entry(optionsBar)
        self.wellName.grid(row=1,column=1)

        tk.Button(self,text="Create Custom Location",command=lambda: self.CreateNickname(),justify=tk.LEFT).pack(side=tk.TOP)
    
    def compile_labware_list(self):
        i = 0
        new_list = []
        for each_plate in self.my_labware.plate_list:
            new_list.append(str(i) + ": " + each_plate.model)
            i = i + 1
        return new_list


    def CreateNickname(self):
        name = self.newNickname.get()
        location = self.my_stage.get_motor_coordinates()
        self.my_labware.add_custom_location(name, location)
        self.destroy()