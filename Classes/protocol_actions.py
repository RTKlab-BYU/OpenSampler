import json
import time
import os
import threading
print(os.getcwd())
from Classes.module_files.labware import Labware

MS_WAIT_TIMEOUT = 15 # Time allowed before ignoring he triggering of the MS
MS_ANALYZE_TIMEOUT = 45 # Time we allow for the MS to stop analyzing the previous cycle and going back to waiting so that it can start analyzing the current sample
MS_RELAY = 1
LC_RELAY = 0
MS_INPUT = "D14"
MS_INPUT_PORT = 0
DEFAULT_OUTPUT = 0


class ProtocolActions:
    def __init__(self, coordinator):
        self.myCoordinator = coordinator


    def dispense_to_sample(self, volume, speed, wait_seconds):
        '''
        this is a mass spec method. 
        it retrieves the current sample specs from the method reader, and unpackages them.
        it moves to the well, waits for a specified time, aspirates the volume, waits again.
        '''
        # need stage, plate, well
        stage = self.myCoordinator.myReader.current_run["Stage"] 
        plate = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
        well = self.myCoordinator.myReader.current_run["Well"]

        self.move_to_well(stage, plate, well)
        self.wait(wait_seconds)
        self.dispense_in_place(stage, volume, speed)
        self.wait(wait_seconds)

    def dispense_to_samples(self, volume, speed, wait_seconds):
        '''
        this is a mass spec method. 
        it retrieves the current sample specs from the method reader, and unpackages them.
        it moves to the well, waits for a specified time, aspirates the volume, waits again.
        '''
        # need stage, plate, well
        stage = self.myCoordinator.myReader.current_run["Stage"]
        plate = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
        wells: str = self.myCoordinator.myReader.current_run["Well"]
        
        wells = wells.replace(" ", "")

        for well in wells.split(","):
            self.move_to_well(stage, plate, well)
            self.wait(wait_seconds)
            self.dispense_in_place(stage, volume, speed)
            self.wait(wait_seconds)

    def collect_sample(self, volume, speed, wait_seconds):
        '''
        this is a mass spec method. 
        it retrieves the current sample specs from the method reader, and unpackages them.
        it moves to the well, waits for a specified time, aspirates the volume, waits again.
        '''
        # need stage, plate, well
        stage = self.myCoordinator.myReader.current_run["Stage"] 
        plate = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
        well = self.myCoordinator.myReader.current_run["Well"]

        self.move_to_well(stage, plate, well)
        self.wait(wait_seconds)
        self.aspirate_in_place(stage, volume, speed)
        self.wait(wait_seconds)

    def collect_samples(self, volume, speed, wait_seconds):
        '''
        this is a mass spec method. 
        it retrieves the current sample specs from the method reader, and unpackages them.
        it moves to the well, waits for a specified time, aspirates the volume, waits again.
        '''
        # need stage, plate, well
        stage = self.myCoordinator.myReader.current_run["Stage"]
        plate = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
        wells: str = self.myCoordinator.myReader.current_run["Well"]
        
        wells.replace(" ", "")

        for well in wells.split(","):
            self.move_to_well(stage, plate, well)
            self.wait(wait_seconds)
            self.aspirate_in_place(stage, volume, speed)
            self.wait(wait_seconds)
    

    def move_to_custom_location(self, stage, location_name):

        #find location in
        labware: Labware = self.myCoordinator.myModules.myStages[stage].myLabware
        self.myCoordinator.myLogger.info(f"Moving to '{location_name}' at '{labware.custom_locations[location_name]}'")
        location = self.myCoordinator.myModules.myStages[stage].myLabware.custom_locations[location_name]

        self.myCoordinator.myModules.myStages[stage].move_to(location)

    def move_to_well(self, stage, plate, well):

        #find location in 
        location: tuple = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(plate), well)
        self.myCoordinator.myLogger.info(f"Moving to '{well}' at '{location}'")

        self.myCoordinator.myModules.myStages[stage].move_to(location)
            
    def aspirate_from_well(self, stage, well_plate_index, well, volume, speed):

        # get well xyz coordinates
        location = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(well_plate_index), well) 
        # x,y,z = location.split(" ")
        # location = tuple([float(x),float(y),float(z)])

        self.myCoordinator.myLogger.info(f"Moving to wellplate '{well_plate_index}' at {location}")
        self.myCoordinator.myModules.myStages[stage].move_to(location)

        self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
        self.myCoordinator.myModules.myStages[stage].step_syringe_motor_up(volume, speed)
        
    def dispense_to_well(self, stage, well_plate_index, well, volume, speed):
        
        # get well xyz coordinates
        location = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(well_plate_index), well) # Tuple (x,y,z) 
        self.myCoordinator.myLogger.info(f"Moving to wellplate '{well_plate_index}' at {location}")
        # x,y,z = location.split(" ")
        # location = tuple([float(x),float(y),float(z)])

        self.myCoordinator.myModules.myStages[stage].move_to(location)

        self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
        self.myCoordinator.myModules.myStages[stage].step_syringe_motor_down(volume, speed)

    def dispense_to_wells(self, stage, well_plate_index, wells, volume, speed):

        well_list = wells.split(",")
        
        for well in well_list:

            # get well xyz coordinates
            location = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(well_plate_index), well) # Tuple (x,y,z) 
            self.myCoordinator.myLogger.info(f"Moving to wellplate '{well_plate_index}' at {location}")
            # x,y,z = location.split(" ").split(", ")
            # location = tuple([float(x),float(y),float(z)])
            
            self.myCoordinator.myModules.myStages[stage].move_to(location)

            self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
            self.myCoordinator.myModules.myStages[stage].step_syringe_motor_down(volume, speed)
    
    def aspirate_in_place(self, stage, volume, speed): 
        self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
        self.myCoordinator.myModules.myStages[stage].step_syringe_motor_up(volume, speed)
    
    def dispense_in_place(self, stage, volume, speed): 
        self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
        self.myCoordinator.myModules.myStages[stage].step_syringe_motor_down(volume, speed)

    def syringe_to_max(self, stage, nL_min_speed):
        speed = float(nL_min_speed) # pre min to per sec
        max_position = self.myCoordinator.myModules.myStages[stage].myLabware.get_syringe_max()
        self.myCoordinator.myModules.myStages[stage].move_syringe_to(max_position, speed)

    def syringe_to_min(self, stage, nL_min_speed):
        speed = float(nL_min_speed) # pre min to per sec
        min_position = self.myCoordinator.myModules.myStages[stage].myLabware.get_syringe_min()
        self.myCoordinator.myModules.myStages[stage].move_syringe_to(min_position, speed)
    
    def syringe_to_rest(self, stage, nL_min_speed):
        speed = float(nL_min_speed) # pre min to per sec
        rest_position = self.myCoordinator.myModules.myStages[stage].myLabware.get_syringe_rest()
        self.myCoordinator.myModules.myStages[stage].move_syringe_to(rest_position, speed)

    def wait(self, seconds):
        # pauses system, but checks for stop_run
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        print(f"{current_time}: Wait for {int(seconds)} seconds")
        seconds_waited = 0
        while seconds_waited < int(seconds) and not self.myCoordinator.myReader.stop_run == True:
            time.sleep(1)
            seconds_waited = seconds_waited + 1

    def valve_to_run(self, valve_index): 
        self.myCoordinator.myModules.my2PosValves[int(valve_index)].to_runPosition()

    def valve_to_load(self, valve_index): 
        self.myCoordinator.myModules.my2PosValves[int(valve_index)].to_loadPosition()
    
    def move_selector(self, valve_index, position):
        self.myCoordinator.myModules.mySelectors[int(valve_index)].move_to_position(int(position))

    def set_tempdeck(self, tempdeck_name, temperature):
        self.myCoordinator.myModules.myTempDecks[tempdeck_name].start_set_temperature(temperature)

    def run_sub_method(self, scriptName):
        # read file
        with open(scriptName, 'r') as myfile:
            data = myfile.read()
        obj = json.loads(data) # parse file

        
        #loop for all commands in json script
        for command in obj['commands']:
            if self.myCoordinator.myReader.stop_run == True: # check to see if we should stop loading
                break # if stop_run then we break to loop and stop loading

            
            params = command['parameters'] # save command parameters in a list

                
                #calls correct function in coordinator & unpacks the parameters list with (*params): logs each parameter
            getattr(self.myCoordinator.actionOptions, command['type'])(*params)

    def run_sub_method_simultaneously(self, scriptName): #Untracked works better if not necessary
        unmonitored_thread = threading.Thread(target = self.run_sub_method, args=([scriptName])) 
        unmonitored_thread.start()
    
    def start_sub_method(self, scriptName, thread_number): #finer control and tracking for sub_method_simultaneoulsy
        thread_number = int(thread_number)
        while len(self.myCoordinator.myModules.myThreads) < thread_number + 1:
            self.myCoordinator.myModules.myThreads.append(threading.Thread(target = self.wait, args=(30)))
        self.myCoordinator.myModules.myThreads[thread_number] = threading.Thread(target = self.run_sub_method, args=([scriptName])) 
        self.myCoordinator.myModules.myThreads[thread_number].start()

    def wait_sub_method(self, thread_number): 
        thread_number = int(thread_number)
        while len(self.myCoordinator.myModules.myThreads) < thread_number + 1:
            self.myCoordinator.myModules.myThreads.append(threading.Thread(target = self.wait, args=(30)))
        while self.myCoordinator.myModules.myThreads[thread_number].is_alive():
            time.sleep(0.5)

    def MS_contact_closure(self, Relay = MS_RELAY, Input = MS_INPUT, Port = MS_INPUT_PORT): 
        wait_to_analyze_timer = 0
        analyze_to_wait_timer = 0
        MS_Ready = True
        if not self.myCoordinator.myReader.stop_run == True:
            self.myCoordinator.myLogger.info("THREAD: self.myCoordinator.MS_contact_closure()")
            while not(self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input)):
             #   self.ms_indicator
                analyze_to_wait_timer += 1
                if (analyze_to_wait_timer >= MS_ANALYZE_TIMEOUT):
                    self.myCoordinator.myLogger.error(f"MS TIMEOUT: MS not ready (still analyzing) after {MS_ANALYZE_TIMEOUT} seconds")
                    MS_Ready = False
                    break
                time.sleep(1)
            if MS_Ready:
                self.myCoordinator.myLogger.info(f"MS IS READY TO BE TRIGGERED, ATTEMPTING CONTACT CLOSURE")
            while (self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input) or not MS_Ready):
                wait_to_analyze_timer += 1
                self.myCoordinator.myModules.myRelays[int(Relay)].relay_on() # you need to pass in the number relay you want to switch
                                        # in this case the MS is connected to relay 2
                time.sleep(0.5) # wait half second to make sure signal had time to start pump
                self.myCoordinator.myModules.myRelays[int(Relay)].relay_off() # turn off so it can be turned on again in the next loop
                time.sleep(0.5) # wait half second to make sure signal had time to start pump
                if (wait_to_analyze_timer >= MS_WAIT_TIMEOUT):
                    self.myCoordinator.myLogger.error(f"MS TIMEOUT: MS did not trigger after {MS_WAIT_TIMEOUT} seconds")
                    return "Not triggerd"
                else:
                    pass
            self.myCoordinator.myLogger.info("MS just triggered!")
