import datetime 
import json
import time
import threading

# from Classes.module_files.labware import Labware

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

    def move_to_well(self, stage, plate_index, well, report=True):
        location: tuple = self.myCoordinator.myModules.myStages[stage].myLabware.get_well_location(int(plate_index), well)
        plate_model = self.myCoordinator.myModules.myStages[stage].myLabware.plate_list[int(plate_index)].model
        self.myCoordinator.myModules.myStages[stage].move_to(location)

        if report:
            message = f"Moving to '{well}' of well plate '{plate_model}' (plate index: {plate_index}). XYZ: {location}"
            self.myCoordinator.myLogger.info(message)

    def move_to_location(self, stage, location_name, report=True):
        location = self.myCoordinator.myModules.myStages[stage].myLabware.custom_locations[location_name]
        self.myCoordinator.myModules.myStages[stage].move_to(location)

        if report:
            message = f"Moving to '{location_name}'"
            self.myCoordinator.myLogger.info(message)

    def aspirate_in_place(self, stage, volume, speed, report=True):
        self.myCoordinator.myModules.myStages[stage].step_syringe_motor_up(volume=volume, speed=speed)
        if report:
            message = f"Aspirating {float(volume)} nL at speed {float(speed)} nL/min"
            self.myCoordinator.myLogger.info(message)
    
    def dispense_in_place(self, stage, volume, speed, report=True):
        self.myCoordinator.myModules.myStages[stage].step_syringe_motor_down(volume=volume, speed=speed)
        if report:
            message = f"Dispensing {float(volume)} nL at speed {float(speed)} nL/min"
            self.myCoordinator.myLogger.info(message)


    # Compounded Commands (convenient combinations of basic commands)
       
    def aspirate_from_wells(self, stage, plate_index, wells, volume, speed):
        wells = wells.replace(" ","")
        well_list = wells.split(",")
        plate_model = self.myCoordinator.myModules.myStages[stage].myLabware.plate_list[int(plate_index)].model

        message = f"Aspirating {volume} nL each from well(s) {wells} of wellplate {plate_model} (index: {plate_index})."
        self.myCoordinator.myLogger.info(message)

        for well in well_list:
            self.move_to_well(stage, plate_index, well, report=False)
            self.aspirate_in_place(stage, volume, speed, report=False)
        
    def aspirate_from_location(self, stage, location_name, volume, speed):
        self.move_to_location(stage, location_name, report=False)
        self.aspirate_in_place(stage, volume, speed, report=False)

        message = f"Aspirating {volume} nL from '{location_name}'."
        self.myCoordinator.myLogger.info(message)

    def dispense_to_wells(self, stage, plate_index, wells, volume, speed):
        wells = wells.replace(" ","")
        well_list = wells.split(",")
        plate_model = self.myCoordinator.myModules.myStages[stage].myLabware.plate_list[int(plate_index)].model

        message = f"Dispensing {volume} nL to each well(s) {wells} of wellplate {plate_model} (index: {plate_index})."
        self.myCoordinator.myLogger.info(message)

        for well in well_list:
            self.move_to_well(stage, plate_index, well, report=False)
            self.dispense_in_place(stage, volume, speed, report=False)

    def dispense_to_location(self, stage, location_name, volume, speed):
        self.move_to_location(stage, location_name, report=False)
        self.dispense_in_place(stage, volume, speed, report=False)

        message = f"Dispensing {volume} nL to {location_name}."
        self.myCoordinator.myLogger.info(message)


    ## LC-MS Commands (specify target wells at run time)

    def aspirate_samples(self, volume, speed, wait_seconds):
        '''
        this is a mass spec method. 
        it retrieves the current sample specs from the method reader, and unpackages them.
        it moves to the well, waits for a specified time, aspirates the volume, waits again.
        '''
        # need stage, plate, well
        stage = self.myCoordinator.myReader.current_run["Stage"]
        plate_index = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
        wells: str = self.myCoordinator.myReader.current_run["Well"]
        plate_model = self.myCoordinator.myModules.myStages[stage].myLabware.plate_list[int(plate_index)].model

        wells.replace(" ", "")
        well_list = wells.split(",")

        message = f"Aspirating {volume} nL each from well(s) {wells} of wellplate {plate_model} (index: {plate_index})."
        self.myCoordinator.myLogger.info(message)

        for well in well_list:
            self.move_to_well(stage, plate_index, well, report=False)
            self.aspirate_in_place(stage, volume, speed, report=False)
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
        plate_index = int(self.myCoordinator.myReader.current_run["Wellplate"])  # uses index value for now...
        wells: str = self.myCoordinator.myReader.current_run["Well"]
        plate_model = self.myCoordinator.myModules.myStages[stage].myLabware.plate_list[int(plate_index)].model
        
        wells = wells.replace(" ", "")
        well_list = wells.split(",")

        message = f"Dispensing {volume} nL each to well(s) {wells} of wellplate {plate_model} (index: {plate_index})."
        self.myCoordinator.myLogger.info(message)

        for well in well_list:
            self.move_to_well(stage, plate_index, well, report=False)
            self.dispense_in_place(stage, volume, speed, report=False)
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
    

    ## Syringe Commands

    def syringe_to_max(self, stage, nL_min_speed):
        speed = float(nL_min_speed) # pre min to per sec
        max_position = self.myCoordinator.myModules.myStages[stage].myLabware.get_syringe_max()
        self.myCoordinator.myModules.myStages[stage].move_syringe_to(max_position, speed)

        message = f"Moving syringe to max position"
        self.myCoordinator.myLogger.info(message)

    def syringe_to_min(self, stage, nL_min_speed):
        speed = float(nL_min_speed) # pre min to per sec
        min_position = self.myCoordinator.myModules.myStages[stage].myLabware.get_syringe_min()
        self.myCoordinator.myModules.myStages[stage].move_syringe_to(min_position, speed)

        message = f"Moving syringe to min position"
        self.myCoordinator.myLogger.info(message)
    
    def syringe_to_rest(self, stage, nL_min_speed):
        speed = float(nL_min_speed) # pre min to per sec
        rest_position = self.myCoordinator.myModules.myStages[stage].myLabware.get_syringe_rest()
        self.myCoordinator.myModules.myStages[stage].move_syringe_to(rest_position, speed)

        message = f"Moving syringe to rest position"
        self.myCoordinator.myLogger.info(message)

    
    # Valve Commands

    def valve_to_run(self, valve_index): 
        self.myCoordinator.myModules.my2PosValves[int(valve_index)].to_position_A()

        message = "Sending valve to position A"
        self.myCoordinator.myLogger.info(message)

    def valve_to_load(self, valve_index): 
        self.myCoordinator.myModules.my2PosValves[int(valve_index)].to_position_B()

        message = "Sending valve to position B"
        self.myCoordinator.myLogger.info(message)
    
    def move_selector(self, valve_index, position):
        self.myCoordinator.myModules.mySelectors[int(valve_index)].move_to_position(int(position))

        message = f"Moving selector valve to position {position}."
        self.myCoordinator.myLogger.info(message)


    # Relay Commands

    def LC_contact_closure(self, Relay = LC_RELAY):

        message = "Sending signal to start LC"
        self.myCoordinator.myLogger.info(message)

        self.myCoordinator.myModules.myRelays[int(Relay)].relay_on()
        self.myCoordinator.myModules.myRelays[int(Relay)].relay_off()
        self.myCoordinator.myModules.myRelays[int(Relay)].relay_on() 
        self.myCoordinator.myModules.myRelays[int(Relay)].relay_off() 

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

    def Wait_Contact_Closure(self, Logic, pin, Port=0):
        logic = Logic == "True" # definded by user based on expected input state
        pin_state = self.myCoordinator.myModules.myPorts[int(Port)].getPinState(pin)

        message = f"Awaiting Contact Closure from pin {pin}. Expecting {str(logic)}"
        self.myCoordinator.myLogger.info(message)

        while (pin_state != logic):
            time.sleep(1)
            pin_state = self.myCoordinator.myModules.myPorts[int(Port)].getPinState(pin)

            if self.myCoordinator.myReader.stop_run == True:
                break

        message = "Contact Closure Recieved"
        self.myCoordinator.myLogger.info(message)

    def set_pin(self, pin, logic: str, port=0):
        if logic.upper() == "HIGH":
            self.myCoordinator.myModules.myPorts[int(port)].activatePin(pin)

        elif logic.upper() == "LOW":
            self.myCoordinator.myModules.myPorts[int(port)].deactivatePin(pin)


    # Other Commands

    def wait(self, seconds):
        # pauses system, but checks for stop_run
        # t = time.localtime()
        current_time = datetime.datetime.now().strftime("%I:%M %p")  # uses AM/PM time format
        seconds = int(seconds)
        seconds_remainder = seconds
        minutes = 0
        hours = 0
        if seconds > 1:
            if seconds >= 60:
                minutes = seconds//60
                seconds_remainder = seconds%60
            if minutes >= 60:
                hours = minutes//60
                minutes = minutes%60

            message = f"Wait called at {current_time}: Wait for {hours} h, {minutes} min, {seconds_remainder} s"
            self.myCoordinator.myLogger.info(message)

        seconds_waited = 0
        while seconds_waited < int(seconds) and not self.myCoordinator.myReader.stop_run == True:
            time.sleep(1)
            seconds_waited = seconds_waited + 1

    def set_tempdeck(self, tempdeck_name, temperature):
        try:
            self.myCoordinator.myModules.myTempDecks[tempdeck_name].start_set_temperature(temperature)
            message = f"Setting tempdeck to {temperature} C"
            self.myCoordinator.myLogger.info(message)
        except:
            print("Tempdeck Not Responding")

    def run_sub_method(self, scriptName):
        message = f"Running Submethod: {scriptName}"
        self.myCoordinator.myLogger.info(message)

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



    
   