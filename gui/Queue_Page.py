import tkinter as tk
from tkinter import filedialog as fd
import time
import threading
import pathlib
import pandas as pd

from Classes.coordinator import Coordinator

STANDARD_ROW_HEIGHT = 100
SP_HEADERS = ["Method"]
MS_HEADERS = ["Stage", "Wellplate", "Well", "Method"]
FRAC_HEADERS = ["Stage", "Wellplate", "Sample Wells", "Elution Wells", "Method"]

class Queue_Gui(tk.Toplevel,):

    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Run Method")
        self.geometry("1000x1800")
        self.state("zoomed")
        self.coordinator: Coordinator = coordinator
        self.page_type = tk.StringVar()
        self.sample_prep_to_schedule = []

        # This frame determines what is displayed in the rest of the page.
        self.page_selection_frame = tk.Frame(self)
        self.page_selection_frame.pack(pady=20)

        self.sample_prep_page = tk.Radiobutton(self.page_selection_frame, text="Sample Preparation", variable=self.page_type, value="Sample Prep", command=self.load_page)
        self.mass_spec_page = tk.Radiobutton(self.page_selection_frame, text="Mass Spectrometry", variable=self.page_type, value="Mass Spec", command=self.load_page)
        self.fractionation_page = tk.Radiobutton(self.page_selection_frame, text="Fractionation", variable=self.page_type, value="Fractionation", command=self.load_page)
        self.scheduled_queue_page = tk.Radiobutton(self.page_selection_frame, text="Active Queue", variable=self.page_type, value="Active Queue", command=self.load_page)

        self.sample_prep_page.grid(row=0,column=0)
        self.mass_spec_page.grid(row=0,column=1)
        self.fractionation_page.grid(row=0,column=2)
        self.scheduled_queue_page.grid(row=0,column=3)

        # Frame that changes based on page type
        self.page_display_frame = tk.Frame(self) 
        self.page_display_frame.pack(fill="both", expand=True)

        self.upper_frame = tk.Frame(self.page_display_frame) #, highlightbackground="pink", highlightthickness=2)
        self.queue_frame = tk.Frame(self.page_display_frame) #, highlightbackground="yellow", highlightthickness=2) 
        self.sample_prep_frame = tk.Frame(self.page_display_frame)
        self.scheduled_queue_frame = Scheduled_Queue(self.page_display_frame, self.coordinator)
        # self.scheduled_queue_frame.config(highlightbackground="green", highlightthickness=2)

        # Canvas for scrolling through long que 
        self.canvas = tk.Canvas(self.queue_frame, width=4000, height = 1800, scrollregion=(0,0,4000,1800),)
        canvas_width = self.canvas.winfo_width()
        self.queue_grid = tk.Frame(self.canvas, width=canvas_width)

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

        self.clear_button = tk.Button(self.file_bar, text='Clear Queue', command= lambda:self.clear_queue())
        self.load_button = tk.Button(self.file_bar,text='Load Queue', command= lambda:self.select_file())
        self.save_button = tk.Button(self.file_bar,text="Save Queue", command= lambda:self.save_queue())

        self.clear_button.grid(row=0, column=1)
        self.load_button.grid(row=0, column=2)
        self.save_button.grid(row=0, column=3)


        # run bar for ms and frac queues.
        self.run_bar = tk.Frame(self.upper_frame)
        self.run_bar.pack()

        self.RunButton = tk.Button(self.run_bar, text="Run Queue",command=lambda: self.schedule_queue(),justify=tk.LEFT)
        self.RunButton.grid(row=0, column=0)

        # In sample prep frame
        self.sp_run_button = tk.Button(self.sample_prep_frame, text="Run Method",command=lambda: self.schedule_queue(),justify=tk.LEFT)
        self.sp_inputs = Sample_Prep_Inputs(self.sample_prep_frame)

        self.sp_run_button.pack()
        self.sp_inputs.pack()

        # initial button states
        self.RunButton["state"] =  "normal"

        

        # Initial Page
        self.page_type.set("Sample Prep")
        self.load_page()

        # Reconfigure que when reconfiguring window
        self.bind("<Configure>", lambda x: self.config_my_queue(x))

    def config_my_queue(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)

    def load_page(self):
        page_type = self.page_type.get()
        self.handler.set_active_page(page_type)
        
        if page_type == "Sample Prep":
            self.upper_frame.pack_forget()
            self.queue_frame.pack_forget()
            self.scheduled_queue_frame.pack_forget()
            self.sample_prep_frame.pack(pady=50)

        elif page_type == "Mass Spec":
            self.sample_prep_frame.pack_forget()
            self.scheduled_queue_frame.pack_forget()
            self.upper_frame.pack(fill="x")
            self.queue_frame.pack(fill="both", expand=True)
            self.update()
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)         
            self.handler.clear_grid()
            
        elif page_type == "Fractionation":
            self.sample_prep_frame.pack_forget()
            self.scheduled_queue_frame.pack_forget()
            self.upper_frame.pack(fill="x")
            self.queue_frame.pack(fill="both", expand=True)
            self.update()
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)
            self.handler.clear_grid()

        elif page_type == "Active Queue":
            self.sample_prep_frame.pack_forget()
            self.upper_frame.pack_forget()
            self.queue_frame.pack_forget()
            self.scheduled_queue_frame.pack(expand=True, fill="both")
        
    def compile_queue(self):
        '''
        This function is used to pull the parameters out of the entry values and package them as pandas dataframe object.
        '''

        page_type = self.page_type.get()
        self.handler.set_active_page(page_type)
        
        if page_type == "Sample Prep":
            # package sample prep params

            # i don't have anything set up for this yet
            pass

        elif page_type == "Mass Spec":
            # package MS queue
            self.ms_queue_to_schedule = pd.DataFrame({MS_HEADERS[0]: [], MS_HEADERS[1]: [], MS_HEADERS[2]: [], MS_HEADERS[3]: []})
            for entry in self.handler.ms_queue[1:]:
                ms_inputs: MS_Queue_Row_Inputs = entry
            
                temp_list = [ms_inputs.stage.get(), ms_inputs.plate.get(), ms_inputs.well.get(), ms_inputs.method.get()]
                self.ms_queue_to_schedule.loc[len(self.ms_queue_to_schedule.index)] = temp_list
            return self.ms_queue_to_schedule
        
        elif page_type == "Fractionation":
            # package Frac queue
            self.frac_queue_to_schedule = pd.DataFrame({FRAC_HEADERS[0]: [], FRAC_HEADERS[1]: [], FRAC_HEADERS[2]: [], FRAC_HEADERS[3]: [], FRAC_HEADERS[4]: []})
            for row, entry in enumerate(self.handler.frac_queue, 1):
                frac_inputs: Frac_Queue_Row_Inputs = self.handler.frac_queue[row]
                temp_list = [frac_inputs.stage.get(), frac_inputs.plate.get(), frac_inputs.pool_wells.get(), frac_inputs.method.get(), frac_inputs.target_well.get()]
                self.frac_queue_to_schedule.loc[len(self.frac_queue_to_schedule.index)] = temp_list
            return self.frac_queue_to_schedule
                    
    def schedule_queue(self):
        '''
        Compile the current queue into a pandas dataframe.
        Verify the methods.
        Add the dataframe to the schedule queue,
        If not currently running, begin running.
        '''

        # start thread to run queue
        new_queue_type = self.page_type.get()

        # check for conflict between current and new queue
        if not self.coordinator.myReader.running:
            compiled_queue = self.compile_queue()
            self.scheduled_queue_frame.queue_type = new_queue_type
            self.scheduled_queue_frame.update_scheduled_queue_display()
        elif (new_queue_type == self.scheduled_queue_frame.queue_type):
            compiled_queue = self.compile_queue()
        else:
            print("\n\nYou Shall Not Queue!!!\n(Wait until current active que is finished to schedule new queue type)\n\n")
            return
        
        # verify methods in new queue (needs work)
        if not self.coordinator.myReader.verify(compiled_queue):
            print("\n\nInsufficient Vespian Gas\n(method verification failed...)\n\n")
            return
        
        # add compiled methods to scheduled queue
        try: 
            empty_queue = self.coordinator.myReader.scheduled_queue.empty
        except:
            empty_queue = True
        if empty_queue:
            self.coordinator.myReader.scheduled_queue = compiled_queue
            print("Methods Queued")
        else:
            new_scheduled_queue = pd.concat([self.coordinator.myReader.scheduled_queue, compiled_queue])
            new_scheduled_queue = new_scheduled_queue.reset_index()
            self.coordinator.myReader.scheduled_queue = new_scheduled_queue
            print("Methods added to current Queue")

        # if not already running scheduled queue, start running
        if not self.coordinator.myReader.running:
            # start queue in method_reader
            queueThread = threading.Thread(target = self.coordinator.myReader.run_scheduled_methods, args=[]) #finishes the run
            queueThread.start()
            # start thread to watch status
            watchThread = threading.Thread(target = self.scheduled_queue_frame.watch_status, args=[]) #finishes the run
            watchThread.start()
    
    def clear_queue(self):  # rework 
        pass
        # self.wellList = []
        # self.methodList = []
    
    def select_file(self):  # rework
        pass
        # filetypes = (
        #     ('csv files', '*.csv'),
        #     ('All files', '*')
        # )

        # new_file = fd.askopenfilename(
        #     title='Add to Queue',
        #     initialdir='queues',
        #     filetypes=filetypes)
        
        # self.queue_to_run = new_file
        # self.RunButton["state"] =  "normal"
        
        # pathToQueue = self.queue_to_run
        # queueFile = pathlib.Path(pathToQueue)
        # if queueFile.exists ():
        #     queueFail = True
        # else:
        #     queueFail = False
 
        # while queueFail == False:
        #     self.queue_to_run = input("Invalid queue. Try again: ")
        #     pathToQueue = self.queue_to_run
        #     queueFile = pathlib.Path(pathToQueue)
        #     if queueFile.exists ():
        #         queueFail = True
        #     else:
        #         queueFail = False

        # # -----Get list from CSV queue.csv with pd. This is used for the RPi because the RPi doesn't have excel-----
        
        # col_list = ['Locations', 'Methods']
        # df = pd.read_csv(pathToQueue, usecols=col_list)
        # [self.wellList.append(well) for well in df["Locations"].tolist()]
        # [self.methodList.append(method) for method in df["Methods"].tolist()]
     
    def save_queue(self):  # rework 
        pass
        # filetypes = (
        #     ('CSV files', '*.csv'),
        #     ( 'All files', '*')
        # )

        # new_file = fd.asksaveasfile(
        #     title='Save a file',
        #     initialdir='queues',
        #     filetypes=filetypes)
        
        # if new_file.name.endswith(".csv"):
        #     new_file = new_file.name.replace(".csv","") + ".csv"
        # else:
        #     new_file = new_file.name + ".csv"
        
        # df = pd.DataFrame(data={'Locations':self.wellList,'Methods':self.methodList})
        # df.to_csv(new_file,index=False)      


