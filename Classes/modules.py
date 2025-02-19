
from Classes.module_files.selector_actuator import SelectorActuator
from Classes.module_files.actuator import Actuator
from Classes.module_files.relays import Relays
from Classes.module_files.IOpins import SerialPort
from Classes.module_files.zaber_motor_series import ZaberMotorSeries
from Classes.module_files.OT_driver import OT2_nanotrons_driver
from Classes.module_files.zaber_independent_syringe import ZaberIndependentSyringe
from Classes.module_files.joystick import XboxJoystick
from Classes.module_files.profile import Profile
from Classes.module_files.tempdeck_driver import TempDeck


import os
import json
import logging
from datetime import datetime

LINUX_OS = 'posix'
WINDOWS_OS = 'nt'
LOGGING_LEVEL = logging.ERROR

class Modules:

    def __init__(self):
        self.settings = None
        self.used_stages = {}
        self.myPorts = []
        self.myStages = {}
        self.myJoysticks = []
        self.myJoystickProfiles = {}
        self.my2PosValves = []
        self.myRelays = []
        self.mySwitches = []
        self.mySelectors = []
        self.myFeedbacks = []
        self.myThreads = []
        self.myTempDecks = {}
        self.status = "disconnected"
        pass

    def disconnect(self):
        for eachPort in self.myPorts:
            eachPort.ser.close()
        for eachStage in self.myStages:
            self.myStages[eachStage].close_motors_connection()
        for eachJoystick in self.myJoysticks:
            eachJoystick.stop_listening()
        
        self.settings = None
        self.used_stages = {}
        self.mySwitches=[]
        self.myPorts = []
        self.myStages = {}
        self.myJoysticks = []
        self.myJoystickProfiles = {}
        self.my2PosValves = []
        self.myRelays = []
        self.mySelectors = []
        self.myFeedbacks = []
        self.myTempDecks = {}
        self.myThreads = []
        self.status = "disconnected"


    def add_module_files_from_dictionary(self, dictionary):
        settingsObj = dictionary

        operating_system = ""
        os_recognized = os.name

        if os_recognized == WINDOWS_OS:
            operating_system = "w"
            # print("Windows Operating System Detected")
        elif os_recognized == LINUX_OS:
            operating_system = "r"
        # --------------------- Log files namehead
        folder = "logs/" if os.name == 'posix' else "logs\\"
        now = datetime.now()
        timestamp = now.strftime("%m-%d-%Y---%H-%M-%S")
        log_file_name_head = folder + timestamp

        for eachPort in settingsObj["ports"]:
            print("\nAdding Serial Port " + eachPort["pattern"])
            self.myPorts.append(SerialPort(eachPort["pattern"])) 
        
        for each2PositionActuator in settingsObj["2_position_actuators"]:
            print("\nAdding 2-Position Valve")
            print(each2PositionActuator)
            self.my2PosValves.append(Actuator(self, each2PositionActuator["port"],
                each2PositionActuator["Position A Out"],
                each2PositionActuator["Position B Out"],
                each2PositionActuator["Position A In"],
                each2PositionActuator["Position B In"]))
            
        for eachSelector in settingsObj["selector_actuators"]:
            print("\nAdding Selector Valve")
            print(eachSelector)
            self.mySelectors.append(SelectorActuator(self, 
                eachSelector["port"],
                eachSelector["Home Out"],
                eachSelector["Move Out"],
                eachSelector["Number of Ports"]))
            
        for eachRelay in settingsObj["relays"]:
            print(f"\nAdding a relay controlled by pin {str(eachRelay['pin'])}")
            self.myRelays.append(Relays(self, eachRelay["port"], eachRelay["pin"]))

        for eachInput in settingsObj["feedbacks"]:
            print(f"\nSetting up pin {str(eachInput['pin'])} as an input.")
            self.myFeedbacks.append(eachInput)
            self.myPorts[eachInput["port"]].addInputPin(eachInput["pin"])

        for eachMotorSeries in settingsObj["motors_configurations"].keys():
            if settingsObj["motors_configurations"][eachMotorSeries]["type"] == "Zaber":
                print("\nAdding Zaber Stage")
                self.myStages[eachMotorSeries] = (ZaberMotorSeries(self, settingsObj["motors_configurations"][eachMotorSeries], log_file_name_head, LOGGING_LEVEL))
            elif settingsObj["motors_configurations"][eachMotorSeries]["type"] == "Opentrons":
                print("\nAdding Opentrons Stage")
                self.myStages[eachMotorSeries] = (OT2_nanotrons_driver(myModules=self,motors_config=settingsObj["motors_configurations"][eachMotorSeries]))
            elif settingsObj["motors_configurations"][eachMotorSeries]["type"] == "Zaber - Syringe Only":
                print("\nAdding Zaber Syringe")
                self.myStages[eachMotorSeries] = ZaberIndependentSyringe(self, settingsObj["motors_configurations"][eachMotorSeries], log_file_name_head, )   
            self.myJoystickProfiles[eachMotorSeries] = Profile(settingsObj["motors_configurations"][eachMotorSeries]["joystick"])     

        for eachTempDeck in settingsObj["temp_decks"].keys():
            print("\nAdding Temp Deck")
            self.myTempDecks[eachTempDeck] = TempDeck(settingsObj["temp_decks"][eachTempDeck]["com"])
        self.myJoysticks = [XboxJoystick(operating_system)]
            


    def load_settings_from_file(self, filename):

        self.myPorts = []
        self.myStages = {}
        self.myJoysticks = []
        self.myJoystickProfiles = {}
        self.my2PosValves = []
        self.myRelays = []
        self.mySelectors = []
        self.myFeedbacks = []
        self.myTempDecks = {}
        self.myThreads = []
        
        dictionary = self.read_dictionary_from_file(filename)

        self.add_module_files_from_dictionary(dictionary)

    def load_settings_from_dictionary(self, dictionary):

        self.myPorts = []
        self.myStages = {}
        self.myJoysticks = []
        self.myJoystickProfiles = {}
        self.my2PosValves = []
        self.myRelays = []
        self.mySelectors = []
        self.myFeedbacks = []
        
        self.add_module_files_from_dictionary(dictionary)

    def read_dictionary_from_file(self, filename):
        if filename == "":
            pass
        else:
            # read file
            with open(filename, 'r') as myfile:
                data = myfile.read()
                # parse file
            settingsObj = json.loads(data)
            self.settings = settingsObj
            return settingsObj