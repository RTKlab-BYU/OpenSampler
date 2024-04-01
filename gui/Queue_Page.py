import tkinter as tk
from tkinter import filedialog as fd
import time
import threading
import pathlib
import pandas as pd

class Queue_Gui(tk.Toplevel,):

    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Run Method")
        self.geometry("1000x1800")
        self.state("zoomed")
        self.coordinator = coordinator
        self.page_type = tk.StringVar()
        self.scheduled_queue = []
        self.sample_prep_to_schedule = []


        self.page_frame = tk.Frame(self)
        self.page_frame.pack(pady=20)

        # select method type. this determines how page is displayed
        self.sample_prep_page = tk.Radiobutton(self.page_frame, text="Sample Preparation", variable=self.page_type, value="Sample Prep", command=self.load_page)
        self.mass_spec_page = tk.Radiobutton(self.page_frame, text="Mass Spectrometry", variable=self.page_type, value="Mass Spec", command=self.load_page)
        self.fractionation_page = tk.Radiobutton(self.page_frame, text="Fractionation", variable=self.page_type, value="Fractionation", command=self.load_page)
        self.active_queue_page = tk.Radiobutton(self.page_frame, text="Active Queue", variable=self.page_type, value="Active Queue", command=self.load_page)
        self.sample_prep_page.grid(row=0,column=0)
        self.mass_spec_page.grid(row=0,column=1)
        self.fractionation_page.grid(row=0,column=2)
        self.active_queue_page.grid(row=0,column=3)

        # Frame that changes based on page type
        self.master_frame = tk.Frame(self) #, highlightthickness=2, highlightbackground="black")
        self.master_frame.pack(fill="both", )
        self.upper_frame = tk.Frame(self.master_frame)
        self.queue_frame = tk.Frame(self.master_frame) #, highlightthickness=2, highlightbackground="green")
        self.sample_prep_frame = Sample_Prep_Frame(self.master_frame)

        # Canvas for scrolling through long que 
        self.canvas = tk.Canvas(self.queue_frame, width=4000, height = 1800, scrollregion=(0,0,4000,1800), highlightthickness=2,highlightbackground="blue")
        canvas_width = self.canvas.winfo_width()
        self.queue_grid = tk.Frame(self.canvas, width=canvas_width, highlightthickness=2, highlightbackground="red")

        self.y_scrollbar = tk.Scrollbar(self.queue_frame, orient="vertical", command=self.canvas.yview)       
        self.x_scrollbar = tk.Scrollbar(self.queue_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand = self.y_scrollbar.set, xscrollcommand = self.x_scrollbar.set)

        self.y_scrollbar.pack(side="right", fill="y")
        self.x_scrollbar.pack(side = tk.BOTTOM, fill = tk.X)
        self.canvas.pack(fill="both", expand=True)
        
        self.queue_grid_window = self.canvas.create_window((4,4), window=self.queue_grid, anchor="nw", tags="self.queue_grid")
        self.queue_grid.bind("<Configure>", lambda x: self.config_my_queue(x))

        self.update()
        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-3)
        
        # Handler must come after que grid 
        self.handler = Queue_Handler(self.queue_grid, self.coordinator)
        
        # file bar for ms and frac queues.
        self.file_bar = tk.Frame(self.upper_frame)
        self.file_bar.pack()
        self.clear_queue = tk.Button(self.file_bar, text='Clear Queue', command= lambda:self.clear_queue())
        self.select_file = tk.Button(self.file_bar,text='Select Queue File', command= lambda:self.select_file())
        self.save_queue = tk.Button(self.file_bar,text="Save Queue", command= lambda:self.save_queue())

        # run bar for ms and frac queues.
        self.run_bar = tk.Frame(self.upper_frame)
        self.run_bar.pack()
        self.RunButton = tk.Button(self.run_bar, text="Run Queue",command=lambda: self.RunQueue_Thread(),justify=tk.LEFT)
        self.StopButton = tk.Button(self.run_bar, text="STOP NOW",command=lambda: self.StopQueue(),justify=tk.LEFT)
        self.PauseButton = tk.Button(self.run_bar, text="Pause Queue",command=lambda: self.PauseQueue(),justify=tk.LEFT)
        self.ResumeButton = tk.Button(self.run_bar, text="Resume Queue",command=lambda: self.ResumeQueue(),justify=tk.LEFT)
        self.RunButton.grid(row=0, column=0, columnspan=1)
        self.StopButton.grid(row=0,column=1, columnspan=1)
        self.PauseButton.grid(row=0,column=2, columnspan=1)
        self.ResumeButton.grid(row=0,column=3, columnspan=1)

        # initial button states
        self.RunButton["state"] =  "normal"
        self.StopButton["state"] =  "disabled"
        self.PauseButton["state"] =  "disabled"
        self.ResumeButton["state"] =  "disabled"

        # active que setup
        self.active_queue = Active_Queue(self.master_frame)

        # 
        self.page_type.set("Sample Prep")
        self.load_page()

        #
        self.bind("<Configure>", lambda x: self.config_my_queue(x))


    def config_my_queue(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)



    def load_page(self):
        queue = self.page_type.get()
        self.handler.active_queue = queue
        
        if queue == "Sample Prep":
            self.upper_frame.pack_forget()
            self.queue_frame.pack_forget()
            self.active_queue.pack_forget()
            self.sample_prep_frame.pack()

        elif queue == "Mass Spec":
            self.sample_prep_frame.pack_forget()
            self.active_queue.pack_forget()
            self.upper_frame.pack()
            self.queue_frame.pack(fill="both", expand=True)
            self.update()
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)         
            self.handler.clear_grid()
            
        elif queue == "Fractionation":
            self.sample_prep_frame.pack_forget()
            self.active_queue.pack_forget()
            self.upper_frame.pack()
            self.queue_frame.pack(fill="both", expand=True)
            self.update()
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)
            self.handler.clear_grid()

        elif queue == "Active Queue":
            self.sample_prep_frame.pack_forget()
            self.upper_frame.pack_forget()
            self.queue_frame.pack_forget()
            self.active_queue.pack()


    # Run Method Functions
        
    def compile_queue(self):
        '''
        This function is used to pull the parameters out of the entry values and package them as pandas dataframe object.
        '''
        queue = self.page_type.get()
        self.handler.active_queue = queue
        
        if queue == "Sample Prep":
            # package sample prep params

            # i don't have anything set up for this yet
            pass

        elif queue == "Mass Spec":
            # package MS queue
            self.ms_queue_to_schedule = pd.DataFrame({"Stage": [], "Wellplate": [], "Well": [], "Method": []})
            for entry in self.handler.ms_queue[1:]:
                ms_inputs: MS_Queue_Row_Inputs = entry
            
                temp_list = [ms_inputs.stage.get(), ms_inputs.plate.get(), ms_inputs.well.get(), ms_inputs.method.get()]
                self.ms_queue_to_schedule.loc[len(self.ms_queue_to_schedule.index)] = temp_list
            return self.ms_queue_to_schedule
        
        elif queue == "Fractionation":
            # package Frac queue
            self.frac_queue_to_schedule = pd.DataFrame({"Stage": [], "Wellplate": [], "Well": [], "Method": [], "Target Well": []})
            for row, entry in enumerate(self.handler.frac_queue, 1):
                frac_inputs: Frac_Queue_Row_Inputs = self.handler.frac_queue[row]
                temp_list = [frac_inputs.stage.get(), frac_inputs.plate.get(), frac_inputs.pool_wells.get(), frac_inputs.method.get(), frac_inputs.target_well.get()]
                self.frac_queue_to_schedule.loc[len(self.frac_queue_to_schedule.index)] = temp_list
            return self.frac_queue_to_schedule
            
        
    def RunQueue_Thread(self):
        '''
        Compile the current queue into a pandas dataframe.
        Verify the methods.
        Add the dataframe to the schedule queue,
        If not currently running, begin running.
        '''
        # set button states        
        self.StopButton["state"] =  "normal"
        self.PauseButton["state"] =  "normal"

        # start thread to run queue
        compiled_queue = self.compile_queue()
        
        if self.coordinator.myReader.verify(compiled_queue):
            self.scheduled_queue.append(compiled_queue)
            if self.coordinator.myReader.running:
                pass
            else:
                queueThread = threading.Thread(target = self.Run_Scheduled_Methods, args=[]) #finishes the run
                queueThread.start()


    def Run_Scheduled_Methods(self):        
        
        # start thread to watch status
        watchThread = threading.Thread(target = self.watch_status, args=[]) #finishes the run
        watchThread.start()

        while len(self.scheduled_queue) > 0:
            current = self.scheduled_queue.pop(0)
            self.coordinator.myReader.run(current)

        
        self.coordinator.myReader.running = False           


    def watch_status(self):

        time.sleep(5)
        
        while self.coordinator.myReader.running:
            time.sleep(1)
            if self.coordinator.myReader.queue_changed:
                self.coordinator.myReader.queue_changed = False

        self.RunButton["state"] = "normal"
        self.StopButton["state"] =  "disabled"
        self.PauseButton["state"] =  "disabled"
        self.ResumeButton["state"] = "disabled"
    
    # move to active queue
    def StopQueue(self):
        self.RunButton["state"] =  "normal"
        self.StopButton["state"] =  "disabled"
        self.PauseButton["state"] =  "disabled"
        self.ResumeButton["state"] = "disabled"
      
        self.coordinator.myReader.hard_stop()

    # move to active queue
    def PauseQueue(self):
        self.ResumeButton["state"] =  "normal"
        self.PauseButton["state"] =  "disabled"
        self.grab_release()
        
        self.coordinator.myReader.pause_queue()           

    # move to active queue
    def ResumeQueue(self):
        self.PauseButton["state"] =  "normal"
        self.ResumeButton["state"] =  "disabled"
      

        self.coordinator.myReader.resume_queue()

    # rework 
    def clear_queue(self):
        self.wellList = []
        self.methodList = []

    # rework
    def select_file(self):
        filetypes = (
            ('csv files', '*.csv'),
            ('All files', '*')
        )

        new_file = fd.askopenfilename(
            title='Add to Queue',
            initialdir='queues',
            filetypes=filetypes)
        
        self.queue_to_run = new_file
        self.RunButton["state"] =  "normal"
        
        pathToQueue = self.queue_to_run
        queueFile = pathlib.Path(pathToQueue)
        if queueFile.exists ():
            queueFail = True
        else:
            queueFail = False
 
        while queueFail == False:
            self.queue_to_run = input("Invalid queue. Try again: ")
            pathToQueue = self.queue_to_run
            queueFile = pathlib.Path(pathToQueue)
            if queueFile.exists ():
                queueFail = True
            else:
                queueFail = False

        # -----Get list from CSV queue.csv with pd. This is used for the RPi because the RPi doesn't have excel-----
        
        col_list = ['Locations', 'Methods']
        df = pd.read_csv(pathToQueue, usecols=col_list)
        [self.wellList.append(well) for well in df["Locations"].tolist()]
        [self.methodList.append(method) for method in df["Methods"].tolist()]

    # rework  
    def save_queue(self):
        
        filetypes = (
            ('CSV files', '*.csv'),
            ( 'All files', '*')
        )

        new_file = fd.asksaveasfile(
            title='Save a file',
            initialdir='queues',
            filetypes=filetypes)
        
        if new_file.name.endswith(".csv"):
            new_file = new_file.name.replace(".csv","") + ".csv"
        else:
            new_file = new_file.name + ".csv"
        
        df = pd.DataFrame(data={'Locations':self.wellList,'Methods':self.methodList})
        df.to_csv(new_file,index=False)      