class Queue_Handler:
    def __init__(self, queue_grid, coordinator):
        self.queue_handler_master = queue_grid
        self.coordinator = coordinator
        self.active_page = None
        
        self.row_buttons_frame = tk.Frame(self.queue_handler_master)
        self.row_buttons_frame.pack(side="left", fill="y")

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
        self.ms_stage_label = tk.StringVar(self.ms_queue_header, value=MS_HEADERS[0])
        self.ms_wellplate_label = tk.StringVar(self.ms_queue_header, value=MS_HEADERS[1])
        self.ms_sample_label = tk.StringVar(self.ms_queue_header, value=MS_HEADERS[2])
        self.ms_method_label = tk.StringVar(self.ms_queue_header, value=MS_HEADERS[3])
        tk.Entry(self.ms_queue_header, textvariable=self.ms_stage_label).pack(side='left')
        tk.Entry(self.ms_queue_header, textvariable=self.ms_wellplate_label).pack(side='left')
        tk.Entry(self.ms_queue_header, textvariable=self.ms_sample_label).pack(side='left')
        tk.Entry(self.ms_queue_header, textvariable=self.ms_method_label).pack(expand=True, fill="x", side='left')

        # fractionation queue headers
        self.frac_stage_label = tk.StringVar(self.frac_queue_header, value=FRAC_HEADERS[0])
        self.frac_wellplate_label = tk.StringVar(self.frac_queue_header, value=FRAC_HEADERS[1])
        self.frac_sample_label = tk.StringVar(self.frac_queue_header, value=FRAC_HEADERS[2])
        self.frac_elute_label = tk.StringVar(self.frac_queue_header, value=FRAC_HEADERS[3])
        self.frac_method_label = tk.StringVar(self.frac_queue_header, value=FRAC_HEADERS[4])
        tk.Entry(self.frac_queue_header, textvariable=self.frac_stage_label).pack(side='left')
        tk.Entry(self.frac_queue_header, textvariable=self.frac_wellplate_label).pack(side='left')
        tk.Entry(self.frac_queue_header, textvariable=self.frac_sample_label).pack(side='left')
        tk.Entry(self.frac_queue_header, textvariable=self.frac_elute_label).pack(side='left')
        tk.Entry(self.frac_queue_header, textvariable=self.frac_method_label).pack(expand=True, fill="x", side='left')

        # Add an initial row to queues
        self.add_row_buttons(1)
        self.ms_queue.insert(1, MS_Queue_Row_Inputs(self.ms_queue_frame))
        self.frac_queue.insert(1, Frac_Queue_Row_Inputs(self.frac_queue_frame))


    # Queue maker display functions

    def clear_grid(self):
        '''
        Only called when switching queue types.
        It clears everything from the queue grid so the proper grid can be displayed
        '''

        if self.active_page == 'Mass Spec':
            self.frac_queue_frame.pack_forget()
            self.ms_queue_frame.pack(expand=True, fill="both", side="left")
            

        elif self.active_page == 'Fractionation':
            self.ms_queue_frame.pack_forget()
            self.frac_queue_frame.pack(expand=True, fill="both", side="left")

        self.update_grid()
      
    def reset_grid(self):
        '''
        This function returns the column headers to the grid, then checks on the nimber of button rows needed.
        If the number of needed button rows has changed (eg we switch queue type), rows are added or removed.
        '''
        
        if self.active_page == 'Mass Spec':
             
            for frame in self.ms_queue:
                frame: tk.Frame = frame
                frame.pack_forget()
            
            for frame in self.ms_queue:
                frame: tk.Frame = frame
                frame.pack(fill="both", expand=True)
                # frame.config(height=STANDARD_ROW_HEIGHT)
            
                
        elif self.active_page == 'Fractionation':
            for frame in self.frac_queue:
                frame: tk.Frame = frame
                frame.pack_forget()

            for frame in self.frac_queue:
                frame: tk.Frame = frame
                frame.pack(fill="both", expand=True)
                # frame.config(height=STANDARD_ROW_HEIGHT) 

    def maintain_button_rows(self):
        '''
        Disables "Move Up" button on row 1.
        Disables "Move Down" button on last row.
        Ensures all other buttons are enabled. 
        '''
        if self.active_page == 'Mass Spec':
            queue_length = len(self.ms_queue)
        elif self.active_page == 'Fractionation':
            queue_length = len(self.frac_queue)
        else:
            queue_length = 1

        while len(self.queue_row_buttons) > queue_length:
            remove_buttons: Queue_Row_Buttons = self.queue_row_buttons.pop()
            remove_buttons.destroy()

        while len(self.queue_row_buttons) < queue_length:
            self.add_row_buttons(len(self.queue_row_buttons))

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
        
    def set_active_page(self, active_page):
        if self.active_page != active_page:
            self.active_page = active_page
            self.update_grid()

    def add_row_buttons(self, index):
        new_buttons = Queue_Row_Buttons(self.row_buttons_frame, index, self)
        self.queue_row_buttons.append(new_buttons)
        new_buttons.pack()
        # new_buttons.config(height=STANDARD_ROW_HEIGHT)


    # Queue Maker Button functions

    def  insert_row(self, buttons_index=None):
        '''
        Creates a new row of buttons, then inserts a new set of inputs at the indicated index.
        '''
        if buttons_index == None:
            buttons_index = len(self.queue_row_buttons)
        self.add_row_buttons(len(self.queue_row_buttons))

        if self.active_page == 'Mass Spec':
            self.ms_queue.insert(buttons_index, MS_Queue_Row_Inputs(self.ms_queue_frame))
        elif self.active_page == 'Fractionation':
            self.frac_queue.insert(buttons_index, Frac_Queue_Row_Inputs(self.frac_queue_frame))

        self.update_grid()

    def move_up(self, row_index):
        '''
        Moves the indicated row's current inputs up one row by poping it out and reinserting it one index less.
        '''
        print(self.active_page)
        if self.active_page == 'Mass Spec':
            move_item = self.ms_queue.pop(row_index)
            self.ms_queue.insert(row_index-1, move_item)
        elif self.active_page == 'Fractionation':
            move_item = self.frac_queue.pop(row_index)
            self.frac_queue.insert(row_index-1, move_item)

        self.update_grid()

    def move_down(self, row_index):
        '''
        Moves the indicated row's current inputs down one row by poping it out and reinserting it one index greater.
        '''
        print(self.active_page)
        if self.active_page == 'Mass Spec':
            move_item = self.ms_queue.pop(row_index)
            self.ms_queue.insert(row_index+1, move_item)
        elif self.active_page == 'Fractionation':
            move_item = self.frac_queue.pop(row_index)
            self.frac_queue.insert(row_index+1, move_item)

        self.update_grid()
    
    def delete_row(self, row_index):
        '''
        Removes the indicated inputs and destroys them, then removes the last row of buttons.
        Waits until the grid has been updated to destroy the button (in case this was the last row).
        '''
        print(self.active_page)
        
        if self.active_page == 'Mass Spec':
            remove_item: MS_Queue_Row_Inputs = self.ms_queue.pop(row_index)
            remove_item.destroy()
        elif self.active_page == 'Fractionation':
            remove_item: Frac_Queue_Row_Inputs = self.frac_queue.pop(row_index)
            remove_item.destroy()

        remove_item: Queue_Row_Buttons = self.queue_row_buttons.pop()      
        self.update_grid()
        remove_item.destroy() # go last to ensure all other tasks completed


    
    # functinos for active que display

    
