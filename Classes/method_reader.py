

from datetime import datetime 
import logging
import json
import pandas as pd



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
        self.queue_changed = True

        self.current_run = None
        self.stop_run = False
        
        
        
    def verify_wells(self, proposed_queue):  # checks all the wells in CSV to make sure they all exist
        print("Verifying Wells...")

        for index, row in proposed_queue.iterrows():

            row["Well"] = row["Well"].replace(" ", "")
            for well in row["Well"].split(","):
                
                well_exists = self.myCoordinator.myModules.myStages[row["Stage"]].myLabware.check_well_exists(int(row["Wellplate"]), well)

                if not well_exists:
                    print(f"ERROR: {well} does not exist. Verify that the queue file contains only existing wells", "\n")
                    return False

        print("All Wells Verified!\n")
        return True
    
    def verify_method(self, path_to_method):
        dictionary = {}
        try:
            with open(path_to_method, 'r') as myfile: # open file
                data = myfile.read()
        except:
            print(f"Method {path_to_method} not found on the record")
            return False
        else:
            dictionary = json.loads(data)
            for command in dictionary["commands"]:
                if command["type"] == "move_to_custom_location":  # why this specifically?
                    stage = command["parameters"][0]
                    location_name = command["parameters"][1]
                    stage_exists = stage in self.myCoordinator.myModules.myStages.keys()
                    if stage_exists:
                        nickname_exists = self.myCoordinator.myModules.myStages[stage].myLabware.check_custom_location_exists(location_name)
                        if nickname_exists:
                            print("*", end=" ")
                        else:
                            return False
                    else:
                        print("bad nickname")
                        return False
            return True
                    
    def verify_methods(self, compiled_queue): # checks all the json files in CSV to make sure they all exist
        print("Verifying Method files...")

        for method in compiled_queue["Method"]: # open and close each json file, if one is missing it will throw error
            if self.verify_method(method):
                pass
            else:
                return False
        
        print("SUCCESS!", "\n")
        return True

    def verify(self, scheduled_methods):  # check excel file to make sure its format is valid, sets first gradient, estimate end time
        #method ([str]): [the name of the method used to prepare the sample at the well location. e.g., "qc.json"]
        
        if (len(scheduled_methods) == 0):
            print("ERROR EMPTY BATCH")
            return False
        
        # check all cells make sure none are empty & make sure size of each array is same
        elif  (not self.verify_wells(scheduled_methods)) or (not self.verify_methods(scheduled_methods)) : 
            print ("VERIFICATION FAILED. CANNOT RUN THE PROVIDED QUEUE")
            return False #stops code from running
        
        
        
        else:
            # print out estimated completion time ask for approval
            #self.estimate_end_time()
            
            return True #allows code to continue

    def reset(self):
        self.stop_run = False
        self.queue_paused = False
        self.current_run = None

    def stop_current_run(self):
        print("\nStopping current run...\n")
        self.stop_run = True

    def pause_scheduled_queue(self):
        self.queue_paused = True
        print("\nScheduled queue has been paused.")

    def resume_scheduled_queue(self):
        self.queue_paused = False
        print("\nScheduled queue has been resumed.")

    def run_next_sample(self):  # reads and calls commands from method to load next sample
        """
            Args:
                well ([str]): [holds the location of the sample we want to load. e.g., 'P1c4']
                methodName ([str]): [the name of the method used to prepare the sample at the well location. e.g., "qc.json"]
        """

        path_to_method = self.current_run["Method"]
        
        
        # read file
        with open(path_to_method, 'r') as myfile:
            data = myfile.read()
        obj = json.loads(data) # parse file

        #loop for all commands in json method
        for command in obj['commands']:

            # check to see if method should be interupted
            if self.stop_run == True: 
                self.pause_scheduled_queue()
                run_completed = False
                return run_completed 
            else:
                # calls correct function in coordinator & unpacks the parameters list with (*params): logs each parameter
                getattr(self.myCoordinator.actionOptions, command['type'])(*command['parameters'])

        run_completed = True
        return run_completed

    def run_scheduled_methods(self): #main function: handles looping and threads
        """
        This method operates the     
        """
        print("") #Add line to make output easier to read
        
        self.methodIndex = 0 # used to track the index of the wellList to get corresponding method. reset for every queue
        self.reset() # reset the stop indicators back to false for every queue
        
        #loop for all wells. this may also include wellplate_wells for QC loading
        self.running = True
        sample_count = 0
        while self.running:
        

            
        
            while self.queue_paused:
                if not self.running:
                    # Add any end of run commands if not elsewhere
                    self.current_run = None
                    print("\nN!!!")
                    print("\n----------------------------------------------------------\n") #white space for output readibility
                    return
                else:
                    continue

            self.reset()
            if self.scheduled_queue == None:
                break

            self.scheduled_queue: pd.DataFrame
            if self.scheduled_queue.shape[0] > 0:
                
                self.current_run = self.scheduled_queue.iloc[0] # set the location of 'current_run' to the first row of the scheduled queue
                self.scheduled_queue = self.scheduled_queue.drop(self.scheduled_queue.index[0])
                self.queue_changed = True
                
                now_date = datetime.now().strftime("%m/%d/%Y")
                now_time = datetime.now().strftime("%H:%M %p")
                sample_count += 1

                logging.info(f"Run for sample {sample_count} started at {now_time} on {now_date}.")
                print("\n*****************************************************************\n")
                print(f"\nRun for sample {sample_count} started at {now_time} on {now_date}.")  

                logging.info(f'Running sample {sample_count} with {self.current_run["Method"]}') # print message stating that a method has begun
                print(f"\nRunning Sample {sample_count}. \nSamples remaining in scheduled queue: {int(self.scheduled_queue.shape[0])}")

                try:
                    run_completed = self.run_next_sample() # run self.current_run, return True if completed without stopping
                except:
                    now_date = datetime.now().strftime("%m/%d/%Y")
                    now_time = datetime.now().strftime("%I:%M %p")
                    logging.info(f"Run for sample {sample_count} !EXPERIENCED AN ERROR! at {now_time} on {now_date}.")
                    print(f"\nRun for sample {sample_count} !EXPERIENCED AN ERROR! at {now_time} on {now_date}.")
                    self.pause_scheduled_queue()
                else:
                    now_date = datetime.now().strftime("%m/%d/%Y")
                    now_time = datetime.now().strftime("%I:%M %p")
                    
                    if run_completed:
                        logging.info(f"Run for sample {sample_count} completed at {now_time} on {now_date}.")
                        print(f"\nRun for sample {sample_count} completed at {now_time} on {now_date}.")
                    else:
                        logging.info(f"Run for sample {sample_count} was interupted by user at {now_time} on {now_date}.")
                        print(f"\nRun for sample {sample_count} was interupted by user at {now_time} on {now_date}.")
                finally:
                    print("\n*****************************************************************\n")
                    self.current_run = None
            else:
                break

            
        # End of queue commands
        self.current_run = None
        self.running = False
        self.queue_changed = True
        # 

        print("\n     DONE!!!")
        print("\n----------------------------------------------------------\n") #white space for output readibility
            
            
            
            
            
        

        # self.get_method_times(self.methodList[self.methodIndex])
        
        

        

            
        
            

'''
# comment in or out the following 3 lines to test just this file. 
# You will have to Comment in the psudo coordinator class at the top of this file
Coordinator = Coordinator()
myReader = MethodReader(Coordinator, "queue")
myReader.run("queue")
'''