class Queue_Handler:
    def __init__(self, queue_grid, coordinator):
        self.queue_handler_master = queue_grid
        self.coordinator = coordinator
        self.active_queue = None
        
        self.row_buttons_frame = tk.Frame(self.queue_handler_master)
        self.row_buttons_frame.pack(side="left")

        self.ms_queue_frame = tk.Frame(self.queue_handler_master)
        self.frac_queue_frame = tk.Frame(self.queue_handler_master)
        
        self.buttons_header = tk.Frame(self.row_buttons_frame)
        self.buttons_header.pack()
        self.ms_queue_header = tk.Frame(self.ms_queue_frame)
        self.frac_queue_header = tk.Frame(self.frac_queue_frame)

        self.ms_queue =  [self.ms_queue_header]
        self.frac_queue = [self.frac_queue_header]
        self.queue_row_buttons = [self.buttons_header]

        self.add_row = tk.Button(self.buttons_header, text="Add Row", command= lambda: self.insert_row())
        self.add_row.pack(side=tk.LEFT)

        # MS queue headers
        tk.Label(self.ms_queue_header,text="Motor Series", bd=2, relief="solid").pack(side='left')
        tk.Label(self.ms_queue_header,text="Wellplate Index", bd=2, relief="solid").pack(side='left')
        tk.Label(self.ms_queue_header,text="Sample Well", bd=2, relief="solid").pack(side='left')
        tk.Label(self.ms_queue_header,text="Method Path", bd=2, relief="solid").pack(expand=True, fill="x", side='left')

        # fractionation queue headers
        tk.Label(self.frac_queue_header,text="Motor Series").pack(side='left')
        tk.Label(self.frac_queue_header,text="Wellplate Index").pack(side='left')
        tk.Label(self.frac_queue_header,text="Sample Well").pack(side='left')
        tk.Label(self.frac_queue_header,text="Method Path").pack(expand=True, fill="x", side='left')

        # Add an initial row to queues
        new_buttons = Queue_Row_Buttons(self.row_buttons_frame, self.coordinator, 1, self)
        self.queue_row_buttons.append(new_buttons)
        new_buttons.pack()
        self.ms_queue.insert(1, MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator))
        self.frac_queue.insert(1, Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator))




    def clear_grid(self):
        '''
        Only called when switching queue types.
        It clears everything from the queue grid so the proper grid can be displayed
        '''

        if self.active_queue == 'Mass Spec':
            self.frac_queue_frame.pack_forget()
            self.ms_queue_frame.pack(expand=True, fill="x", side="left")
            

        elif self.active_queue == 'Fractionation':
            self.ms_queue_frame.pack_forget()
            self.frac_queue_frame.pack(expand=True, fill="x", side="left")

        self.update_grid()
      
    def reset_grid(self):
        '''
        This function returns the column headers to the grid, then checks on the nimber of button rows needed.
        If the number of needed button rows has changed (eg we switch queue type), rows are added or removed.
        '''
        
        if self.active_queue == 'Mass Spec':
             
            for frame in self.ms_queue:
                frame: tk.Frame = frame
                frame.pack_forget()
            
            for frame in self.ms_queue:
                frame: tk.Frame = frame
                frame.pack(fill="x", expand=True)
            
                
        elif self.active_queue == 'Fractionation':
            for frame in self.frac_queue:
                frame: tk.Frame = frame
                frame.pack_forget()

            for frame in self.frac_queue:
                frame: tk.Frame = frame
                frame.pack(fill="x", expand=True) 

    def maintain_button_rows(self):
        '''
        Disables "Move Up" button on row 1.
        Disables "Move Down" button on last row.
        Ensures all other buttons are enabled. 
        '''
        if self.active_queue == 'Mass Spec':
            queue = len(self.ms_queue)
        elif self.active_queue == 'Fractionation':
            queue = len(self.frac_queue)

        while len(self.queue_row_buttons) > queue:
            remove_buttons: Queue_Row_Buttons = self.queue_row_buttons.pop()
            remove_buttons.destroy()

        while len(self.queue_row_buttons) < queue:
            new_buttons = Queue_Row_Buttons(self.row_buttons_frame, self.coordinator, len(self.queue_row_buttons), self)
            self.queue_row_buttons.append(new_buttons)
            new_buttons.pack()

        for row in range(1, len(self.queue_row_buttons)):
            if row == 1:
                buttons: Queue_Row_Buttons = self.queue_row_buttons[row]
                buttons.move_up.config(state="disabled")
                buttons.move_down.config(state="normal")
            elif row == len(self.queue_row_buttons)-1:
                buttons: Queue_Row_Buttons = self.queue_row_buttons[row]
                buttons.move_up.config(state="normal")
                buttons.move_down.config(state="disabled")
            else:
                buttons: Queue_Row_Buttons = self.queue_row_buttons[row]
                buttons.move_up.config(state="normal")
                buttons.move_down.config(state="normal")

    def update_grid(self):
        self.reset_grid()
        self.maintain_button_rows()
        
    def set_active_queue(self, active_queue):
        if self.active_queue != active_queue:
            self.active_queue = active_queue
            self.update_grid()


    # Queue Handler Buttons

    def  insert_row(self, buttons_index=None):
        '''
        Creates a new row of buttons, then inserts a new set of inputs at the indicated index.
        '''
        if buttons_index == None:
            buttons_index = len(self.queue_row_buttons)
        # print(self.active_queue)
        new_buttons = Queue_Row_Buttons(self.row_buttons_frame, self.coordinator, len(self.queue_row_buttons), self)
        self.queue_row_buttons.append(new_buttons)
        new_buttons.pack()
        if self.active_queue == 'Mass Spec':
            self.ms_queue.insert(buttons_index, MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator))
        elif self.active_queue == 'Fractionation':
            self.frac_queue.insert(buttons_index, Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator))

        
        self.update_grid()

    def move_up(self, row_index):
        '''
        Moves the indicated row's current inputs up one row by poping it out and reinserting it one index less.
        '''
        print(self.active_queue)
        if self.active_queue == 'Mass Spec':
            move_item = self.ms_queue.pop(row_index)
            self.ms_queue.insert(row_index-1, move_item)
        elif self.active_queue == 'Fractionation':
            move_item = self.frac_queue.pop(row_index)
            self.frac_queue.insert(row_index-1, move_item)

        self.update_grid()

    def move_down(self, row_index):
        '''
        Moves the indicated row's current inputs down one row by poping it out and reinserting it one index greater.
        '''
        print(self.active_queue)
        if self.active_queue == 'Mass Spec':
            move_item = self.ms_queue.pop(row_index)
            self.ms_queue.insert(row_index+1, move_item)
        elif self.active_queue == 'Fractionation':
            move_item = self.frac_queue.pop(row_index)
            self.frac_queue.insert(row_index+1, move_item)

        self.update_grid()
    
    def delete_row(self, row_index):
        '''
        Removes the indicated inputs and destroys them, then removes the last row of buttons.
        Waits until the grid has been updated to destroy the button (in case this was the last row).
        '''
        print(self.active_queue)
        
        if self.active_queue == 'Mass Spec':
            remove_item: MS_Queue_Row_Inputs = self.ms_queue.pop(row_index)
            remove_item.destroy()
        elif self.active_queue == 'Fractionation':
            remove_item: Frac_Queue_Row_Inputs = self.frac_queue.pop(row_index)
            remove_item.destroy()

        remove_item: Queue_Row_Buttons = self.queue_row_buttons.pop()      
        self.update_grid()
        remove_item.destroy() # go last to ensure all other tasks completed


