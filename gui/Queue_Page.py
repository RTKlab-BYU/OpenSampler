import tkinter as tk
from tkinter import filedialog as fd
import time
import threading
import pathlib
import pandas as pd

from Classes.coordinator import Coordinator
from Classes.method_reader import MethodReader

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
        self.page_frame = tk.Frame(self)
        self.page_frame.pack(pady=20)

        self.sample_prep_page = tk.Radiobutton(self.page_frame, text="Sample Preparation", variable=self.page_type, value="Sample Prep", command=self.load_page)
        self.mass_spec_page = tk.Radiobutton(self.page_frame, text="Mass Spectrometry", variable=self.page_type, value="Mass Spec", command=self.load_page)
        self.fractionation_page = tk.Radiobutton(self.page_frame, text="Fractionation", variable=self.page_type, value="Fractionation", command=self.load_page)
        self.scheduled_queue_page = tk.Radiobutton(self.page_frame, text="Active Queue", variable=self.page_type, value="Active Queue", command=self.load_page)

        self.sample_prep_page.grid(row=0,column=0)
        self.mass_spec_page.grid(row=0,column=1)
        self.fractionation_page.grid(row=0,column=2)
        self.scheduled_queue_page.grid(row=0,column=3)

        # Frame that changes based on page type
        self.master_frame = tk.Frame(self) 
        self.master_frame.pack(fill="both")

        self.upper_frame = tk.Frame(self.master_frame)
        self.queue_frame = tk.Frame(self.master_frame) 
        self.sample_prep_frame = tk.Frame(self.master_frame)
        self.scheduled_queue_frame = Scheduled_Queue(self.master_frame, self.coordinator)

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

        self.clear_button = tk.Button(self.file_bar, text='Clear Queue', command= lambda:self.clear_queue())
        self.load_button = tk.Button(self.file_bar,text='Load Queue', command= lambda:self.select_file())
        self.save_button = tk.Button(self.file_bar,text="Save Queue", command= lambda:self.save_queue())

        self.clear_button.pack()
        self.load_button.pack()
        self.save_button.pack()


        # run bar for ms and frac queues.
        self.run_bar = tk.Frame(self.upper_frame)
        self.run_bar.pack()

        self.RunButton = tk.Button(self.run_bar, text="Run Queue",command=lambda: self.schedule_que(),justify=tk.LEFT)
        self.RunButton.grid(row=0, column=0)

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
            self.sample_prep_frame.pack()

        elif page_type == "Mass Spec":
            self.sample_prep_frame.pack_forget()
            self.scheduled_queue_frame.pack_forget()
            self.upper_frame.pack()
            self.queue_frame.pack(fill="both", expand=True)
            self.update()
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)         
            self.handler.clear_grid()
            
        elif page_type == "Fractionation":
            self.sample_prep_frame.pack_forget()
            self.scheduled_queue_frame.pack_forget()
            self.upper_frame.pack()
            self.queue_frame.pack(fill="both", expand=True)
            self.update()
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)
            self.handler.clear_grid()

        elif page_type == "Active Queue":
            self.sample_prep_frame.pack_forget()
            self.upper_frame.pack_forget()
            self.queue_frame.pack_forget()
            self.scheduled_queue_frame.pack()
        
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
            self.ms_queue_to_schedule = pd.DataFrame({"Stage": [], "Wellplate": [], "Well": [], "Method": []})
            for entry in self.handler.ms_queue[1:]:
                ms_inputs: MS_Queue_Row_Inputs = entry
            
                temp_list = [ms_inputs.stage.get(), ms_inputs.plate.get(), ms_inputs.well.get(), ms_inputs.method.get()]
                self.ms_queue_to_schedule.loc[len(self.ms_queue_to_schedule.index)] = temp_list
            return self.ms_queue_to_schedule
        
        elif page_type == "Fractionation":
            # package Frac queue
            self.frac_queue_to_schedule = pd.DataFrame({"Stage": [], "Wellplate": [], "Sample Wells": [], "Elution Wells": [], "Method": []})
            for row, entry in enumerate(self.handler.frac_queue, 1):
                frac_inputs: Frac_Queue_Row_Inputs = self.handler.frac_queue[row]
                temp_list = [frac_inputs.stage.get(), frac_inputs.plate.get(), frac_inputs.pool_wells.get(), frac_inputs.method.get(), frac_inputs.target_well.get()]
                self.frac_queue_to_schedule.loc[len(self.frac_queue_to_schedule.index)] = temp_list
            return self.frac_queue_to_schedule
                    
    def schedule_que(self):
        '''
        Compile the current queue into a pandas dataframe.
        Verify the methods.
        Add the dataframe to the schedule queue,
        If not currently running, begin running.
        '''

        # start thread to run queue
        new_queue_type = self.page_type.get()

        if new_queue_type == self.handler.active_page:
            compiled_queue = self.compile_queue()
        else:
            print("\n\nYou Shall Not Queue!!!\n(Wait until current active que is finished to schedule new queue type)\n\n")
            return

        if not self.coordinator.myReader.verify(compiled_queue):
            print("\n\nInsufficient Vespian Gas\n(method verification failed...)\n\n")
            return
        
        try: 
            empty_queue = self.coordinator.myReader.scheduled_queue.empty
        except:
            empty_queue = (self.coordinator.myReader.scheduled_queue == None)
        if empty_queue:
            self.coordinator.myReader.scheduled_queue = compiled_queue
        else:
            self.coordinator.myReader.scheduled_queue.append(compiled_queue)  # Not append, this is a pandas
            
            

        if self.coordinator.myReader.running:
            pass
        else:
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
        self.ms_stage_label = tk.StringVar(self.ms_queue_header, value="Stage")
        self.ms_wellplate_label = tk.StringVar(self.ms_queue_header, value="Wellplate")
        self.ms_sample_label = tk.StringVar(self.ms_queue_header, value="Sample Well")
        self.ms_method_label = tk.StringVar(self.ms_queue_header, value="Method Path")
        tk.Entry(self.ms_queue_header, textvariable=self.ms_stage_label).pack(side='left')
        tk.Entry(self.ms_queue_header, textvariable=self.ms_wellplate_label).pack(side='left')
        tk.Entry(self.ms_queue_header, textvariable=self.ms_sample_label).pack(side='left')
        tk.Entry(self.ms_queue_header, textvariable=self.ms_method_label).pack(expand=True, fill="x", side='left')

        # fractionation queue headers
        self.frac_stage_label = tk.StringVar(self.frac_queue_header, value="Stage")
        self.frac_wellplate_label = tk.StringVar(self.frac_queue_header, value="Wellplate")
        self.frac_sample_label = tk.StringVar(self.frac_queue_header, value="Sample Wells")
        self.frac_elute_label = tk.StringVar(self.frac_queue_header, value="Elution Wells")
        self.frac_method_label = tk.StringVar(self.frac_queue_header, value="Method Path")
        tk.Entry(self.frac_queue_header, textvariable=self.frac_stage_label).pack(side='left')
        tk.Entry(self.frac_queue_header, textvariable=self.frac_wellplate_label).pack(side='left')
        tk.Entry(self.frac_queue_header, textvariable=self.frac_sample_label).pack(side='left')
        tk.Entry(self.frac_queue_header, textvariable=self.frac_elute_label).pack(side='left')
        tk.Entry(self.frac_queue_header, textvariable=self.frac_method_label).pack(expand=True, fill="x", side='left')

        # Add an initial row to queues
        new_buttons = Queue_Row_Buttons(self.row_buttons_frame, self.coordinator, 1, self)
        self.queue_row_buttons.append(new_buttons)
        new_buttons.pack()
        self.ms_queue.insert(1, MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator))
        self.frac_queue.insert(1, Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator))


    # Queue maker display functions

    def clear_grid(self):
        '''
        Only called when switching queue types.
        It clears everything from the queue grid so the proper grid can be displayed
        '''

        if self.active_page == 'Mass Spec':
            self.frac_queue_frame.pack_forget()
            self.ms_queue_frame.pack(expand=True, fill="x", side="left")
            

        elif self.active_page == 'Fractionation':
            self.ms_queue_frame.pack_forget()
            self.frac_queue_frame.pack(expand=True, fill="x", side="left")

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
                frame.pack(fill="x", expand=True)
            
                
        elif self.active_page == 'Fractionation':
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
        if self.active_page == 'Mass Spec':
            queue = len(self.ms_queue)
        elif self.active_page == 'Fractionation':
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
        
    def set_active_page(self, active_page):
        if self.active_page != active_page:
            self.active_page = active_page
            self.update_grid()



    # Queue Maker Button functions

    def  insert_row(self, buttons_index=None):
        '''
        Creates a new row of buttons, then inserts a new set of inputs at the indicated index.
        '''
        if buttons_index == None:
            buttons_index = len(self.queue_row_buttons)
        # print(self.active_page)
        new_buttons = Queue_Row_Buttons(self.row_buttons_frame, self.coordinator, len(self.queue_row_buttons), self)
        self.queue_row_buttons.append(new_buttons)
        new_buttons.pack()
        if self.active_page == 'Mass Spec':
            self.ms_queue.insert(buttons_index, MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator))
        elif self.active_page == 'Fractionation':
            self.frac_queue.insert(buttons_index, Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator))

        
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

    
class Sample_Prep_Frame(tk.Frame,):
    '''
    This class allows the user to select and schedule a sample preparation method
    '''
    def __init__(self, master_frame):
        super().__init__(master_frame)

        self.stage = tk.StringVar()
        self.stage_box = tk.Entry(self, textvariable=self.stage)
        self.stage_box.pack()


