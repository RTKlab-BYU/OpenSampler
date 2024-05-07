import json
import os
import tkinter as tk
from tkinter import ttk, filedialog
from serial.tools import list_ports
from gui.Advanced_Settings import Configuration


DEFAULT_SETTINGS = "settings/default_settings.json"
LAST_SETTINGS = "settings/last_settings.json"
ADDITIONAL_MODULE_TYPES = []
DEFAULT_LIST_NAMES = ["ports","2_position_actuators", "selector_actuators","relays","switches","feedbacks"]
DEFAULT_DICT_NAMES = ["motors_configurations","temp_decks"]
DEFAULT_MOTOR_SETTINGS = {"port":"","motors":{"x":["","",""],"y":["","",""],"z":["","",""]},"syringes":{"s":["","",""]},"side":"","type":"","joystick":{}}


class PortRow(tk.Frame,):
    def __init__(self, frame, container, portIndex, rowNum):
        super().__init__(frame.portsGrid)
        ttk.Label(frame.portsGrid, text=portIndex).grid(row=rowNum,column=0)
        self.com_box = ttk.Combobox(frame.portsGrid, state='readonly')
        self.com_box.grid(row=rowNum,column=1)
        self.com_box["values"] = [*container.com_dict.keys()]
        current_com = container.loaded_settings["ports"][portIndex]["pattern"]
        if current_com in container.rev_com_dict.keys():
            self.com_box.set(container.rev_com_dict[current_com])
        self.com_box.bind("<<ComboboxSelected>>", lambda x: self.UpdatePort(container, portIndex))
        
        
    def UpdatePort(self, container, portIndex):
        new_port = container.com_dict[self.com_box.get()]
        container.loaded_settings["ports"][portIndex]["pattern"] = new_port

