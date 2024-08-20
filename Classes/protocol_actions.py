import datetime 
import json
import time
import threading


from Classes.module_files.labware import Labware
import datetime

MS_WAIT_TIMEOUT = 20 # Time allowed before ignoring he triggering of the MS
MS_ANALYZE_TIMEOUT = 40 # Time we allow for the MS to stop analyzing the previous cycle and going back to waiting so that it can start analyzing the current sample
MS_RELAY = 1
LC_RELAY = 0
MS_INPUT = "D14"
MS_INPUT_PORT = 0
DEFAULT_OUTPUT = 0



class ProtocolActions:
    def __init__(self, coordinator):
        self.myCoordinator = coordinator

    # Basic Commands

    def move_to_well(self, stage, plate, well):

        #find location in 
        location: tuple = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(plate), well)
        self.myCoordinator.myLogger.info(f"Moving to '{well}' at '{location}'")

        self.myCoordinator.myModules.myStages[stage].move_to(location)

    def move_to_location(self, stage, location_name):

        #find location in
        labware: Labware = self.myCoordinator.myModules.myStages[stage].myLabware
        self.myCoordinator.myLogger.info(f"Moving to '{location_name}' at '{labware.custom_locations[location_name]}'")
        location = self.myCoordinator.myModules.myStages[stage].myLabware.custom_locations[location_name]

        self.myCoordinator.myModules.myStages[stage].move_to(location)

    def aspirate_in_place(self, stage, volume, speed): 
        self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
        self.myCoordinator.myModules.myStages[stage].step_syringe_motor_up(volume=volume, speed=speed)
    
    def dispense_in_place(self, stage, volume, speed): 
        self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
        self.myCoordinator.myModules.myStages[stage].step_syringe_motor_down(volume=volume, speed=speed)


    # Compounded Commands (convenient combinations of basic commands)
       
    def aspirate_from_wells(self, stage, well_plate_index, wells, volume, speed):

        wells = wells.replace(" ","")
        well_list = wells.split(",")
        
        for well in well_list:

            # get well xyz coordinates
            location = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(well_plate_index), well) 

            self.myCoordinator.myLogger.info(f"Moving to wellplate '{well_plate_index}' at {location}")
            self.myCoordinator.myModules.myStages[stage].move_to(location)

            self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
            self.myCoordinator.myModules.myStages[stage].step_syringe_motor_up(volume=volume, speed=speed)

    def aspirate_from_location(self, stage, location_name, volume, speed):
        self.move_to_location(stage, location_name)
        self.aspirate_in_place(stage, volume, speed)

    def dispense_to_wells(self, stage, well_plate_index, wells, volume, speed):

        wells = wells.replace(" ","")
        well_list = wells.split(",")
        
        for well in well_list:

            # get well xyz coordinates
            location = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(well_plate_index), well) # Tuple (x,y,z) 
            
            self.myCoordinator.myLogger.info(f"Moving to wellplate '{well_plate_index}' at {location}")
            self.myCoordinator.myModules.myStages[stage].move_to(location)

            self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
            self.myCoordinator.myModules.myStages[stage].step_syringe_motor_down(volume=volume, speed=speed)

    def dispense_to_location(self, stage, location_name, volume, speed):
        self.move_to_location(stage, location_name)
        self.dispense_in_place(stage, volume, speed)

    '''
    # def aspirate_from_well(self, stage, well_plate_index, well, volume, speed):

    #     # get well xyz coordinates
    #     location = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(well_plate_index), well) 

    #     self.myCoordinator.myLogger.info(f"Moving to wellplate '{well_plate_index}' at {location}")
    #     self.myCoordinator.myModules.myStages[stage].move_to(location)

    #     self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")
    #     self.myCoordinator.myModules.myStages[stage].step_syringe_motor_up(volume=volume, speed=speed)

    # def dispense_to_well(self, stage, well_plate_index, well, volume, speed):
        
    #     # get well xyz coordinates
    #     location = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(well_plate_index), well) # Tuple (x,y,z) 
    #     self.myCoordinator.myLogger.info(f"Moving to wellplate '{well_plate_index}' at {location}")

    #     self.myCoordinator.myModules.myStages[stage].move_to(location)

    #     self.myCoordinator.myLogger.info(f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min")

    #     self.myCoordinator.myModules.myStages[stage].step_syringe_motor_down(volume=volume, speed=speed)
    '''


    ## LC-MS Commands (specify target wells at run time)

    def aspirate_samples(self, volume, speed, wait_seconds):
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
            self.aspirate_in_place(stage, volume, speed)
            if not wait_seconds==0:
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
            self.dispense_in_place(stage, volume, speed)
            if not wait_seconds==0:
                self.wait(wait_seconds)

    def pool_samples(self, volume, speed, spread, wait_seconds):
        '''
        this is a mass spec method for pooling labeled samples. 
        The capillary needle must be moved around to collect all pico-well samples. 
        The needle starts in the middle of the well just like other sample commands.
        after dispensing liquid, the needle moves a chosen "spread" distance in the y axis.
        it then makes a circuit around the well before aspirating the sample once more.
        '''
        # need stage, plate, well
        stage = self.myCoordinator.myReader.current_run["Stage"]
        plate = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
        wells: str = self.myCoordinator.myReader.current_run["Well"]
        spread = float(spread)
        
        wells.replace(" ", "")

        for well in wells.split(","):
            self.move_to_well(stage, plate, well)
            self.dispense_in_place(stage, volume, speed)

            # coordinates of well center
            location: tuple = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(plate), well)
            x = location[0] 
            y = location[1]
            z = location[2] 
            
            # move "up" by spread distance (mm)
            y = y + spread
            new_location = (x,y,z)
            
            self.myCoordinator.myModules.myStages[stage].small_move_xy(new_location, move_speed=spread)

            # move "left" by spread distance (mm)
            x = x + spread
            new_location = (x,y,z)
            self.myCoordinator.myModules.myStages[stage].small_move_xy(new_location, move_speed=spread)

            # move "down" by 2x spread distance (mm)
            y = y - (2*spread)
            new_location = (x,y,z)
            self.myCoordinator.myModules.myStages[stage].small_move_xy(new_location, move_speed=spread)

            # move "right" by 2x spread distance (mm)
            x = x - (2*spread)
            new_location = (x,y,z)
            self.myCoordinator.myModules.myStages[stage].small_move_xy(new_location, move_speed=spread)

            # move "up" by 2x spread distance (mm)
            y = y + (2*spread)
            new_location = (x,y,z)
            self.myCoordinator.myModules.myStages[stage].small_move_xy(new_location, move_speed=spread)

            # move "left" by spread distance (mm)
            x = x + spread
            new_location = (x,y,z)
            self.myCoordinator.myModules.myStages[stage].small_move_xy(new_location, move_speed=spread)
            
            self.aspirate_in_place(stage, volume, speed)
            self.wait(wait_seconds)

    '''
    # def aspirate_sample(self, volume, speed, wait_seconds):
    #     
    #     # this is a mass spec method. 
    #     # it retrieves the current sample specs from the method reader, and unpackages them.
    #     # it moves to the well, waits for a specified time, aspirates the volume, waits again.
    #     
    #     # need stage, plate, well
    #     stage = self.myCoordinator.myReader.current_run["Stage"] 
    #     plate = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
    #     well = self.myCoordinator.myReader.current_run["Well"]

    #     self.move_to_well(stage, plate, well)
    #     self.wait(wait_seconds)
    #     self.aspirate_in_place(stage, volume, speed)
    #     self.wait(wait_seconds)

    # def dispense_to_sample(self, volume, speed, wait_seconds):
    #     
    #     # this is a mass spec method. 
    #     # it retrieves the current sample specs from the method reader, and unpackages them.
    #     # it moves to the well, waits for a specified time, aspirates the volume, waits again.
    #     
    #     # need stage, plate, well
    #     stage = self.myCoordinator.myReader.current_run["Stage"] 
    #     plate = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
    #     well = self.myCoordinator.myReader.current_run["Well"]

    #     self.move_to_well(stage, plate, well)
    #     self.wait(wait_seconds)
    #     self.dispense_in_place(stage, volume, speed)
    #     self.wait(wait_seconds)
    '''
    

    ## Syringe Commands

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

    
    # Valve Commands

    def valve_to_run(self, valve_index): 
        self.myCoordinator.myModules.my2PosValves[int(valve_index)].to_runPosition()

    def valve_to_load(self, valve_index): 
        self.myCoordinator.myModules.my2PosValves[int(valve_index)].to_loadPosition()
    
    def move_selector(self, valve_index, position):
        self.myCoordinator.myModules.mySelectors[int(valve_index)].move_to_position(int(position))


    # Relay Commands

    def LC_contact_closure(self, Relay = LC_RELAY):
        if not self.myCoordinator.myReader.stop_run == True:
            self.myCoordinator.myLogger.info("THREAD: self.myCoordinator.LC_contact_closure()")  
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_on() # you need to pass in the number relay you want to switch
                                            # in this case the LC is connected to relay 2
            # time.sleep(2) # wait half second to make sure signal had time to start pump
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_off() # turn off so it can be turned on again in the next loop
            # time.sleep(2) # wait half second to make sure signal had time to start pump
            #try twice
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_on() # you need to pass in the number relay you want to switch
                                            # in this case the LC is connected to relay 2
            # time.sleep(2) # wait half second to make sure signal had time to start pump
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_off() # turn off so it can be turned on again in the next loop
            # time.sleep(2) # wait half second to make sure signal had time to start pump
        else:
            print("Stopping")

    def MS_contact_closure(self, Relay = MS_RELAY, Input = MS_INPUT, Port = MS_INPUT_PORT): 
        wait_to_analyze_timer = 0
        analyze_to_wait_timer = 0
        MS_Ready = True
        if not self.myCoordinator.myReader.stop_run == True:
            self.myCoordinator.myLogger.info("THREAD: self.myCoordinator.MS_contact_closure()")
            pin_state = self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input)
            while not(pin_state): #start connected to ground
             #   self.ms_indicator
                time.sleep(1.5) 
                pin_state = self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input)

                analyze_to_wait_timer += 1
                if (analyze_to_wait_timer >= MS_ANALYZE_TIMEOUT):
                    self.myCoordinator.myLogger.error(f"MS TIMEOUT: MS not ready (still analyzing) after {MS_ANALYZE_TIMEOUT} seconds")
                    MS_Ready = False
                    break
                
                # print(pin_state)
                if self.myCoordinator.myReader.stop_run == True:
                    break
                self.myCoordinator.myLogger.info("MS just triggered!")
            if MS_Ready:
                self.myCoordinator.myLogger.info(f"MS IS READY TO BE TRIGGERED, ATTEMPTING CONTACT CLOSURE")
            while (pin_state or not MS_Ready):
                pin_state = self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input)
                wait_to_analyze_timer += 4
                self.myCoordinator.myModules.myRelays[int(Relay)].relay_on() # you need to pass in the number relay you want to switch
                                        # in this case the MS is connected to relay 2
                # time.sleep(2) # wait half second to make sure signal had time to start pump
                self.myCoordinator.myModules.myRelays[int(Relay)].relay_off() # turn off so it can be turned on again in the next loop
                # time.sleep(2) # wait half second to make sure signal had time to start pump
                # print(pin_state)
                if (wait_to_analyze_timer >= MS_WAIT_TIMEOUT):
                    self.myCoordinator.myLogger.error(f"MS TIMEOUT: MS did not trigger after {MS_WAIT_TIMEOUT} seconds")
                    return "Not triggerd"
                else:
                    pass
                if self.myCoordinator.myReader.stop_run == True:
                    break
                self.myCoordinator.myLogger.info("MS just triggered!")