class Sample_Prep_Frame(tk.Frame,):
    '''
    This class allows the user to select and schedule a sample preparation method
    '''
    def __init__(self, master_frame):
        super().__init__(master_frame)

        self.stage = tk.StringVar()
        self.stage_box = tk.Entry(self, textvariable=self.stage)
        self.stage_box.pack()


class Active_Queue(tk.Frame,):
    '''
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame):
        super().__init__(master_frame)
        self.run_type = tk.StringVar(value="Nothing in the Active Queue")

        self.type_frame = tk.Frame(self)
        self.current_run_frame = tk.Frame(self)
        self.scheduled_runs_frame = tk.Frame(self)

        # inside type frame
        self.type_label = tk.Label(self, textvariable=self.run_type)
        self.type_label.pack()

        # inside current run frame
        self.stop_button = tk.Button(self.current_run_frame, command=self.stop_immediately)
        self.current_run_label = tk.Label(self.current_run_frame, text="Currently Running")
        self.current_run_inner = tk.Frame(self.current_run_frame)

        

        # add 

        self.current_headers = None
        self.current_specs = None

        
        
    def update_active_queue_type(self, queue_type):

        if queue_type == "Sample Prep":
            self.run_type.set("Sample Preparation")
            # forget other displays 
            # pack sample prep display
            
        elif queue_type == "Mass Spec":
            self.run_type.set("LC-MS")
            # forget other displays 
            # pack mass spec display
 
        elif queue_type == "Fractionation":
            self.run_type.set("Fractionation")
            # forget other displays 
            # pack fractionation  display

        else:
            self.run_type.set("Nothing in the Active Queue")
            # forget all displays
            

    def stop_immediately(self):
        '''
        Pauses queue and interupts current run.
        '''
        pass



class MS_Queue_Row_Inputs(tk.Frame,):
    '''
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame, coordinator):
        super().__init__(master_frame)
        self.master_frame: tk.Frame = master_frame
        self.coordinator = coordinator
        
        self.stage = tk.StringVar()
        self.plate = tk.StringVar()
        self.well = tk.StringVar()
        self.method = tk.StringVar()

        # self.stage_box_frame = tk.Frame(self)
        # self.plate_box_frame = tk.Frame(self)
        # self.well_box_frame = tk.Frame(self)
        # self.method_box_frame = tk.Frame(self)

        # self.stage_box = tk.Entry(self.stage_box_frame, textvariable=self.stage)
        # self.plate_box = tk.Entry(self.plate_box_frame, textvariable=self.plate)
        # self.well_box = tk.Entry(self.well_box_frame, textvariable=self.well)
        # self.method_box = tk.Entry(self.method_box_frame, textvariable=self.method)

        self.stage_box = tk.Entry(self, textvariable=self.stage)
        self.plate_box = tk.Entry(self, textvariable=self.plate)
        self.well_box = tk.Entry(self, textvariable=self.well)
        self.method_box = tk.Entry(self, textvariable=self.method)

        self.stage_box.pack(side="left")
        self.plate_box.pack(side="left")
        self.well_box.pack(side="left")
        self.method_box.pack(expand=True, fill="x", side="left")
        
        self.method_box.bind('<Double-Button-1>', lambda x: self.select_method(x))


    def select_method(self, event):
        filetypes = (
            ('JSON files', '*.json'),
            ('All files', '*')
        )

        file_path = fd.askopenfilename(title='Choose a Method', initialdir='methods', filetypes=filetypes)
        self.method.set(file_path)
        # self.handler.ms_default_file_path = file_path #README: Make it so method is default populated


