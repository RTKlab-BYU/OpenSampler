import json
import tkinter as tk
from tkinter import ttk, filedialog


DEFAULT_SETTINGS = "settings/default_settings.json"
ADDITIONAL_MODULE_TYPES = []
DEFAULT_LIST_NAMES = ["ports","2_position_actuators", "selector_actuators","relays","switches","feedbacks"]
DEFAULT_DICT_NAMES = ["motors_configurations","temp_decks"]
DEFAULT_MOTOR_SETTINGS = {"port":"","motors":{"x":["","",""],"y":["","",""],"z":["","",""]},"syringes":{"s":["","",""]},"side":"","type":"","joystick":{}}

class PortPattern(tk.Entry,):
    def __init__(self, frame, container, string, portIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePortPattern(container, portIndex, self.get()))

    def UpdatePortPattern(self, container, portIndex, new_value):
        container.loaded_settings["ports"][portIndex]["pattern"] = new_value


class PortRow(tk.Frame,):
    def __init__(self, frame, container, eachPort, portIndex, rowNum):
        super().__init__(frame.portsGrid)
        port = PortPattern(frame.portsGrid, container, eachPort["pattern"], portIndex)
        port.grid(row=rowNum,column=0)
        
        delete = tk.Button(frame.portsGrid,text="Remove Port",command= lambda: self.RemovePort(container, portIndex, frame))
        delete.grid(row=rowNum,column=1)

    def UpdateGUI(self, container, SP):
        SP.portsGrid.destroy()
        SP.myPortPatterns = []
        SP.PopulatePorts(container)

    def RemovePort(self, container, portIndex, SP):
        container.loaded_settings["ports"].pop(portIndex)
        SP.UpdateGUI(container)


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

        tk.Label(self.portsGrid, text="Serial Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)

        portIndex = 0
        for eachPort in container.loaded_settings.get("ports"):
            self.myPorts.append(PortRow(self, container, eachPort, portIndex, i))
            portIndex = portIndex + 1
            i = i + 1

        add_button = tk.Button(self.portsGrid,text="Add Output",command= lambda: self.AddPort(container))
        add_button.grid(row=i,column=1)

    def AddPort(self, container):
        container.loaded_settings["ports"].append({"pattern": ""})
        self.UpdateGUI(container)

    def UpdateGUI(self, container):
        self.portsGrid.destroy()
        self.myPortPatterns = []
        self.PopulatePorts(container)

    def RemovePort(self, container, portIndex):
        container.loaded_settings["ports"].pop(portIndex)
        self.UpdateGUI(container)
    

class OutPortNum(tk.Entry,):
    def __init__(self, frame, container, string, OutputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePortPattern(container, OutputIndex, int(self.get())))

    def UpdatePortPattern(self, container, OutputIndex, new_value):
        container.loaded_settings["relays"][OutputIndex]["port"] = new_value


class OutPin(tk.Entry,):
    def __init__(self, frame, container, string, OutputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.parameter_var.trace_add("write", self.update_parameter)

        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, OutputIndex, self.get()))

    def UpdatePinPattern(self, container, OutputIndex, new_value):
        container.loaded_settings["relays"][OutputIndex]["pin"] = new_value


class OutPutRow(tk.Frame,):
    def __init__(self, frame, container, eachOut, portIndex, rowNum):
        super().__init__(frame.portsGrid)
        myPort = OutPortNum(frame.portsGrid, container, eachOut["port"], portIndex)
        myPort.grid(row=rowNum,column=0)

        myPin = OutPin(frame.portsGrid, container, eachOut["pin"], portIndex)
        myPin.grid(row=rowNum,column=1)
        
        delete = tk.Button(frame.portsGrid,text="Remove Output",command= lambda: self.RemoveOutput(container, portIndex, frame))
        delete.grid(row=rowNum,column=2)
    
    def UpdateGUI(self, container, SP):
        SP.portsGrid.destroy()
        SP.myPortPatterns = []
        SP.PopulatePorts(container)

    def RemoveOutput(self, container, portIndex, SP):
        container.loaded_settings["relays"].pop(portIndex)
        SP.UpdateGUI(container)   
        
            
class Outputs(tk.Frame,):
    def __init__(self, container):
        super().__init__(container)
        self.PopulateOutputs(container)

    def PopulateOutputs(self, container):
        self.portsGrid = tk.Frame(self)
        self.portsGrid.pack(side=tk.TOP)
        tk.Label(self.portsGrid, text="Outputs", font="Helvetica 14",justify=tk.LEFT).grid(row=0,column=0)
        self.myOutputs = []
        i = 2
        tk.Label(self.portsGrid, text="Serial Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)

        tk.Label(self.portsGrid, text="Pin", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
        portIndex = 0
        for eachOut in container.loaded_settings.get("relays"):
            self.myOutputs.append(OutPutRow(self, container, eachOut, portIndex, i))
            portIndex = portIndex + 1
            i = i + 1
        add_button = tk.Button(self.portsGrid,text="Add Output",command= lambda: self.AddOutput(container))
        add_button.grid(row=i,column=2)
    
    def AddOutput(self, container):
        container.loaded_settings["relays"].append({"port": "", "pin": ""})
        self.UpdateGUI(container)

    def UpdateGUI(self, container):
        self.portsGrid.destroy()
        self.myOutputs = []
        self.PopulateOutputs(container)

    def RemoveOutput(self, container, portIndex):
        container.loaded_settings["relays"].pop(portIndex)
        self.UpdateGUI(container)


class SwitchPortNum(tk.Entry,):
    def __init__(self, frame, container, string, SwitchIndex):
        super().__init__(frame)
       # self.ButtonVar.trace("w", lambda x,y,z: self.UpdateButton(container, j, eachButton, self.ButtonVar[j][i-2]))
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePortPattern(container, SwitchIndex, int(self.get())))

    def UpdatePortPattern(self, container, SwitchIndex, new_value):
        container.loaded_settings["switches"][SwitchIndex]["port"] = new_value


class SwitchPinLeft(tk.Entry,):
    def __init__(self, frame, container, string, SwitchIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, SwitchIndex, self.get()))

    def UpdatePinPattern(self, container, SwitchIndex, new_value):
        container.loaded_settings["switches"][SwitchIndex]["pin_left"] = new_value


class SwitchPinRight(tk.Entry,):
    def __init__(self, frame, container, string, SwitchIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, SwitchIndex, self.get()))

    def UpdatePinPattern(self, container, SwitchIndex, new_value):
        container.loaded_settings["switches"][SwitchIndex]["pin_right"] = new_value