class Scheduled_Queue(tk.Frame,):
    '''
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame, coordinator):
        super().__init__(master_frame)
        self.run_type = tk.StringVar(value="Nothing in the Active Queue")
        self.coordinator: Coordinator = coordinator

        # main frames of active queue page
        self.type_frame = tk.Frame(self)
        self.current_run_frame = tk.Frame(self)
        self.scheduled_runs_frame = tk.Frame(self)

        self.type_frame.pack(side="top")
        self.current_run_frame.pack(side="top")
        self.scheduled_runs_frame.pack(side="top")

        # inside type frame
        self.type_label = tk.Label(self.type_frame, textvariable=self.run_type)
        self.type_label.pack(side="left", fill="x")

        # inside current run frame
        self.stop_button = tk.Button(self.current_run_frame, text="Stop Run!",command=self.stop_immediately)
        self.current_run_label = tk.Label(self.current_run_frame, text="Currently Running")
        self.current_run_inner = tk.Frame(self.current_run_frame)

        self.stop_button.pack(side="left")
        self.current_run_label.pack(side="top", anchor="nw")
        self.current_run_inner.pack(side="top")

        # inside scheduled runs frame
        self.scheduled_runs_buttons = tk.Frame(self.scheduled_runs_frame)
        self.scheduled_runs_label = tk.Label(self.scheduled_runs_frame, text="Scheduled")
        self.scheduled_runs_inner = tk.Frame(self.scheduled_runs_frame)

        self.scheduled_runs_buttons.pack(side="left")
        
        # scheduled runs buttons
        self.pause_button = tk.Button(self.scheduled_runs_buttons, text="Pause", command=self.pause_resume_scheduled_queue)
        self.clear_selected_button = tk.Button(self.scheduled_runs_buttons, text="Clear Selected", command=self.clear_selected_runs)
        self.clear_all_button = tk.Button(self.scheduled_runs_buttons, text="Clear All", command=self.clear_all_runs)
        self.pause_button.pack()
        self.clear_selected_button.pack()
        self.clear_all_button.pack()

        # ms headers 
        self.ms_current_headers = tk.Frame(self.current_run_inner)
        self.ms_scheduled_headers = tk.Frame(self.current_run_inner)

        # MS Headers
        self.ms_stage_label_1 = tk.Entry(self.ms_current_headers, textvariable="Stage")
        self.ms_stage_label_1.pack(side='left')
        self.ms_wellplate_label_1 = tk.Entry(self.ms_current_headers, textvariable="Wellplate")
        self.ms_wellplate_label_1.pack(side='left')
        self.ms_sample_label_1 = tk.Entry(self.ms_current_headers, textvariable="Sample Well")
        self.ms_sample_label_1.pack(side='left')
        self.ms_method_label_1 = tk.Entry(self.ms_current_headers, textvariable="Method")
        self.ms_method_label_1.pack(expand=True, fill="x", side='left')

        self.ms_stage_label_2 = tk.Entry(self.ms_current_headers, textvariable="Stage")
        self.ms_stage_label_2.pack(side='left')
        self.ms_wellplate_label_2 = tk.Entry(self.ms_current_headers, textvariable="Wellplate")
        self.ms_wellplate_label_2.pack(side='left')
        self.ms_sample_label_2 = tk.Entry(self.ms_current_headers, textvariable="Sample Well")
        self.ms_sample_label_2.pack(side='left')
        self.ms_method_label_2 = tk.Entry(self.ms_current_headers, textvariable="Method")
        self.ms_method_label_2.pack(expand=True, fill="x", side='left')


        # add 
        self.current_headers = None
        self.current_specs = None

    
        
    def update_scheduled_queue_display(self, queue_type):

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
            

    # functions for active queue handling
    
    def watch_status(self):

        time.sleep(5)
        
        while self.coordinator.myReader.running:
            time.sleep(1)
            if self.coordinator.myReader.queue_changed:
                self.update_scheduled_queue_display()
                self.coordinator.myReader.queue_changed = False
            if not self.coordinator.myReader.running:
                self.update_scheduled_queue_display("Done")  

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