class Frac_Queue_Row_Inputs(tk.Frame,):
    '''
    Currently identical to MS_Queue_Row_Inputs
    
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame, coordinator):
        super().__init__(master_frame)
        self.coordinator = coordinator
        
        self.stage = tk.StringVar()
        self.plate = tk.StringVar()
        self.pool_wells = tk.StringVar()
        self.target_wells = tk.StringVar()
        self.method = tk.StringVar()
        
        self.stage_box = tk.Entry(self, textvariable=self.stage)
        self.plate_box = tk.Entry(self, textvariable=self.plate)
        self.pool_wells_box = tk.Entry(self, textvariable=self.pool_wells)
        self.target_wells_box = tk.Entry(self, textvariable=self.target_wells)
        self.method_box = tk.Entry(self, textvariable=self.method)

        self.stage_box.pack(side="left")
        self.plate_box.pack(side="left")
        self.pool_wells_box.pack(side="left")
        self.target_wells_box.pack(side="left")
        self.method_box.pack(expand=True, fill="x", side="left")
        

        self.method_box.bind('<Double-Button-1>', lambda x: self.select_method(x))


    def select_method(self, event):  # still needs work
        filetypes = (
            ('JSON files', '*.json'),
            ('All files', '*')
        )

        file_path = fd.askopenfilename(title='Choose a Method', initialdir='methods', filetypes=filetypes)
        self.method.set(file_path)
        

class Queue_Row_Buttons(tk.Frame,):
    '''
    This class is used to replicate the movement options for each queue row
    Each index has a row index to inform the affect those buttons have on the corresponding rows of inputs.
    Button rows do not need to move around as the inputs do, but the number of button rows should always match 
        the number of input rows.
    '''
    def __init__(self, master_frame, coordinator, row_index, handler: Queue_Handler):
        super().__init__(master_frame)
        self.coordinator = coordinator
        self.row = row_index
        self.handler = handler

        self.insert = tk.Button(self, text="Insert", command=lambda: self.handler.insert_row(self.row))
        self.delete = tk.Button(self, text="Delete", command=lambda: self.handler.delete_row(self.row))
        self.move_up = tk.Button(self, text="Up", command=lambda: self.handler.move_up(self.row))
        self.move_down = tk.Button(self, text="Down", command=lambda: self.handler.move_down(self.row))

        self.insert.grid(row=0, column=0)
        self.delete.grid(row=0, column=1)
        self.move_up.grid(row=0, column=2)
        self.move_down.grid(row=0, column=3)