#            return "Successful"
        else:
            self.myCoordinator.myLogger.info("Skipping MS Contact Closure")
          #  return "Skipped MS Trigger"

    def LC_contact_closure(self, Relay = LC_RELAY):
        if not self.myCoordinator.myReader.stop_run == True:
            self.myCoordinator.myLogger.info("THREAD: self.myCoordinator.LC_contact_closure()")  
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_on() # you need to pass in the number relay you want to switch
                                            # in this case the LC is connected to relay 2
            time.sleep(0.5) # wait half second to make sure signal had time to start pump
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_off() # turn off so it can be turned on again in the next loop
            time.sleep(0.5) # wait half second to make sure signal had time to start pump
            #try twice
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_on() # you need to pass in the number relay you want to switch
                                            # in this case the LC is connected to relay 2
            time.sleep(0.5) # wait half second to make sure signal had time to start pump
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_off() # turn off so it can be turned on again in the next loop
            time.sleep(0.5) # wait half second to make sure signal had time to start pump
    
    def set_relay_side(self, Relay=LC_RELAY, value="Left"):
        if value == "Left" or value == "LEFT" or value == "left":
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_off()
        elif value == "Right"or value == "RIGHT" or value == "right":
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_on()
        else:
            print(f"{value} is not a valid side")

    def Wait_Contact_Closure(self, Logic, Input = MS_INPUT, Port = MS_INPUT_PORT):
        Logic = Logic == "True"
        #print(self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input))
       # print((Logic))
        while (self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input) != Logic):
            time.sleep(1)
            if self.myCoordinator.myReader.stop_run == True:
                break
        #print("Contact Closure")

    
   