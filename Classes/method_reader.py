from Classes.stopIndicator import StopIndicator

import time
import logging
import json


'''

'''

class MethodReader:  #should call read from coordinator file
    def __init__(self, myCoordinator, queue): # initialize all variables and store needed data
        # you may need to also pass in a coordinator object to access the function names 
        self.myCoordinator = myCoordinator # this has the functions that move the motors
        self.myStopIndicator = StopIndicator() # holds values for stop values
        # self.emptyTimingValues = ScriptTimingValues(0, 0, 0, 0, 0) # make object with zero values to fill array at start

        self.methodIndex = 0 # this lets you know what number sample you are on. 
        self.queueName = "queues//queue.csv" # stores name of the queue
        
        self.secondsEstimatedTotal = 0 # stores variable that is added to secondsTillComplete (sTC) and is later subtracted to get updated variable (sTC)
        self.percentComplete = 0 # stores the percent complete to display in the GUI
        self.secondsTillComplete = 0 # stores approximate number of seconds it will take to complete queue
        self.queueCompletionDate = 0 # holds date for when the queue will be finished
        self.running = False
        self.queue_changed = True
        
        # *note: gradient^-1 indicates the gradient time from the previous sample. SPE^-2 would be the SPE time from two samples ago

        format = "%(asctime)s: %(message)s" #format logging
        logging.basicConfig(format=format, level=logging.ERROR,
                            datefmt="%H:%M:%S")
        
        
    def verify_wells(self, compiled_queue):  # checks all the wells in CSV to make sure they all exist
        print("Verifying Wells...")

        for index, row in compiled_queue.iterrows():

            row["Well"] = row["Well"].replace(" ", "")
            for well in row["Well"].split(","):
                
                well_exists = self.myCoordinator.myModules.myStages[row["Stage"]].myLabware.check_well_exists(int(row["Wellplate"]), well)

                if not well_exists:
                    print(f"ERROR: {well} does not exist. Verify that the queue file contains only existing wells", "\n")
                    return False

        print("All Wells Verified!", "\n")
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

    def convert_sec_to_day(self, n): # takes in time in seconds and converts to day, hour, minute, second
        #n = number of seconds to complete a queue
        
        days = int(n / (24 * 3600))  # calculate days
  
        n = n % (24 * 3600)
        hours = int(n / 3600) # calculate hours
  
        n %= 3600
        minutes = int(n / 60) # calculate minutes
  
        n %= 60
        seconds = int(n)#calculate seconds
        
        logging.info("\"%s\" estimated completion in: %s d %s h %s m %s s", self.queueName, days, hours, minutes, seconds) #log this info

    def estimate_end_time(self): #estimates how long the method will take to complete
        # add the first gradient time (thread) and all gradients from queue methods
        # add first gradient to this. (About 35 minutes for dry or QCtime for wet)

        firstFile = True #variable that allows estimated time to be more accurate: only adds self.secondsEstimatedTotal one extra time
        extraSeconds = 0
        
        for method in self.methodList: # for all the methods in queue
                  
            path_to_method = method # moves to method folder
            with open(path_to_method, 'r') as myfile: # open file
                data = myfile.read()
            obj = json.loads(data) # parse file and sets variables
            extraSeconds = (max((int(obj['SPEtime'])),(int(obj['gradientTime'])))) - (int(obj['LCtime'])) - (int(obj['MStime']))
            self.secondsEstimatedTotal = int(obj['LCtime'])
            self.secondsEstimatedTotal += int(obj['MStime'])
            self.secondsEstimatedTotal += extraSeconds
            # add up all gradient times from each method to see how long it will take
            
            if firstFile:
                turnOnLC = (max((int(obj['SPEtime'])),(int(obj['gradientTime']))))*2 - (int(obj['LCtime']))
                self.secondsEstimatedTotal += turnOnLC
                self.secondsEstimatedTotal -= extraSeconds
                firstFile = False #updates variable

            self.secondsTillComplete += self.secondsEstimatedTotal # note that this is in seconds

        methodLength = 4
        for methodLength in self.wellList: #adds one to self.methodIndex to accuratly find the time of each middleLoop
            self.methodIndex += 1
            if methodLength > 4:
                methodLength = self.methodIndex
        self.lastLoop = extraSeconds*2 + int(obj['LCtime'])*2 + int(obj['MStime'])*3
        self.firstTwoLoops = turnOnLC + int(obj['LCtime'])
        self.middleLoops = (self.secondsTillComplete - self.lastLoop - self.firstTwoLoops) / (methodLength - 3)

        self.queueCompletionDate = time.asctime( time.localtime(time.time() + self.secondsTillComplete)) #find estimated time of completion
        logging.info("\"%s\" estimated completion on: %s", self.queueName, self.queueCompletionDate)

        self.convert_sec_to_day(self.secondsTillComplete) # prints message for when it will be done
        #if input("          Is this okay? (y/n): ") == "n":
         #   sys.exit()

        self.methodIndex = 0 # resets the self.methodIndex

    def hard_stop(self): # stops queue entirely, stops loading and the rest of the LC and MS calls
        self.myStopIndicator.turn_on_hardStop()

    # NOT IMPLEMENTED AT THE MOMENT. need to add queue queueing first
    def pause_queue(self): # this pauses the queue so you can add methods to the queue (stops you from runnning the finishup routine and starting over. saves maybe 3 hours)
        self.myStopIndicator.pause()
    
    def resume_queue(self):
        self.myStopIndicator.resume()

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

    def load_sample(self, path_to_method):  # reads and calls commands from method to load next sample
        """
            Args:
                well ([str]): [holds the location of the sample we want to load. e.g., 'P1c4']
                methodName ([str]): [the name of the method used to prepare the sample at the well location. e.g., "qc.json"]
        """
        logging.info(f"Loading sample {self.methodIndex} with {path_to_method}: Started") # print message stating that a method has begun
        
        # read file
        with open(path_to_method, 'r') as myfile:
            data = myfile.read()
        obj = json.loads(data) # parse file

        #loop for all commands in json method
        for command in obj['commands']:
            if self.myStopIndicator.hardStop == True: # check to see if we should stop loading
                break # if hardStop then we break to loop and stop loading

            
            params = command['parameters'] # save command parameters in a list

            
            #calls correct function in coordinator & unpacks the parameters list with (*params): logs each parameter
            getattr(self.myCoordinator.actionOptions, command['type'])(*params)

        logging.info("Loading Sample '%s': Complete!") # print that the sample is done being loaded      

    def run(self, scheduled_methods): #main function: handles looping and threads
        """
            
        """
        print("") #Add line to make output easier to read
        
        self.methodIndex = 0 # used to track the index of the wellList to get corresponding method. reset for every queue
        self.myStopIndicator.reset() # reset the stop indicators back to false for every queue
        
        #loop for all wells. this may also include wellplate_wells for QC loading
        total_number = scheduled_methods.shape[0]
        for index, row in scheduled_methods.iterrows():
            self.queue_changed = True
            self.running = True
        
            while self.myStopIndicator.paused:
                pass
            print("\n")


            self.mySample = row # set the location of 'mySample' to well for each loops



            #make gradient threads
            
            # load next sample while thread is running--------------------------------------------------
            self.load_sample(row["Method"]) # load next sample with appropirate method

            # make sure loading next sample is faster than gradient thread--------------------------------------------------

            print(f"Sample {str(index+1)} of {str(total_number)} complete!")#: {str(self.percentComplete)}%") # print percent complete
            self.methodIndex += 1 # next well may have a different method than the one we just did
            
            print("----------------------------------------------------------") #white space for output readibility
            
            if self.myStopIndicator.stopLoad or self.myStopIndicator.hardStop:
                print("No more samples will be loaded. Either stopLoad or hardStop was called")
                break # stop loading more samples if either is set to true
            
        self.methodIndex = 0 #reset the method index for the next queue
        

        # self.get_method_times(self.methodList[self.methodIndex])
        #finish run: stops whether hard stop or load is done
        if self.myStopIndicator.hardStop:
            print("hardStop Called. All function calls have stopped. Finish up routine Skipped")
        else:
            print("stopLoad Called. Finish up routine will be executed and then program will end")

        print("")
        print("     DONE!!!")

            
        
            

'''
# comment in or out the following 3 lines to test just this file. 
# You will have to Comment in the psudo coordinator class at the top of this file
Coordinator = Coordinator()
myReader = MethodReader(Coordinator, "queue")
myReader.run("queue")
'''