#            return "Successful"
        else:
            self.myCoordinator.myLogger.info("Skipping MS Contact Closure")
          #  return "Skipped MS Trigger"

    def Wait_Contact_Closure(self, Logic, Input = MS_INPUT, Port = MS_INPUT_PORT):
        Logic = Logic == "True"
        pin_state = self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input)
        #print((Logic))
        while (pin_state != Logic):
            time.sleep(1.5)
            pin_state = self.myCoordinator.myModules.myPorts[int(Port)].getPinState(Input)            
            # print(pin_state)
            if self.myCoordinator.myReader.stop_run == True:
                break
        #print("Contact Closure")


    # Other Commands

    def wait(self, seconds):
        # pauses system, but checks for stop_run
        # t = time.localtime()
        current_time = datetime.datetime.now().strftime("%I:%M %p")  # uses AM/PM time format
        seconds = int(seconds)
        minutes = 0
        hours = 0
        if seconds > 1:
            if seconds > 60:
                minutes = seconds//60
                seconds_remainder = seconds%60
            if minutes > 60:
                hours = minutes//60
                minutes = minutes%60
            print(f"Wait called at {current_time}: Wait for {hours} h, {minutes} min, {seconds_remainder} s")
        seconds_waited = 0
        while seconds_waited < int(seconds) and not self.myCoordinator.myReader.stop_run == True:
            time.sleep(1)
            seconds_waited = seconds_waited + 1

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

            # calls correct function in coordinator & unpacks the parameters list with (*params): logs each parameter
            getattr(self.myCoordinator.actionOptions, command['type'])(*params)


    # Dual Column Commands

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
    
    def set_relay_side(self, Relay=LC_RELAY, value="Left"):
        if value == "Left" or value == "LEFT" or value == "left":
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_off()
        elif value == "Right"or value == "RIGHT" or value == "right":
            self.myCoordinator.myModules.myRelays[int(Relay)].relay_on()
        else:
            print(f"{value} is not a valid side")



    
   