class SwitchRow(tk.Frame,):
    def __init__(self, frame, container, eachSwitch, portIndex, rowNum):
        super().__init__(frame.portsGrid)
        myPort = SwitchPortNum(frame.portsGrid, container, eachSwitch["port"], portIndex)
        myPort.grid(row=rowNum,column=0)

        myPin = SwitchPinLeft(frame.portsGrid, container, eachSwitch["pin_left"], portIndex)
        myPin.grid(row=rowNum,column=1)

        myPin = SwitchPinRight(frame.portsGrid, container, eachSwitch["pin_right"], portIndex)
        myPin.grid(row=rowNum,column=2)

        delete = tk.Button(frame.portsGrid,text="Remove Switch",command= lambda: self.RemoveSwitch(container, portIndex, frame))
        delete.grid(row=rowNum,column=3)
    
    def UpdateGUI(self, container, SP):
        SP.portsGrid.destroy()
        SP.myPortPatterns = []
        SP.PopulatePorts(container)

    def RemoveSwitch(self, container, portIndex, SP):
        container.loaded_settings["switches"].pop(portIndex)
        SP.UpdateGUI(container)       


class Switches(tk.Frame,):
    def __init__(self, container):
        super().__init__(container)
        self.PopulateSwitches(container)

    def PopulateSwitches(self, container):
        self.portsGrid = tk.Frame(self)
        self.portsGrid.pack(side=tk.TOP)
        tk.Label(self.portsGrid, text="Switches", font="Helvetica 14",justify=tk.LEFT).grid(row=0,column=0)
        self.mySwitches = []
        i = 2
        tk.Label(self.portsGrid, text="Serial Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)

        tk.Label(self.portsGrid, text="Pin Left", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
        tk.Label(self.portsGrid, text="Pin Right", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=2)
        portIndex = 0
        for eachOut in container.loaded_settings.get("switches"):
            self.mySwitches.append(SwitchRow(self, container, eachOut, portIndex, i))
            portIndex = portIndex + 1
            i = i + 1
        add_button = tk.Button(self.portsGrid,text="Add Switch",command= lambda: self.AddSwitch(container))
        add_button.grid(row=i,column=2)
    
    def AddSwitch(self, container):
        container.loaded_settings["switches"].append({"port": "", "pin_left": "", "pin_right": ""})
        self.UpdateGUI(container)

    def UpdateGUI(self, container):
        self.portsGrid.destroy()
        self.mySwitches = []
        self.PopulateSwitches(container)

    def RemoveSwitch(self, container, portIndex):
        container.loaded_settings["switches"].pop(portIndex)
        self.UpdateGUI(container)


class InPortNum(tk.Entry,):
    def __init__(self, frame, container, string, inputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePortPattern(container, inputIndex, int(self.get())))

    def UpdatePortPattern(self, container, inputIndex, new_value):
        container.loaded_settings["feedbacks"][inputIndex]["port"] = new_value


class InPin(tk.Entry,):
    def __init__(self, frame, container, string, inputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, inputIndex, self.get()))

    def UpdatePinPattern(self, container, inputIndex, new_value):
        container.loaded_settings["feedbacks"][inputIndex]["pin"] = new_value


class InputRow(tk.Frame,):
    def __init__(self, frame, container, eachOut, portIndex, rowNum):
        super().__init__(frame.portsGrid)
        myPort = InPortNum(frame.portsGrid, container, eachOut["port"], portIndex)
        myPort.grid(row=rowNum,column=0)

        myPin = InPin(frame.portsGrid, container, eachOut["pin"], portIndex)
        myPin.grid(row=rowNum,column=1)
        
        delete = tk.Button(frame.portsGrid,text="Remove Input",command= lambda: self.RemoveInput(container, portIndex, frame))
        delete.grid(row=rowNum,column=2)
    
    def UpdateGUI(self, container, SP):
        SP.portsGrid.destroy()
        SP.myPortPatterns = []
        SP.PopulatePorts(container)

    def RemoveInput(self, container, portIndex, SP):
        container.loaded_settings["feedbacks"].pop(portIndex)
        SP.UpdateGUI(container)


class Inputs(tk.Frame,):
    def __init__(self, container):
        super().__init__(container)
        self.PopulateInputs(container)

    def PopulateInputs(self, container):
        self.portsGrid = tk.Frame(self)
        self.portsGrid.pack(side=tk.TOP)
        tk.Label(self.portsGrid, text="Inputs", font="Helvetica 14",justify=tk.LEFT).grid(row=0,column=0)
        self.myInputs = []
        i = 2

        tk.Label(self.portsGrid, text="Serial Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)

        tk.Label(self.portsGrid, text="Pin", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
        portIndex = 0
        for eachOut in container.loaded_settings.get("feedbacks"):
            self.myInputs.append(InputRow(self, container, eachOut, portIndex, i))
            portIndex = portIndex + 1
            i = i + 1

        add_button = tk.Button(self.portsGrid,text="Add Input",command= lambda: self.AddInput(container))
        add_button.grid(row=i,column=2)
    
    def AddInput(self, container):
        container.loaded_settings["feedbacks"].append({"port": "", "pin": ""})
        self.UpdateGUI(container)

    def UpdateGUI(self, container):
        self.portsGrid.destroy()
        self.myInputs = []
        self.PopulateInputs(container)

    def RemoveInput(self, container, portIndex):
        container.loaded_settings["feedbacks"].pop(portIndex)
        self.UpdateGUI(container)


class ValvePortNum(tk.Entry,):
    def __init__(self, frame, container, string, inputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePortPattern(container, inputIndex, int(self.get())))

    def UpdatePortPattern(self, container, inputIndex, new_value):
        container.loaded_settings["2_position_actuators"][inputIndex]["port"] = new_value


class AInPin(tk.Entry,):
    def __init__(self, frame, container, string, inputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, inputIndex, self.get()))

    def UpdatePinPattern(self, container, inputIndex, new_value):
        container.loaded_settings["2_position_actuators"][inputIndex]["Position A In"] = new_value


class AOutPin(tk.Entry,):
    def __init__(self, frame, container, string, OutputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, OutputIndex, self.get()))

    def UpdatePinPattern(self, container, OutputIndex, new_value):
        container.loaded_settings["2_position_actuators"][OutputIndex]["Position A Out"] = new_value


class BInPin(tk.Entry,):
    def __init__(self, frame, container, string, inputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, inputIndex, self.get()))

    def UpdatePinPattern(self, container, inputIndex, new_value):
        print(new_value)
        container.loaded_settings["2_position_actuators"][inputIndex]["Position B In"] = new_value


class BOutPin(tk.Entry,):
    def __init__(self, frame, container, string, OutputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, OutputIndex, self.get()))

    def UpdatePinPattern(self, container, OutputIndex, new_value):
        container.loaded_settings["2_position_actuators"][OutputIndex]["Position B Out"] = new_value