class Scheduled_Queue(tk.Frame,):
    '''
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame, coordinator):
        super().__init__(master_frame)
        self.queue_type_string = tk.StringVar(value="Nothing in the Active Queue")
        self.coordinator: Coordinator = coordinator
        self.queue_type = None

        # main frames of active queue page
        self.type_frame = tk.Frame(self, highlightbackground="black", highlightthickness=2)
        self.current_run_frame = tk.Frame(self, pady=20, padx=5) #, highlightbackground="green", highlightthickness=2)
        self.scheduled_runs_frame = tk.Frame(self, padx=5) #, pady=20, highlightbackground="orange", highlightthickness=2)

        self.type_frame.pack() 
        self.current_run_frame.pack(fill="x")
        self.scheduled_runs_frame.pack(fill="both", expand=True)



        # inside type frame
        self.type_label = tk.Label(self.type_frame, textvariable=self.queue_type_string, font=(40))
        self.type_label.pack(side="left", fill="x")



        # inside current run frame
        self.stop_button_frame = tk.Frame(self.current_run_frame, padx=5) #, highlightbackground="purple", highlightthickness=2)
        self.current_run_label = tk.Label(self.current_run_frame, text="Currently Running")
        self.current_run_inner = tk.Frame(self.current_run_frame, highlightbackground="black", highlightthickness=2)

        self.stop_button_frame.pack(side="left", fill="y")
        self.current_run_label.pack(side="top", anchor="nw")
        self.current_run_inner.pack(side="top", fill="x")

        # inside stop button frame
        self.stop_button_spacer = tk.Label(self.stop_button_frame, text="")
        self.stop_button = tk.Button(self.stop_button_frame, text="Stop Run!", command=self.stop_immediately, width=12, background="indian red")

        self.stop_button_spacer.pack()
        self.stop_button.pack()

        # inside current run inner frame
        self.space_label_1 = tk.Label(self.current_run_inner, text="")
        self.space_label_2 = tk.Label(self.current_run_inner, text="")



        # inside scheduled runs frame
        self.scheduled_runs_buttons = tk.Frame(self.scheduled_runs_frame, padx=5) 
        self.scheduled_runs_label = tk.Label(self.scheduled_runs_frame, text="Scheduled Runs")
        self.scheduled_runs_inner = tk.Frame(self.scheduled_runs_frame, highlightbackground="black", highlightthickness=2)

        self.scheduled_runs_buttons.pack(side="left", fill="y")
        self.scheduled_runs_label.pack(side="top", anchor="nw")
        self.scheduled_runs_inner.pack(side="top", fill="both", expand=True)
        
        # inside scheduled runs buttons
        self.scheduled_buttons_spacer = tk.Label(self.scheduled_runs_buttons, text="")
        self.pause_button = tk.Button(self.scheduled_runs_buttons, text="Pause", command=self.pause_resume_scheduled_queue, width=12)
        self.clear_selected_button = tk.Button(self.scheduled_runs_buttons, text="Clear Selected", command=self.clear_selected_runs)
        self.clear_all_button = tk.Button(self.scheduled_runs_buttons, text="Clear All", command=self.clear_all_runs)

        self.scheduled_buttons_spacer.pack()
        self.pause_button.pack(fill="x")
        self.clear_selected_button.pack(fill="x")
        self.clear_all_button.pack(fill="x")

        # sample prep header
        self.sp_current_headers = Sample_Prep_Inputs(self.current_run_inner)
        self.sp_current_headers.method.set(MS_HEADERS[0])

        # ms headers 
        self.ms_current_headers = MS_Queue_Row_Inputs(self.current_run_inner)
        self.ms_current_headers.stage.set(MS_HEADERS[0])
        self.ms_current_headers.plate.set(MS_HEADERS[1])
        self.ms_current_headers.well.set(MS_HEADERS[2])
        self.ms_current_headers.method.set(MS_HEADERS[3])

        self.ms_scheduled_headers = MS_Queue_Row_Inputs(self.scheduled_runs_inner)
        self.ms_scheduled_headers.stage.set(MS_HEADERS[0])
        self.ms_scheduled_headers.plate.set(MS_HEADERS[1])
        self.ms_scheduled_headers.well.set(MS_HEADERS[2])
        self.ms_scheduled_headers.method.set(MS_HEADERS[3])

        # frac headers 
        self.frac_current_headers = Frac_Queue_Row_Inputs(self.current_run_inner)
        self.frac_current_headers.stage.set(FRAC_HEADERS[0])
        self.frac_current_headers.plate.set(FRAC_HEADERS[1])
        self.frac_current_headers.sample_wells.set(FRAC_HEADERS[2])
        self.frac_current_headers.elution_wells.set(FRAC_HEADERS[3])
        self.frac_current_headers.method.set(FRAC_HEADERS[4])
        
        self.frac_scheduled_headers = Frac_Queue_Row_Inputs(self.scheduled_runs_inner)
        self.frac_scheduled_headers.stage.set(FRAC_HEADERS[0])
        self.frac_scheduled_headers.plate.set(FRAC_HEADERS[1])
        self.frac_scheduled_headers.sample_wells.set(FRAC_HEADERS[2])
        self.frac_scheduled_headers.elution_wells.set(FRAC_HEADERS[3])
        self.frac_scheduled_headers.method.set(FRAC_HEADERS[4])


        self.update_scheduled_queue_display()

    def add_entry_headers(self):
        '''
        This method uses the pandas objects found
        '''
        pass
    
    def display_current_run(self):
        '''
        This method populates the current run frame when a method is running 
        '''
        pass

    def clear_current_run_display(self):
        '''
        This method clears the current run frame when a run has finished
        '''
        pass

    def display_scheduled_runs(self):
        '''
        This method populates the scheduled runs frame when there are runs in the scheduled queue
        '''
        pass

    def clear_scheduled_runs_display(self):
        '''
        This method removes all 
        '''
        pass
        
    def update_scheduled_queue_display(self):

        queue_type = self.queue_type
        queue_type = "Mass Spec"  #override for testing purposes

        if queue_type == "Sample Prep":
            self.queue_type_string.set("Sample Preparation")
            self.ms_current_headers.pack_forget()
            self.ms_scheduled_headers.pack_forget()
            self.frac_current_headers.pack_forget()
            self.frac_scheduled_headers.pack_forget() 
            # pack sample prep display
            
        elif queue_type == "Mass Spec":
            self.queue_type_string.set("Mass Spectrometry")
            # forget other displays
            self.frac_current_headers.pack_forget()
            self.frac_scheduled_headers.pack_forget()
            self.space_label_1.pack_forget()
            self.space_label_2.pack_forget()

            self.ms_current_headers.pack()
            self.ms_scheduled_headers.pack()
            
 
        elif queue_type == "Fractionation":
            self.queue_type_string.set("Fractionation")
            # forget other displays
            self.ms_current_headers.pack_forget()
            self.ms_scheduled_headers.pack_forget()
            self.space_label_1.pack_forget()
            self.space_label_2.pack_forget()

            self.frac_current_headers.pack()
            self.frac_scheduled_headers.pack()

        else:
            self.queue_type_string.set("Nothing in the Active Queue")
            self.ms_current_headers.pack_forget()
            self.ms_scheduled_headers.pack_forget()
            self.frac_current_headers.pack_forget()
            self.frac_scheduled_headers.pack_forget()

            self.space_label_1.pack()
            self.space_label_2.pack()
            

    # functions for active queue handling
    
    def watch_status(self):
        
        while self.coordinator.myReader.running:
            time.sleep(1)
            if self.coordinator.myReader.queue_changed:
                self.update_scheduled_queue_display()
                self.coordinator.myReader.queue_changed = False
            if not self.coordinator.myReader.running:
                self.queue_type = None
                self.update_scheduled_queue_display()  

    def stop_immediately(self):
        '''
        Pauses queue and interupts current run.
        '''
        self.coordinator.myReader.stop_current_run()

    def pause_resume_scheduled_queue(self):
        '''
        Pauses queue after finishing current run. 

        '''
        if self.coordinator.myReader.paused:
            self.coordinator.myReader.resume_scheduled_queue()
            # Change button color?
        elif not self.coordinator.myReader.paused:
            self.coordinator.myReader.pause_scheduled_queue()
            # Change button color?

    def clear_selected_runs(self):
        '''
        Removes selected runs from scheduled queue (selected using row oriented checkboxes). 
        Does not affect current run. 
        '''
        print("clear selected - currently just prints this statement.")

    def clear_all_runs(self):
        '''
        Remove all future runs from scheduled queue. Does not affect current run.
        '''
        self.coordinator.myReader.scheduled_queue = None
        self.coordinator.myReader.resume_scheduled_queue()
        print("Clear all - This should be working now.")


class Sample_Prep_Inputs(tk.Frame,):
    '''
    This class contains and displays the method for a sample prep protocol.
    It is designed to match the formating of the Mass Spec and Fractionation queues. 
    '''
    def __init__(self, master_frame):
        super().__init__(master_frame)
        
        self.method = tk.StringVar()

        self.method_label = tk.Label(self, text="Method")
        self.method_box = tk.Entry(self, textvariable=self.method)

        self.method_label.pack(side="left")
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


class MS_Queue_Row_Inputs(tk.Frame,):
    '''
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame):
        super().__init__(master_frame)
        
        self.stage = tk.StringVar()
        self.plate = tk.StringVar()
        self.well = tk.StringVar()
        self.method = tk.StringVar()

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
    def __init__(self, master_frame):
        super().__init__(master_frame)
        
        self.stage = tk.StringVar()
        self.plate = tk.StringVar()
        self.sample_wells = tk.StringVar()
        self.elution_wells = tk.StringVar()
        self.method = tk.StringVar()
        
        self.stage_box = tk.Entry(self, textvariable=self.stage)
        self.plate_box = tk.Entry(self, textvariable=self.plate)
        self.sample_wells_box = tk.Entry(self, textvariable=self.sample_wells)
        self.elution_wells_box = tk.Entry(self, textvariable=self.elution_wells)
        self.method_box = tk.Entry(self, textvariable=self.method)

        self.stage_box.pack(side="left")
        self.plate_box.pack(side="left")
        self.sample_wells_box.pack(side="left")
        self.elution_wells_box.pack(side="left")
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
    def __init__(self, master_frame, row_index, handler: Queue_Handler):
        super().__init__(master_frame)
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