class Serial_Ports(tk.Frame,):
    def __init__(self, container):
        super().__init__(container)
        self.PopulatePorts(container)

    def PopulatePorts(self, container):
        self.portsGrid = tk.Frame(self)
        self.portsGrid.pack(side=tk.TOP)
        tk.Label(self.portsGrid, text="Serial I/O Ports", font="Helvetica 16",justify=tk.LEFT).grid(row=0,column=0)
        self.myPorts = []
        i = 2

        tk.Label(self.portsGrid, text="Serial Port Name", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
        tk.Label(self.portsGrid, text="COM Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)

        portIndex = 0
        for eachPort in container.loaded_settings.get("ports"):
            self.myPorts.append(PortRow(self, container, portIndex, i))
            portIndex = portIndex + 1
            i = i + 1
    

class MotorSeriesRow(tk.Frame,):
    def __init__(self, frame, container, coordinator, currentMotorSeries, rowNum):
        super().__init__(frame.motorsGrid)
        ttk.Label(frame.motorsGrid, text=currentMotorSeries).grid(row=rowNum,column=0)
        self.com_box = ttk.Combobox(frame.motorsGrid, state='readonly')
        self.com_box.grid(row=rowNum,column=1)
        ttk.Button(frame.motorsGrid,text="Home All Motors",command=lambda: self.HomeMotors(coordinator, currentMotorSeries)).grid(row=rowNum,column=2)
        self.com_box["values"] = [*container.com_dict.keys()]
        current_com = container.loaded_settings["motors_configurations"][currentMotorSeries]["port"]
        if current_com in container.rev_com_dict.keys():
            self.com_box.set(container.rev_com_dict[current_com])
        self.com_box.bind("<<ComboboxSelected>>", lambda x: self.UpdatePort(container, currentMotorSeries))
        
        
    def UpdatePort(self, container, currentMotorSeries):
        new_port = container.com_dict[self.com_box.get()]
        container.loaded_settings["motors_configurations"][currentMotorSeries]["port"] = new_port
    
    def HomeMotors(self, coordinator, currentMotorSeries):
        coordinator.myModules.myStages[currentMotorSeries].home_all()

class MotorSeries(tk.Frame,):
    def __init__(self, container, coordinator):
        super().__init__(container)
        self.PopulateMotors(container,coordinator)

    def PopulateMotors(self, container,coordinator):
        self.motorsGrid = tk.Frame(self)
        self.motorsGrid.pack(side=tk.TOP)
        tk.Label(self.motorsGrid, text="Liquid Handlers", font="Helvetica 16",justify=tk.LEFT).grid(row=0,column=0)
        self.myMotors = []
        i = 2

        tk.Label(self.motorsGrid, text="Liquid Handler Name", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
        tk.Label(self.motorsGrid, text="COM Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)

        for eachHandler in container.loaded_settings.get("motors_configurations"):
            self.myMotors.append(MotorSeriesRow(self, container, coordinator, eachHandler, i))
            i = i + 1

    
class TempDeckRow(tk.Frame,):
    def __init__(self, frame, container, deckname, rowNum):
        super().__init__(frame.decksGrid)
        ttk.Label(frame.decksGrid, text=deckname+":").grid(row=rowNum,column=0)
        self.com_box = ttk.Combobox(frame.decksGrid, state='readonly')
        self.com_box.grid(row=rowNum,column=1)
        self.com_box["values"] = [*container.com_dict.keys()]
        current_com = container.loaded_settings["temp_decks"][deckname]["com"]
        if current_com in container.rev_com_dict.keys():
            self.com_box.set(container.rev_com_dict[current_com])
        self.com_box.bind("<<ComboboxSelected>>", lambda x: self.UpdatePort(container, deckname))
        
        
    def UpdatePort(self, container, deckname):
        new_port = container.com_dict[self.com_box.get()]
        container.loaded_settings["temp_decks"][deckname]["com"] = new_port

class TempDecks(tk.Frame,):
    def __init__(self, container):
        super().__init__(container)
        self.PopulateDecks(container)

    def PopulateDecks(self, container):
        self.decksGrid = tk.Frame(self)
        self.decksGrid.pack(side=tk.TOP)
        tk.Label(self.decksGrid, text="Temp Decks", font="Helvetica 16",justify=tk.LEFT).grid(row=0,column=0)
        self.myDecks = []
        i = 2

        tk.Label(self.decksGrid, text="Temp Deck Name", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
        tk.Label(self.decksGrid, text="COM Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)

        for eachDeck in container.loaded_settings.get("temp_decks").keys():
            self.myDecks.append(TempDeckRow(self, container, eachDeck, i))
            i = i + 1

class Connect(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Settings and Configuration")
        self.coordinator = coordinator

        self.available_ports = list_ports.comports()
        self.available_port_dict = {}
        self.com_desc_dict = {}
        print("COM Ports:")
        for eachPort in self.available_ports:
            self.available_port_dict[eachPort.description] = eachPort.name
            self.com_desc_dict[eachPort.name] = eachPort.description
        # sets the geometry of toplevel
        self.geometry("1000x1800")
        self.state("zoomed")
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack( side = tk.RIGHT, fill = tk.Y )
        settingsBar = tk.Frame(self)
        settingsBar.pack(side=tk.TOP)
        self.Canv = tk.Canvas(self, width=1000, height = 1800,
                         scrollregion=(0,0,1000,1800)) #width=1256, height = 1674)
        self.Canv.pack(side=tk.TOP) #added sticky

        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.popCanv = tk.Frame(self.Canv)
        self.popCanv.com_dict = self.available_port_dict
        self.popCanv.rev_com_dict = self.com_desc_dict
        interior_id = self.Canv.create_window(0, 0, window=self.popCanv,
                                           anchor=tk.NW)
        self.rowconfigure(0, weight=1) 
        self.columnconfigure(0, weight=1)

        
        self.settings_filename_to_open = DEFAULT_SETTINGS
        
        # A Label widget to show in toplevel
        self.connectButton = tk.Button(settingsBar,activebackground="yellow",text="Connect",command=lambda: self.Connect(coordinator),justify=tk.LEFT)
        self.connectButton.grid(row=0,column=0)
        self.connectButton.configure(bg="gray")
        self.disconnectButton = tk.Button(settingsBar,activebackground="red",text="Disconnect",command=lambda: self.Disconnect(coordinator),justify=tk.LEFT)
        self.disconnectButton.grid(row=0,column=1)
        tk.Button(settingsBar,text="Clear Settings",command=lambda: self.LoadDefaults(coordinator),justify=tk.LEFT).grid(row=0,column=2)
        tk.Button(settingsBar, text='Import from a Settings File', command=lambda: self.LoadSettings(coordinator),justify=tk.LEFT).grid(row=0,column=3)
        tk.Button(settingsBar,text="Save Settings to File",command=lambda: self.SaveSettings(),justify=tk.LEFT).grid(row=0,column=4)
        
        self.advanced_config = None
        self.advanced_config_button = tk.Button(settingsBar, text="Advanced Configuration", command=self.open_advanced_config_page)
        self.advanced_config_button.grid(row=0,column=4)
        


        if coordinator.myModules.settings == None:
            if os.path.isfile(LAST_SETTINGS):
                self.popCanv.loaded_settings = coordinator.myModules.read_dictionary_from_file(LAST_SETTINGS)
            else:
                self.popCanv.loaded_settings = coordinator.myModules.read_dictionary_from_file(DEFAULT_SETTINGS)
        elif coordinator.myModules.status == "connected":
            self.popCanv.loaded_settings = coordinator.myModules.settings
            self.connectButton.configure(bg="green")
        else:
            print("weird, connected, but not connected")

        self.initialize_frames(coordinator)

        self.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(coordinator))

    def open_advanced_config_page(self):
        if not self.advanced_config or not self.advanced_config.winfo_exists():
            self.advanced_config = Configuration(self.coordinator)
        else:
            self.advanced_config.deiconify()

    def on_closing(self, coordinator):
        self.destroy()

    def initialize_frames(self, coordinator):
        self.myPorts = Serial_Ports(self.popCanv)
        self.myPorts.grid(row=0,column=0)
        
        self.myMotors = MotorSeries(self.popCanv, coordinator)
        self.myMotors.grid(row=1,column=0)
        
    
        self.myTempDecks = TempDecks(self.popCanv)
        self.myTempDecks.grid(row=2,column=0)

    def Disconnect(self, coordinator):
        
        coordinator.myModules.disconnect()
        
        self.connectButton.configure(bg="gray")

    def Connect(self, coordinator):
        if coordinator.myModules.status == "connected" or coordinator.myModules.status == "attempted": 
            self.Disconnect(coordinator)
        self.connectButton.configure(bg="red")
        coordinator.myModules.status = "attempted"
        print("\n\nConnecting")
        coordinator.myModules.load_settings_from_dictionary(self.popCanv.loaded_settings)
        coordinator.myModules.settings = self.popCanv.loaded_settings
        coordinator.myModules.status = "connected"
        output_file = open(LAST_SETTINGS, "w")
        json.dump(self.popCanv.loaded_settings, output_file)

        self.connectButton.configure(bg="green")
        
    def LoadDefaults(self, coordinator):
        self.Canv.destroy()
        
        self.Canv = tk.Canvas(self, width=1000, height = 1800,
                         scrollregion=(0,0,1000,1800)) #width=1256, height = 1674)
        self.Canv.pack(side=tk.TOP)#added sticky

        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.popCanv = tk.Frame(self.Canv)
        self.popCanv.com_dict = self.available_port_dict
        self.popCanv.rev_com_dict = self.com_desc_dict
        interior_id = self.Canv.create_window(0, 0, window=self.popCanv,
                                           anchor=tk.NW)
        self.popCanv.loaded_settings = coordinator.myModules.read_dictionary_from_file(DEFAULT_SETTINGS)
        
        self.initialize_frames(coordinator)
            
    def LoadConfigurations(self, coordinator, filename):
        self.Canv.destroy()
        
        self.Canv = tk.Canvas(self, width=1000, height = 1800,
                         scrollregion=(0,0,1000,1800)) #width=1256, height = 1674)
        self.Canv.pack(side=tk.TOP) #added sticky

        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.popCanv = tk.Frame(self.Canv)
        self.popCanv.com_dict = self.available_port_dict
        self.popCanv.rev_com_dict = self.com_desc_dict
        interior_id = self.Canv.create_window(0, 0, window=self.popCanv,
                                           anchor=tk.NW)
        self.popCanv.loaded_settings = coordinator.myModules.read_dictionary_from_file(filename)
        print(self.popCanv.loaded_settings["temp_decks"])
        
        self.initialize_frames(coordinator)
        
    def AddConfigurations(self, coordinator, new_dict):
        old_dict = self.popCanv.loaded_settings
        
        self.Canv.destroy()
        
        self.Canv = tk.Canvas(self, width=1000, height = 1800,
                         scrollregion=(0,0,1000,1800)) #width=1256, height = 1674)
        self.Canv.pack(side=tk.TOP)#added sticky

        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.popCanv = tk.Frame(self.Canv)
        self.popCanv.com_dict = self.available_port_dict
        self.popCanv.rev_com_dict = self.com_desc_dict
        interior_id = self.Canv.create_window(0, 0, window=self.popCanv,
                                           anchor=tk.NW)
        self.popCanv.loaded_settings = old_dict

        self.popCanv.loaded_settings = self.addToDict(old_dict, new_dict)
                                                                                                                                                              
        self.initialize_frames(coordinator)
    
    def addToDict(self, old_dictionary, new_dictionary):
        for eachName in DEFAULT_LIST_NAMES:
            for eachModule in new_dictionary[eachName]:
                old_dictionary[eachName].append(eachModule)
        for eachName in DEFAULT_DICT_NAMES:
            for eachModule in new_dictionary[eachName].keys():
                old_dictionary[eachName][eachModule] = new_dictionary[eachName][eachModule]
        return old_dictionary

    def LoadSettings(self, coordinator):
        filetypes = (
            ('json files', '*.json'),
            ('All files', '*')
        )

        file_path = filedialog.askopenfilename(parent=self, title='Open a file', initialdir='settings', filetypes=filetypes)

        if file_path == None:  # in the event of a cancel 
            return
        
        self.settings_filename_to_open = file_path

        new_dict = coordinator.myModules.read_dictionary_from_file(self.settings_filename_to_open)
        self.AddConfigurations(coordinator, new_dict)

    def SaveSettings(self):
        filetypes = (
            ('json files', '*.json'),
            ( 'All files', '*')
        )

        new_file =  filedialog.asksaveasfile(parent=self, title='Save Settings', initialdir='settings', filetypes=filetypes)
        
        if new_file.name.endswith(".json"):
            new_file = new_file.name.replace(".json","") + ".json"
        else:
            new_file = new_file.name + ".json"
        
        if self.popCanv.loaded_settings != None:
            output_file = open(new_file, "w")

            # Dump the labware dictionary into the json file
            json.dump(self.popCanv.loaded_settings, output_file)

        else:
            print("Error: Nothing to save!")