class ValveRow(tk.Frame,):
    def __init__(self, frame, container, eachOut, portIndex, rowNum):
        super().__init__(frame.portsGrid)
        ValvePortNum(frame.portsGrid, container, eachOut["port"], portIndex).grid(row=rowNum,column=0)
        AInPin(frame.portsGrid, container, eachOut["Position A In"], portIndex).grid(row=rowNum,column=1)
        AOutPin(frame.portsGrid, container, eachOut["Position A Out"], portIndex).grid(row=rowNum,column=2)
        BInPin(frame.portsGrid, container, eachOut["Position B In"], portIndex).grid(row=rowNum,column=3)
        BOutPin(frame.portsGrid, container, eachOut["Position B Out"], portIndex).grid(row=rowNum,column=4)
        
        delete = tk.Button(frame.portsGrid,text="Remove Valve",command= lambda: self.RemoveValve(container, portIndex, frame))
        delete.grid(row=rowNum,column=5)
    
    def UpdateGUI(self, container, SP):
        SP.portsGrid.destroy()
        SP.myPortPatterns = []
        SP.PopulatePorts(container)

    def RemoveValve(self, container, portIndex, SP):
        container.loaded_settings["2_position_actuators"].pop(portIndex)
        SP.UpdateGUI(container)


class Valves(tk.Frame,):
    def __init__(self, container):
        super().__init__(container)
        self.PopulateValves(container)

    def PopulateValves(self, container):
        self.portsGrid = tk.Frame(self)
        self.portsGrid.pack(side=tk.TOP)
        tk.Label(self.portsGrid, text="2-Position Valves", font="Helvetica 14", justify=tk.LEFT).grid(row=0, column=0)
        self.myValves = []
        i = 2

        tk.Label(self.portsGrid, text="Serial Port", font="Helvetica 10", justify=tk.LEFT).grid(row=1, column=0)
        tk.Label(self.portsGrid, text="A Feedback", font="Helvetica 10", justify=tk.LEFT).grid(row=1, column=1)
        tk.Label(self.portsGrid, text="Go to A", font="Helvetica 10", justify=tk.LEFT).grid(row=1, column=2)
        tk.Label(self.portsGrid, text="B Feedback", font="Helvetica 10", justify=tk.LEFT).grid(row=1, column=3)
        tk.Label(self.portsGrid, text="Go to B", font="Helvetica 10", justify=tk.LEFT).grid(row=1, column=4)
        portIndex = 0
        for eachOut in container.loaded_settings.get("2_position_actuators"):
            self.myValves.append(ValveRow(self, container, eachOut, portIndex, i))
            portIndex = portIndex + 1
            i = i + 1

        add_button = tk.Button(self.portsGrid,text="Add Valve",command= lambda: self.AddValve(container))
        add_button.grid(row=i,column=5)
    
    def AddValve(self, container):
        container.loaded_settings["2_position_actuators"].append({"port": "","Position A Out": "", "Position B Out": "","Position A In":  "","Position B In":  ""})
        self.UpdateGUI(container)

    def UpdateGUI(self, container):
        self.portsGrid.destroy()
        self.myValves = []
        self.PopulateValves(container)

    def RemoveValve(self, container, portIndex):
        container.loaded_settings["2_position_actuators"].pop(portIndex)
        self.UpdateGUI(container)


class SelectorPortNum(tk.Entry,):
    def __init__(self, frame, container, string, inputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePortPattern(container, inputIndex, int(self.get())))

    def UpdatePortPattern(self, container, inputIndex, new_value):
        container.loaded_settings["selector_actuators"][inputIndex]["port"] = new_value


class MoveOutPin(tk.Entry,):
    def __init__(self, frame, container, string, OutputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, OutputIndex, self.get()))

    def UpdatePinPattern(self, container, OutputIndex, new_value):
        container.loaded_settings["selector_actuators"][OutputIndex]["Move Out"] = new_value


class HomeOutPin(tk.Entry,):
    def __init__(self, frame, container, string, OutputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePinPattern(container, OutputIndex, self.get()))

    def UpdatePinPattern(self, container, OutputIndex, new_value):
        container.loaded_settings["selector_actuators"][OutputIndex]["Home Out"] = new_value


class NumSelectorPorts(tk.Entry,):
    def __init__(self, frame, container, string, inputIndex):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePortPattern(container, inputIndex, int(self.get())))

    def UpdatePortPattern(self, container, inputIndex, new_value):
        container.loaded_settings["selector_actuators"][inputIndex]["Number of Ports"] = new_value


class SelectorRow(tk.Frame,):
    def __init__(self, frame, container, eachOut, portIndex, rowNum):
        super().__init__(frame.portsGrid)
        SelectorPortNum(frame.portsGrid, container, eachOut["port"], portIndex).grid(row=rowNum,column=0)
        HomeOutPin(frame.portsGrid, container, eachOut["Home Out"], portIndex).grid(row=rowNum,column=1)
        MoveOutPin(frame.portsGrid, container, eachOut["Move Out"], portIndex).grid(row=rowNum,column=2)
        NumSelectorPorts(frame.portsGrid, container, eachOut["Number of Ports"], portIndex).grid(row=rowNum,column=3)

        tk.Button(frame.portsGrid,text="Remove Selector",command= lambda: self.RemoveSelector(container, portIndex, frame)).grid(row=rowNum,column=4)
    
    def UpdateGUI(self, container, SP):
        SP.portsGrid.destroy()
        SP.myPortPatterns = []
        SP.PopulatePorts(container)

    def RemoveSelector(self, container, portIndex, SP):
        container.loaded_settings["selector_actuators"].pop(portIndex)
        SP.UpdateGUI(container)


