

from datetime import datetime 
import logging
import json
import pandas as pd
import time

SERIES_TYPE = type(pd.Series(dtype=float))
DATAFRAME_TYPE = type(pd.DataFrame(dtype=float))



class MethodReader:  # should call read from coordinator file
    '''
    This class handles the active que. 
    It verifies some aspects of proposed methods before adding them to the scheduled queue.
    It removes and executes the first entry in the scheduled queue until there are none.
    It monitors the current run for errors, and will end the run and pause the queue if one occurs.
    The current run can be interupted by the user, which automatically pauses the remaining queue.
    The scheduled que can be paused (and resumed) without interupting the current run.
    The scheduled que can be cleared (this will also not interupt the current run).
    These controls are operated from the Queue_Gui.
    '''

    def __init__(self, myCoordinator): # initialize all variables and store needed data

        self.myCoordinator = myCoordinator # this has the functions that move the motors
        
        self.running = False
        self.scheduled_queue = None
        self.queue_paused = False

        self.current_run = None
        self.stop_run = False

        self.current_run_changed = True
        self.scheduled_queue_changed = True
        self.update_pause_button = True
        self.error_during_run = False    
        
    def verify_wells(self, proposed_queue):  # checks all the wells in CSV to make sure they all exist
        if "Well" in proposed_queue:
            for index, row in proposed_queue.iterrows():
                if row["Well"] == '':
                    print(F"\n----- Well not specified in row {index} of proposed queue. -----")
                    return False

                row["Well"] = row["Well"].replace(" ", "")
                for well in row["Well"].split(","):
                    
                    well_exists = self.myCoordinator.myModules.myStages[row["Stage"]].myLabware.check_well_exists(int(row["Wellplate"]), well)

                    if not well_exists:
                        print(f"ERROR: {well} does not exist. Verify that the queue file contains only existing wells", "\n")
                        return False

        return True
    
    def verify_method(self, path_to_method):
        dictionary = {}
        try:
            with open(path_to_method, 'r') as myfile: # open file
                data = myfile.read()
        except:
            print(f"\n------- Method {path_to_method} not found on the record. -------\n")
            return False
        else:
            dictionary = json.loads(data)
            for command in dictionary["commands"]:
                if command["type"] == "move_to_location":  # why this specifically?
                    stage = command["parameters"][0]
                    location_name = command["parameters"][1]
                    stage_exists = stage in self.myCoordinator.myModules.myStages.keys()
                    if stage_exists:
                        location_exists = self.myCoordinator.myModules.myStages[stage].myLabware.check_custom_location_exists(location_name)
                        if location_exists:
                            pass
                        else:
                            print(f"Cannot find location named: {location_name}")
                            return False
                    else:
                        print(f"Cannot find stage named: {stage}")
                        return False
            return True
                    
    def verify_methods(self, proposed_queue: pd.DataFrame): # checks all the json files in CSV to make sure they all exist

        for index, row in proposed_queue.iterrows(): # open and close each json file, if one is missing it will throw error

            if row['Method'] == '':
                    print(F"\n----- Method not specified in row {index} of proposed que. -----")
                    return False
            if self.verify_method(row["Method"]):
                pass
            else:
                print(f"Cannot verify method for row {index}")
                print(f"Method: {row['Method']}")
                return False

        return True

    def verify(self, proposed_queue):  # check compiled runs to make sure its format is valid, sets first gradient, estimate end time
        
        if (len(proposed_queue) == 0):
            print("ERROR EMPTY BATCH")
            return False
        
        # check all cells make sure none are empty & make sure size of each array is same
        
        if not self.verify_wells(proposed_queue): 
            print ("\n------- WELL VERIFICATION FAILED. CANNOT RUN THE PROVIDED QUEUE. -------\n")
            return False  # stops code from running
        
        if not self.verify_methods(proposed_queue):
            print ("\n------- METHOD VERIFICATION FAILED. CANNOT RUN THE PROVIDED QUEUE. -------\n")
            return False  # stops code from running
        
        else:
            
            return True #allows code to continue

    def reset(self):
        self.stop_run = False
        self.queue_paused = False
        self.update_pause_button = True
        self.current_run = None
        self.current_run_changed = True

    def stop_current_run(self):
        print("\n------- Stopping current run. -------\n")
        self.stop_run = True
        self.pause_scheduled_queue()

    def pause_scheduled_queue(self):
        self.queue_paused = True
        self.update_pause_button = True
        print("\n------- Scheduled queue has been paused. -------\n")

    def resume_scheduled_queue(self):
        self.queue_paused = False
        self.update_pause_button = True
        print("\n------- Scheduled queue has been resumed. -------\n")

    def run_next_sample(self):  # reads and calls commands from method to load next sample
        """
            Args:
                well ([str]): [holds the location of the sample we want to load. e.g., 'P1c4']
                methodName ([str]): [the name of the method used to prepare the sample at the well location. e.g., "qc.json"]
        """

        path_to_method = self.current_run["Method"]
        
        
        # read file
        with open(path_to_method, 'r') as myfile:
            json_file = myfile.read()
        method_dict = json.loads(json_file) # parse file

        #loop for all commands in json method
        command_count = 0
        for command in method_dict['commands']:
            command_count += 1

            # check to see if method should be interupted
            if self.stop_run == True: 
                self.pause_scheduled_queue()
                print(f"Did not execute command {command_count} of current run.")
                run_completed = False
                return run_completed 
            else:
                # calls correct function in coordinator & unpacks the parameters list with (*params): logs each parameter
                # try:
                getattr(self.myCoordinator.actionOptions, command['type'])(*command['parameters'])
                # except:
                #     print(f"Error occured trying to execute command row {command_count}: {command['type']}, using parameters: {command['parameters']} ")

        run_completed = True
        return run_completed

    def run_scheduled_methods(self): #main function: handles looping and threads
        """
        This method operates the     
        """
        
        self.methodIndex = 0 # used to track the index of the wellList to get corresponding method. reset for every queue
        self.reset() # reset the stop indicators back to false for every queue
        
        #loop for all wells. this may also include wellplate_wells for QC loading
        self.running = True
        sample_count = 0
        while self.running:
        
            if self.scheduled_queue.shape[0] <= 0:
                break
            
        
            while self.queue_paused:
                if not self.running:
                    # Add any end of run commands if not elsewhere
                    self.current_run = None
                    self.current_run_changed = True
                    print("\nN!!!")
                    print("\n----------------------------------------------------------\n") #white space for output readibility
                    return
                else:
                    continue

            self.reset()
            if type(self.scheduled_queue) == (DATAFRAME_TYPE or SERIES_TYPE):
                pass
            else:
                print("Cannot run an empty queue!\n")
                break

            self.scheduled_queue: pd.DataFrame
            
            self.current_run = self.scheduled_queue.iloc[0] # set the location of 'current_run' to the first row of the scheduled queue
            self.scheduled_queue = self.scheduled_queue.drop(self.scheduled_queue.index[0])
            self.current_run_changed = True
            self.scheduled_queue_changed = True

            time.sleep(3)  # lets display update before continuing
            

            
            now_date = datetime.now().strftime("%m/%d/%Y")
            now_time = datetime.now().strftime("%I:%M %p")  # uses AM/PM time format
            sample_count += 1

            logging.info(f"Running sample {sample_count} with {self.current_run['Method']} \nStarted at {now_time} on {now_date}.")
            print("\n*****************************************************************\n")
            print(f"Sample {sample_count} started at {now_time} on {now_date}.")  

            print(f"\nSamples remaining in scheduled queue: {int(self.scheduled_queue.shape[0])}")
            print("\n*****************************************************************\n")

            run_completed = self.run_next_sample() # run self.current_run, return True if completed without stopping

            if self.error_during_run:
                now_date = datetime.now().strftime("%m/%d/%Y")
                now_time = datetime.now().strftime("%I:%M %p")  # uses AM/PM time format
                logging.info(f"Run for sample {sample_count} !EXPERIENCED AN ERROR! at {now_time} on {now_date}.")
                print(f"\nRun for sample {sample_count} !EXPERIENCED AN ERROR! at {now_time} on {now_date}.")
                self.pause_scheduled_queue()
            
            now_date = datetime.now().strftime("%m/%d/%Y")
            now_time = datetime.now().strftime("%I:%M %p")
                
            if run_completed:
                print("\n*****************************************************************\n")
                logging.info(f"Run for sample {sample_count} completed at {now_time} on {now_date}.")
                print(f"Run for sample {sample_count} completed at {now_time} on {now_date}.")
                print("\n*****************************************************************\n")
            else:
                print("\n*************************** Warning ******************************\n")
                logging.info(f"Run for sample {sample_count} was interupted by user at {now_time} on {now_date}.")
                print(f"Run for sample {sample_count} was interupted by user at {now_time} on {now_date}.")
                print("\n*****************************************************************\n")
                    
            
            print("\n*****************************************************************\n")
            self.current_run = None
            self.current_run_changed = True
            

            
        # End of queue commands
        self.reset()
        time.sleep(3)
        self.running = False

        print("\n------------------------- DONE RUNNING ----------------------------\n")  # white space for output readibility
            
            
            
            
            
        

        
        

        

            
        
            

'''
# comment in or out the following 3 lines to test just this file. 
# You will have to Comment in the psudo coordinator class at the top of this file
Coordinator = Coordinator()
myReader = MethodReader(Coordinator, "queue")
myReader.run("queue")
'''