class Selectors(tk.Frame,):
    def __init__(self, container):
        super().__init__(container)
        self.PopulateSelectors(container)

    def PopulateSelectors(self, container):
        self.portsGrid = tk.Frame(self)
        self.portsGrid.pack(side=tk.TOP)
        tk.Label(self.portsGrid, text="Selector Valves", font="Helvetica 14",justify=tk.LEFT).grid(row=0,column=0)
        self.mySelectors = []
        i = 2

        tk.Label(self.portsGrid, text="Serial Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
        tk.Label(self.portsGrid, text="Go to Home", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
        tk.Label(self.portsGrid, text="Step Valve", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=2)
        tk.Label(self.portsGrid, text="Number of Ports", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=3)
        portIndex = 0
        for eachSelector in container.loaded_settings.get("selector_actuators"):
            self.mySelectors.append(SelectorRow(self, container, eachSelector, portIndex, i))
            portIndex = portIndex + 1
            i = i + 1
        add_button = tk.Button(self.portsGrid,text="Add Selector",command= lambda: self.AddSelector(container))
        add_button.grid(row=i,column=4)
    
    def AddSelector(self, container):
        container.loaded_settings["selector_actuators"].append({"port": "", "Home Out": "","Move Out": "", "Number of Ports": ""})
        self.UpdateGUI(container)

    def UpdateGUI(self, container):
        self.portsGrid.destroy()
        self.mySelectors = []

        self.PopulateSelectors(container)

    def RemoveSelector(self, container, portIndex):
        container.loaded_settings.get("selector_actuators").pop(portIndex)
        self.UpdateGUI(container)


class MotorSeriesPort(tk.Entry,):
    def __init__(self, frame, container, string, selectedMotorSeries):
        super().__init__(frame) 
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdateMotorPort(container, selectedMotorSeries, self.get()))

    def UpdateMotorPort(self, container, selectedMotorSeries, new_value):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["port"] = new_value


class MotorSeriesName(tk.Entry,):
    def __init__(self, frame, stages, container,coordinator, selectedMotorSeries):
        super().__init__(frame) 
        self.insert(tk.END,selectedMotorSeries)
        self.bind('<FocusOut>',lambda x: self.UpdateMotorName(stages, container, coordinator, selectedMotorSeries, self.get()))

    def UpdateMotorName(self, stages, container, coordinator, selectedMotorSeries, new_value):
        old_value = container.loaded_settings["motors_configurations"].pop(selectedMotorSeries)
        container.loaded_settings["motors_configurations"][new_value] = old_value
        stages.UpdateGUI(container, coordinator)


class MotorName(tk.Label,):
    def __init__(self, frame, container, key, string, selectedMotorSeries):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.key = key

    def UpdateMotorSettingsValue(self, container, selectedMotorSeries, thisKey, index, new_value):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["motors"][thisKey][index] = new_value     


class MotorNumber(tk.Entry,):
    def __init__(self, frame, container, key, string, selectedMotorSeries):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.key = key
        self.bind('<FocusOut>',lambda x: self.UpdateMotorSettingsValue(container, selectedMotorSeries, self.key, 1, self.get()))

    def UpdateMotorSettingsValue(self, container, selectedMotorSeries, thisKey, index, new_value):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["motors"][thisKey][index] = new_value


class MotorSpeed(tk.Entry,):
    def __init__(self, frame, container, key, string, selectedMotorSeries):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.key = key
        self.bind('<FocusOut>',lambda x: self.UpdateMotorSettingsValue(container, selectedMotorSeries, self.key, 0, self.get()))

    def UpdateMotorSettingsValue(self, container, selectedMotorSeries, thisKey, index, new_value):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["motors"][thisKey][index] = new_value


class MotorLength(tk.Entry,):
    def __init__(self, frame, container, key, string, selectedMotorSeries):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.key = key
        self.bind('<FocusOut>',lambda x: self.UpdateMotorSettingsValue(container, selectedMotorSeries, self.key, 2, self.get()))

    def UpdateMotorSettingsValue(self, container, selectedMotorSeries, thisKey, index, new_value):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["motors"][thisKey][index] = new_value


class SyringeSpeed(tk.Entry,):
    def __init__(self, frame, container, key, string, selectedMotorSeries):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.key = key
        self.bind('<FocusOut>',lambda x: self.UpdateSyringeSettingsValue(container, selectedMotorSeries, self.key, 0, self.get()))

    def UpdateSyringeSettingsValue(self, container, selectedMotorSeries, thisKey, index, new_value):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["syringes"][thisKey][index] = new_value


class SyringeNumber(tk.Entry,):
    def __init__(self, frame, container, key, string, selectedMotorSeries):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.key = key
        self.bind('<FocusOut>',lambda x: self.UpdateSyringeSettingsValue(container, selectedMotorSeries, self.key, 1, self.get()))

    def UpdateSyringeSettingsValue(self, container, selectedMotorSeries, thisKey, index, new_value):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["syringes"][thisKey][index] = new_value


class SyringeLength(tk.Entry,):
    def __init__(self, frame, container, key, string, selectedMotorSeries):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.key = key
        self.bind('<FocusOut>',lambda x: self.UpdateSyringeSettingsValue(container, selectedMotorSeries, self.key, 2, self.get()))

    def UpdateSyringeSettingsValue(self, container, selectedMotorSeries, thisKey, index, new_value):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["syringes"][thisKey][index] = new_value

        
class SyringeRow(tk.Frame,):
    def __init__(self, frame, coordinator, container, eachSyringe, selectedMotorSeries, rowNum, loadedSyringes):
        tk.Label(frame.syringesGrid, text=eachSyringe).grid(row=rowNum,column=0)
        
        numText = loadedSyringes.get(eachSyringe)[1]
        SyringeNumber(frame.syringesGrid, container, eachSyringe, numText, selectedMotorSeries).grid(row=rowNum,column=1)

        speedText = loadedSyringes.get(eachSyringe)[0]
        SyringeSpeed(frame.syringesGrid, container, eachSyringe, speedText, selectedMotorSeries).grid(row=rowNum,column=2)

        lengthText = loadedSyringes.get(eachSyringe)[2]
        SyringeLength(frame.syringesGrid, container, eachSyringe, lengthText, selectedMotorSeries).grid(row=rowNum,column=3)


class MotorRow(tk.Frame,):
    def __init__(self, frame, coordinator, container, eachStage, selectedMotorSeries, rowNum, loadedMotors):
        tk.Label(frame.motorsGrid, text=eachStage).grid(row=rowNum,column=0)
        
        numText = loadedMotors.get(eachStage)[1]
        MotorNumber(frame.motorsGrid, container, eachStage, numText, selectedMotorSeries).grid(row=rowNum,column=1)

        speedText = loadedMotors.get(eachStage)[0]
        MotorSpeed(frame.motorsGrid, container, eachStage, speedText, selectedMotorSeries).grid(row=rowNum,column=2)

        lengthText = loadedMotors.get(eachStage)[2]
        MotorLength(frame.motorsGrid, container, eachStage, lengthText, selectedMotorSeries).grid(row=rowNum,column=3)


class OTMotorRow(tk.Frame,):
    def __init__(self, frame, coordinator, container, eachStage, selectedMotorSeries, rowNum, loadedMotors):
        tk.Label(frame.motorsGrid, text=eachStage).grid(row=rowNum,column=0)
        
        lengthText = loadedMotors.get(eachStage)[2]
        MotorLength(frame.motorsGrid, container, eachStage, lengthText, selectedMotorSeries).grid(row=rowNum,column=1)


class OT_Side(tk.Entry,):
    def __init__(self, frame, container, string, selectedMotorSeries):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdateSide(container, selectedMotorSeries, self.get()))

    def UpdateSide(self, container, selectedMotorSeries, new_value):
        print(selectedMotorSeries)
        print(type(new_value))
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["side"] = new_value


class Motor_Sets(tk.Frame,):
    def __init__(self, container, coordinator):
        super().__init__(container)
        tk.Label(self, text="Motor Settings", font="Helvetica 16",justify=tk.LEFT).pack(side=tk.TOP)
        self.syringes = []
        self.motors = []
        self.myJoy = []
        self.myProfiles = []
        self.PopulateGUI(container, coordinator)
        
    def UpdateGrid(self, container, selectedmotorseries):
        self.joyGrid.destroy()
        self.myJoy = []
        self.myProfiles = []
        self.PopulateGrid(container, selectedmotorseries)

    def PopulateGrid(self, container, selectedmotorseries):
        self.joyGrid = tk.Frame(self)
        self.joyGrid.pack(side=tk.TOP)
        tk.Label(self.joyGrid, text="Joystick Profiles", font="Helvetica 11",justify=tk.LEFT).grid(row=0,column=0)
        self.myProfiles.append(JoyCol(self, container, container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"], selectedmotorseries))
        
    def PopulateGUI(self, container, coordinator):
        self.selectStageBar = tk.Frame(self)
        self.selectStageBar.pack(side=tk.TOP)
        self.motorsGrid = tk.Frame(self)
        self.motorsGrid.pack(side=tk.TOP)
        self.syringesGrid = tk.Frame(self)
        self.syringesGrid.pack(side=tk.TOP)
        self.Port = tk.Entry(self.motorsGrid)
        tk.Label(self.selectStageBar, text="Select Stage: ", font="Helvetica 12",justify=tk.LEFT).grid(row=0,column=0)
        stageOptions = container.loaded_settings["motors_configurations"].keys()
        if(len(stageOptions)>0):
            self.motorsGrid.destroy()
            self.motorsGrid = tk.Frame(self)
            self.motorsGrid.pack(side=tk.TOP)
            self.syringesGrid.destroy()
            self.syringesGrid = tk.Frame(self)
            self.syringesGrid.pack(side=tk.TOP)
            self.loadedMotorSeries = ttk.Combobox(self.selectStageBar, state='readonly')
            self.loadedMotorSeries.grid(row=0,column=1)
            self.loadedMotorSeries["values"] = [*stageOptions]
            self.loadedMotorSeries.current(0)
            self.loadedMotorSeries.bind("<<ComboboxSelected>>", lambda x: self.UpdateGUIforMotors(container, coordinator))
            self.PopulateMotors(container, coordinator)
        else:
            self.joyGrid = tk.Frame(self)
            self.joyGrid.pack(side=tk.TOP)
        tk.Button(self.selectStageBar,text="Add Series",command= lambda: self.AddMotorSeries(container, coordinator)).grid(row=0,column=2)

    def PopulateMotors(self, container, coordinator):
        selectedMotorSeries = self.loadedMotorSeries.get()
        
        #print(type(selectedMotorSeries))
        self.motorsGrid = tk.Frame(self)
        self.motorsGrid.pack(side=tk.TOP)
        tk.Label(self.motorsGrid, text="Motors:", font="Helvetica 12",justify=tk.LEFT).grid(row=0,column=0)
        tk.Label(self.motorsGrid, text="Port:", font="Helvetica 10",justify=tk.LEFT).grid(row=0,column=1)
        portText = container.loaded_settings["motors_configurations"][selectedMotorSeries].get("port")
        self.Port = MotorSeriesPort(self.motorsGrid,container,portText,selectedMotorSeries)
        self.Port.grid(row=0,column=2)
        tk.Label(self.motorsGrid, text="Name:", font="Helvetica 10",justify=tk.LEFT).grid(row=0,column=3)
        self.Name = MotorSeriesName(self.motorsGrid,self,container,coordinator,selectedMotorSeries)
        self.Name.grid(row=0,column=4)
        tk.Label(self.motorsGrid, text="Type:", font="Helvetica 10",justify=tk.LEFT).grid(row=0,column=5)
        self.motorSeriesType = ttk.Combobox(self.motorsGrid, state='readonly')
        self.motorSeriesType.grid(row=0,column=6)
        self.motorSeriesType["values"] = ["Zaber", "Opentrons", "Zaber - Syringe Only"]
        match container.loaded_settings["motors_configurations"][selectedMotorSeries].get("type"):
            case "Zaber":
                combo_start = 0
                self.motorSeriesType.current(combo_start)
                self.motorSeriesType.bind("<<ComboboxSelected>>", lambda x: self.UpdateMotorType(container, coordinator))

                tk.Button(self.motorsGrid,text="Remove Series",command= lambda: self.RemoveMotorSeries(container, coordinator, selectedMotorSeries)).grid(row=0,column=7)
                loadedMotors = container.loaded_settings["motors_configurations"][selectedMotorSeries]["motors"]
                tk.Label(self.motorsGrid, text="Name:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
                tk.Label(self.motorsGrid, text="Number:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
                tk.Label(self.motorsGrid, text="Max Speed:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=2)
                tk.Label(self.motorsGrid, text="Length:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=3)
                
                i = 2   
                for eachStage in loadedMotors.keys():
                    self.motors.append(MotorRow(self, coordinator, container, eachStage, selectedMotorSeries, i, loadedMotors))
                    i = i + 1

                # add_button = tk.Button(self.motorsGrid,text="Add Motor",command= lambda: self.AddMotor(container, coordinator, selectedMotorSeries))
                # add_button.grid(row=i,column=4)
                self.syringesGrid = tk.Frame(self)
                self.syringesGrid.pack(side=tk.TOP)
                tk.Label(self.syringesGrid, text="Syringe Settings:", font="Helvetica 12",justify=tk.LEFT).grid(row=0,column=0)
                loadedSyringes = container.loaded_settings["motors_configurations"][selectedMotorSeries].get("syringes")
                #print(loadedSyringes)
                tk.Label(self.syringesGrid, text="Name:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
                tk.Label(self.syringesGrid, text="Number:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
                tk.Label(self.syringesGrid, text="Max Speed:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=2)
                tk.Label(self.syringesGrid, text="Length:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=3)
                i = 2
                for eachSyringe in loadedSyringes.keys():
                    self.syringes.append(SyringeRow(self, coordinator, container, eachSyringe, selectedMotorSeries, i, loadedSyringes))

                    i = i + 1
                # add_button = tk.Button(self.syringesGrid,text="Add Syringe",command= lambda: self.AddSyringe(container, coordinator, selectedMotorSeries))
                # add_button.grid(row=i,column=5)
            case "Opentrons":
                combo_start = 1
                self.motorSeriesType.current(combo_start)
                self.motorSeriesType.bind("<<ComboboxSelected>>", lambda x: self.UpdateMotorType(container, coordinator))
                tk.Button(self.motorsGrid,text="Remove Series",command= lambda: self.RemoveMotorSeries(container, coordinator, selectedMotorSeries)).grid(row=0,column=7)
                tk.Label(self.motorsGrid, text="Side:", font="Helvetica 12",justify=tk.LEFT).grid(row=1,column=0)
                if "side" in container.loaded_settings["motors_configurations"][selectedMotorSeries].keys():
                    side = container.loaded_settings["motors_configurations"][selectedMotorSeries]["side"]
                    print(side)
                else: 
                    side = ""
                    container.loaded_settings["motors_configurations"][selectedMotorSeries]["side"] = side
                OT_Side(self.motorsGrid,container,side,selectedMotorSeries).grid(column=1,row=1)

                loadedMotors = container.loaded_settings["motors_configurations"][selectedMotorSeries]["motors"]
                tk.Label(self.motorsGrid, text="Name:", font="Helvetica 10",justify=tk.LEFT).grid(row=2,column=0)
                tk.Label(self.motorsGrid, text="Length:", font="Helvetica 10",justify=tk.LEFT).grid(row=2,column=1)
                
                i = 3   
                for eachStage in loadedMotors.keys():
                    self.motors.append(OTMotorRow(self, coordinator, container, eachStage, selectedMotorSeries, i, loadedMotors))
                    i = i + 1

                # add_button = tk.Button(self.motorsGrid,text="Add Motor",command= lambda: self.AddMotor(container, coordinator, selectedMotorSeries))
                # add_button.grid(row=i,column=4)
                self.syringesGrid = tk.Frame(self)
                self.syringesGrid.pack(side=tk.TOP)
                tk.Label(self.syringesGrid, text="Syringe Settings:", font="Helvetica 12",justify=tk.LEFT).grid(row=0,column=0)
                loadedSyringes = container.loaded_settings["motors_configurations"][selectedMotorSeries].get("syringes")
                #print(loadedSyringes)
                tk.Label(self.syringesGrid, text="Name:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
                tk.Label(self.syringesGrid, text="Number:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
                tk.Label(self.syringesGrid, text="Max Speed:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=2)
                tk.Label(self.syringesGrid, text="Length:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=3)
                i = 2
                for eachSyringe in loadedSyringes.keys():
                    self.syringes.append(SyringeRow(self, coordinator, container, eachSyringe, selectedMotorSeries, i, loadedSyringes))

                    i = i + 1
            case "Zaber - Syringe Only":
                combo_start = 2
                self.motorSeriesType.current(combo_start)
                self.motorSeriesType.bind("<<ComboboxSelected>>", lambda x: self.UpdateMotorType(container, coordinator))

                tk.Button(self.motorsGrid,text="Remove Series",command= lambda: self.RemoveMotorSeries(container, coordinator, selectedMotorSeries)).grid(row=0,column=7)
                
                # add_button = tk.Button(self.motorsGrid,text="Add Motor",command= lambda: self.AddMotor(container, coordinator, selectedMotorSeries))
                # add_button.grid(row=i,column=4)
                self.syringesGrid = tk.Frame(self)
                self.syringesGrid.pack(side=tk.TOP)
                tk.Label(self.syringesGrid, text="Syringe Settings:", font="Helvetica 12",justify=tk.LEFT).grid(row=0,column=0)
                loadedSyringes = container.loaded_settings["motors_configurations"][selectedMotorSeries].get("syringes")
                #print(loadedSyringes)
                tk.Label(self.syringesGrid, text="Name:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
                tk.Label(self.syringesGrid, text="Number:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
                tk.Label(self.syringesGrid, text="Max Speed:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=2)
                tk.Label(self.syringesGrid, text="Length:", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=3)
                i = 2
                for eachSyringe in loadedSyringes.keys():
                    self.syringes.append(SyringeRow(self, coordinator, container, eachSyringe, selectedMotorSeries, i, loadedSyringes))

                    i = i + 1
                # add_button = tk.Button(self.syringesGrid,text="Add Syringe",command= lambda: self.AddSyringe(container, coordinator, selectedMotorSeries))
                # add_button.grid(row=i,column=5) 
            
            case "":
                self.motorSeriesType.bind("<<ComboboxSelected>>", lambda x: self.UpdateMotorType(container, coordinator))
                tk.Button(self.motorsGrid,text="Remove Series",command= lambda: self.RemoveMotorSeries(container, coordinator, selectedMotorSeries)).grid(row=0,column=7)
        self.PopulateGrid(container, selectedMotorSeries)
                
    def UpdateMotorType(self, container, coordinator):
        current_type = self.motorSeriesType.get()
        current_motor = self.loadedMotorSeries.get()
        container.loaded_settings["motors_configurations"][current_motor]["type"] = current_type
        self.motorsGrid.destroy()
        self.syringesGrid.destroy()
        self.joyGrid.destroy()
        self.PopulateMotors(container, coordinator)

    def UpdateGUIforMotors(self, container, coordinator):
        self.syringes = []
        self.motors = []
        self.motorsGrid.destroy()
        self.syringesGrid.destroy()
        self.joyGrid.destroy()
        self.PopulateMotors(container, coordinator)

    def AddMotorSeries(self, container, coordinator):
        container.loaded_settings["motors_configurations"]["new"] = DEFAULT_MOTOR_SETTINGS
        self.UpdateGUI(container, coordinator)

    def RemoveMotorSeries(self, container, coordinator, selectedMotorSeries):
        container.loaded_settings["motors_configurations"].pop(selectedMotorSeries)
        self.UpdateGUI(container, coordinator)

    def UpdateGUI(self, container, coordinator):
        self.syringes = []
        self.motors = []
        self.selectStageBar.destroy()
        self.motorsGrid.destroy()
        self.syringesGrid.destroy()
        self.joyGrid.destroy()
        self.PopulateGUI(container, coordinator)

    def RemoveMotor(self, container, coordinator, selectedMotorSeries, motorIndex):
        container.loaded_settings["motors_configurations"][selectedMotorSeries]["motors"].pop(motorIndex)
        self.UpdateGUIforMotors(container, coordinator)
        self.syringes = []
        self.motors = []
        self.motorsGrid.destroy()
        self.syringesGrid.destroy()
  

class JoyName(tk.Entry,):
    def __init__(self, frame, container, currentName):
        super().__init__(frame) 
        self.insert(tk.END,currentName)
        self.bind('<FocusOut>',lambda x: self.UpdateJoystickName(container, currentName, self.get()))

    def UpdateJoystickName(self, container, selectedmotorseries, new_value):
        old_value = container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"].pop(selectedmotorseries)
        container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"][new_value] = old_value


class JoyButton(tk.Entry,):
    def __init__(self, frame, joysticks, container, string, profile_index):
        super().__init__(frame)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdateButton(container, joysticks, profile_index, string, self.get()))

    def UpdateButton(self, container, joysticks, selectedmotorseries, old_key, new_Key):
        current_keys = container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"].keys()
        if old_key in current_keys and new_Key not in current_keys:
            oldValue = container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"].pop(old_key)
            container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"][new_Key] = oldValue
            joysticks.UpdateGrid(container,selectedmotorseries)
        else:
            print(current_keys)


class JoyCommand(tk.Entry,):
    def __init__(self, frame, container, key, string, selectedmotorseries):
        super().__init__(frame)
        self.key = key
       # self.ButtonVar.trace("w", lambda x,y,z: self.UpdateButton(container, j, eachButton, self.ButtonVar[j][i-2]))
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdateCommand(container, selectedmotorseries, key, self.get()))

    def UpdateCommand(self, container, selectedmotorseries, this_key, new_value):
        container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"][this_key] = new_value


class JoyRow(tk.Frame,):
    def __init__(self, frame, container, eachButton, rowNum, eachProfile, selectedmotorseries):
        super().__init__(frame.joyGrid)
        JoyButton(frame.joyGrid, frame, container, eachButton, selectedmotorseries).grid(row=rowNum,column=0)

        JoyCommand(frame.joyGrid, container, eachButton, eachProfile.get(eachButton), selectedmotorseries).grid(row=rowNum,column=1)

        tk.Button(frame.joyGrid,text="Remove Button",command= lambda: self.RemoveJoy(container, selectedmotorseries, eachButton, frame)).grid(row=rowNum,column=2)
        
    def UpdateGUI(self, container, SP, selected_motor_series):
        SP.joyGrid.destroy()
        SP.myJoy = []
        SP.PopulateGrid(container, selected_motor_series)

    def RemoveJoy(self, container, selectedmotorseries, button, SP):
        container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"].pop(button)
        self.UpdateGUI(container, SP, selectedmotorseries)


class JoyCol(tk.Frame,):
    def __init__(self, frame, container, eachProfile,selectedmotorseries):
        rowNum = 1
        tk.Label(frame.joyGrid, text="Button", font="Helvetica 12",justify=tk.LEFT).grid(row=rowNum,column=0)
        tk.Label(frame.joyGrid, text="Command", font="Helvetica 12",justify=tk.LEFT).grid(row=rowNum,column=1)
        rowNum = rowNum + 1
        frame.myJoy = []
        for eachButton in eachProfile.keys():
            frame.myJoy.append(JoyRow(frame, container, eachButton, rowNum, eachProfile, selectedmotorseries))
            rowNum = rowNum + 1
        add_button = tk.Button(frame.joyGrid,text="Add Button",command= lambda: self.AddButton(frame, container, selectedmotorseries))
        add_button.grid(row=rowNum,column=2)

    def UpdateGUI(self, container, SP):
        SP.joyGrid.destroy()
        SP.myJoy = []
        SP.PopulateGrid(container)

    def AddButton(self, frame, container, selectedmotorseries):
        emptyKey = " "
        while emptyKey in container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"].keys():
            emptyKey = emptyKey + " "
        container.loaded_settings["motors_configurations"][selectedmotorseries]["joystick"][emptyKey] = ""
        frame.UpdateGrid(container,selectedmotorseries)  

  
class TempDeckName(tk.Entry,):
    def __init__(self, frame, container, string):
        super().__init__(frame.TempDeckGrid)
        self.text = string
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdatePortPattern(container, frame))

    def UpdatePortPattern(self, container, frame):
        old_key = self.text
        new_key = self.get()
        old_value = container.loaded_settings["temp_decks"].pop(old_key)
        container.loaded_settings["temp_decks"][new_key] = old_value
        frame.UpdateGUI(container)


class TempDeckSerial(tk.Entry,):
    def __init__(self, frame, container, string, eachTemp):
        super().__init__(frame.TempDeckGrid)
        self.insert(tk.END,string)
        self.bind('<FocusOut>',lambda x: self.UpdateSerial(container,eachTemp, self.get()))

    def UpdateSerial(self, container, deckname, new_value):
        container.loaded_settings["temp_decks"][deckname]["com"] = new_value


class TempdeckRow(tk.Frame,):
    def __init__(self, frame, container, eachTemp, rowNum):
        super().__init__(frame.TempDeckGrid)
        myName = TempDeckName(frame, container, eachTemp)
        myName.grid(row=rowNum,column=0)

        mySer = TempDeckSerial(frame, container, container.loaded_settings["temp_decks"][eachTemp]["com"], eachTemp)
        mySer.grid(row=rowNum,column=1)

        delete = tk.Button(frame.TempDeckGrid,text="Remove Tempdeck",command= lambda: self.RemoveTempdeck(frame, container, eachTemp))
        delete.grid(row=rowNum,column=2)
    
    def RemoveTempdeck(self, frame, container, eachTemp):
        container.loaded_settings["temp_decks"].pop(eachTemp)
        frame.UpdateGUI(container)


class Tempdecks(tk.Frame,):
    def __init__(self, container):
        super().__init__(container)
        self.PopulateTempdecks(container)

    def PopulateTempdecks(self, container):
        self.TempDeckGrid = tk.Frame(self)
        self.TempDeckGrid.pack(side=tk.TOP)
        tk.Label(self.TempDeckGrid, text="Tempurature Decks", font="Helvetica 14",justify=tk.LEFT).grid(row=0,column=0)
        self.myTempdecks = []
        i = 2
        tk.Label(self.TempDeckGrid, text="Name", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=0)
        tk.Label(self.TempDeckGrid, text="Com Port", font="Helvetica 10",justify=tk.LEFT).grid(row=1,column=1)
        for eachTemp in container.loaded_settings.get("temp_decks").keys():
            self.myTempdecks.append(TempdeckRow(self, container, eachTemp, i))
            i = i + 1
        add_button = tk.Button(self.TempDeckGrid,text="Add Tempdeck",command= lambda: self.AddTempdeck(container))
        add_button.grid(row=i,column=2)
    
    def AddTempdeck(self, container):
        container.loaded_settings["temp_decks"]["new"] = {"com":""}
        self.UpdateGUI(container)

    def UpdateGUI(self, container):
        self.TempDeckGrid.destroy()
        self.myTempdecks = []
        self.PopulateTempdecks(container)

    def RemoveTempdeck(self, container, portIndex):
        container.loaded_settings["temp_decks"].pop(portIndex)
        self.UpdateGUI(container)


class Configuration(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
        self.grab_set()
        self.title("Settings and Configuration")

        # sets the geometry of toplevel
        self.geometry("1000x1800")
        self.state("zoomed")
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack( side = tk.RIGHT, fill = tk.Y )
        settingsBar = tk.Frame(self)
        settingsBar.pack(side=tk.TOP)
        self.Canv = tk.Canvas(self, width=1000, height = 1800, scrollregion=(0,0,1000,1800)) # width=1256, height = 1674)
        self.Canv.pack(side=tk.TOP) # added sticky

        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.popCanv = tk.Frame(self.Canv)
        interior_id = self.Canv.create_window(0, 0, window=self.popCanv, anchor=tk.NW)
        self.rowconfigure(0, weight=1) 
        self.columnconfigure(0, weight=1)
        
        self.settings_filename_to_open = DEFAULT_SETTINGS
        
        # A Label widget to show in toplevel
        self.connectButton = tk.Button(settingsBar, activebackground="yellow",text="Connect", command=lambda: self.Connect(coordinator), justify=tk.LEFT)
        self.connectButton.grid(row=0,column=0)
        self.connectButton.configure(bg="gray")
        self.disconnectButton = tk.Button(settingsBar, activebackground="red", text="Disconnect", command=lambda: self.Disconnect(coordinator), justify=tk.LEFT)
        self.disconnectButton.grid(row=0,column=1)
        tk.Button(settingsBar,text="Clear Settings",command=lambda: self.LoadDefaults(coordinator),justify=tk.LEFT).grid(row=0, column=2)
        tk.Button(settingsBar, text='Import from a Settings File', command=lambda: self.LoadSettings(coordinator), justify=tk.LEFT).grid(row=0, column=3)
        tk.Button(settingsBar,text="Save Settings to File", command=lambda: self.SaveSettings(), justify=tk.LEFT).grid(row=0, column=4)
        
        if coordinator.myModules.settings == None:
            self.popCanv.loaded_settings = coordinator.myModules.read_dictionary_from_file(DEFAULT_SETTINGS)
        else:
            self.popCanv.loaded_settings = coordinator.myModules.settings
            self.connectButton.configure(bg="green")

        self.initialize_frames()

        self.protocol("WM_DELETE_WINDOW", lambda: self.on_closing(coordinator))

    def on_closing(self, coordinator):
        self.destroy()

    def initialize_frames(self):
        self.myPorts = Serial_Ports(self.popCanv)
        self.myPorts.grid(row=0,column=0)
        self.myIns = Inputs(self.popCanv)
        self.myIns.grid(row=1,column=0)
        self.myOuts = Outputs(self.popCanv)
        self.myOuts.grid(row=2,column=0)
        self.Switches = Switches(self.popCanv)
        self.Switches.grid(row=3,column=0)
        self.myValves = Valves(self.popCanv)
        self.myValves.grid(row=4,column=0)
        self.mySelectors = Selectors(self.popCanv)
        self.mySelectors.grid(row=5,column=0)
        self.myMotors = Motor_Sets(self.popCanv)
        self.myMotors.grid(row=6,column=0)
        self.myTempDecks = Tempdecks(self.popCanv)
        self.myTempDecks.grid(row=7,column=0)

    def Disconnect(self, coordinator):
        coordinator.myModules.disconnect()
        self.connectButton.configure(bg="gray")

    def Connect(self, coordinator):
        if coordinator.myModules.status == "connected" or coordinator.myModules.status == "attempted": 
            self.Disconnect(coordinator)
        self.connectButton.configure(bg="red")
        coordinator.myModules.status = "attempted"
        print("\nConnecting")
        coordinator.myModules.load_settings_from_dictionary(self.popCanv.loaded_settings)
        coordinator.myModules.settings = self.popCanv.loaded_settings
        coordinator.myModules.status = "connected"
        self.connectButton.configure(bg="green")
            
    def LoadDefaults(self, coordinator):
        self.Canv.destroy()
        
        self.Canv = tk.Canvas(self, width=1000, height = 1800, scrollregion=(0,0,1000,1800)) #width=1256, height = 1674)
        self.Canv.pack(side=tk.TOP)#added sticky

        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.popCanv = tk.Frame(self.Canv)
        interior_id = self.Canv.create_window(0, 0, window=self.popCanv, anchor=tk.NW)
        self.popCanv.loaded_settings = coordinator.myModules.read_dictionary_from_file(DEFAULT_SETTINGS)
        
        self.initialize_frames()
            
    def LoadConfigurations(self, coordinator, filename):
        self.Canv.destroy()
        
        self.Canv = tk.Canvas(self, width=1000, height = 1800,
                         scrollregion=(0,0,1000,1800)) #width=1256, height = 1674)
        self.Canv.pack(side=tk.TOP) #added sticky

        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.popCanv = tk.Frame(self.Canv)
        interior_id = self.Canv.create_window(0, 0, window=self.popCanv,
                                           anchor=tk.NW)
        self.popCanv.loaded_settings = coordinator.myModules.read_dictionary_from_file(filename)
        print(self.popCanv.loaded_settings["temp_decks"])
        
        self.initialize_frames())
        
    def AddConfigurations(self, coordinator, new_dict):
        old_dict = self.popCanv.loaded_settings
        
        self.Canv.destroy()
        
        self.Canv = tk.Canvas(self, width=1000, height = 1800,
                         scrollregion=(0,0,1000,1800)) #width=1256, height = 1674)
        self.Canv.pack(side=tk.TOP)#added sticky

        self.scrollbar.config(command=self.Canv.yview)
        self.Canv.config(yscrollcommand = self.scrollbar.set)
        self.popCanv = tk.Frame(self.Canv)
        interior_id = self.Canv.create_window(0, 0, window=self.popCanv,
                                           anchor=tk.NW)
        self.popCanv.loaded_settings = old_dict

        self.popCanv.loaded_settings = self.addToDict(old_dict, new_dict)
                                                                                                                                                              
        self.initialize_frames()
    
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

        new_file = filedialog.askopenfilename(parent=self, title='Open a file', initialdir='settings', filetypes=filetypes)

        if new_file == "":  # in the event of a cancel 
            return
        
        self.settings_filename_to_open = new_file

        new_dict = coordinator.myModules.read_dictionary_from_file(self.settings_filename_to_open)
        self.AddConfigurations(coordinator, new_dict)

    def SaveSettings(self):
        filetypes = (
            ('json files', '*.json'),
            ( 'All files', '*')
        )

        new_file =  filedialog.asksaveasfile(parent=self, title='Save Settings', initialdir='settings', filetypes=filetypes)
        
        if new_file == None:  # in the event of a cancel 
            return
        
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

