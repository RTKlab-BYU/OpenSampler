import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
import time
import threading
import pandas as pd

from Classes.coordinator import Coordinator

STANDARD_ROW_HEIGHT = 100
SP_HEADERS = ["Method"]
MS_HEADERS = ["Stage", "Wellplate", "Well", "Method"]
FRAC_HEADERS = ["Stage", "Wellplate", "Well", "Elution Wells", "Method"]

SERIES_TYPE = type(pd.Series(dtype=float))
DATAFRAME_TYPE = type(pd.DataFrame(dtype=float))

class Queue_Gui(tk.Toplevel,):

    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Run Method")
        self.geometry("1000x600")
        # self.state("zoomed")
        self.coordinator: Coordinator = coordinator
        self.my_reader = self.coordinator.myReader
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

        self.upper_frame = tk.Frame(self.page_display_frame) 
        self.queue_frame = tk.Frame(self.page_display_frame) 
        self.sample_prep_frame = tk.Frame(self.page_display_frame)
        self.active_queue_frame = Active_Queue(self.page_display_frame, self.coordinator)

        # Canvas for scrolling through long que 
        self.canvas = tk.Canvas(self.queue_frame, width=4000, height = 1800, scrollregion=(0,0,4000,1800),)
        canvas_width = self.canvas.winfo_width()
        self.queue_grid = tk.Frame(self.canvas, width=canvas_width)

        self.y_scrollbar = tk.Scrollbar(self.queue_frame, orient="vertical", command=self.canvas.yview)       
        self.x_scrollbar = tk.Scrollbar(self.queue_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand = self.y_scrollbar.set, xscrollcommand = self.x_scrollbar.set)

        self.y_scrollbar.pack(side="right", fill="y")
        self.x_scrollbar.pack(side="bottom", fill="x")
        self.canvas.pack(fill="both", expand=True)
        
        self.queue_grid_window = self.canvas.create_window((4,4), window=self.queue_grid, anchor="nw", tags="self.queue_grid")
        self.queue_grid.bind("<Configure>", lambda x: self.reset_scroll_region(x))

        self.update()
        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-3)
        
        # Handler must come after que grid 
        self.queue_compiler = Queue_Compiler(self, self.coordinator)
        
        # file bar for ms and frac queues.
        self.file_bar = tk.Frame(self.upper_frame)
        self.file_bar.pack()

        self.clear_button = tk.Button(self.file_bar, text='Clear Queue', command= lambda:self.clear_queue())
        self.load_button = tk.Button(self.file_bar,text='Load Queue', command= lambda:self.load_queue_from_csv())
        self.save_button = tk.Button(self.file_bar,text="Save Queue", command= lambda:self.save_queue())

        self.clear_button.grid(row=0, column=1)
        self.load_button.grid(row=0, column=2)
        self.save_button.grid(row=0, column=3)


        # run bar for ms and frac queues.
        self.run_bar = tk.Frame(self.upper_frame)
        self.run_bar.pack()

        self.run_button = tk.Button(self.run_bar, text="Run Queue", command=lambda: self.run_button_clicked())
        self.run_button.grid(row=0, column=0)

        # In sample prep frame
        self.sp_run_button = tk.Button(self.sample_prep_frame, text="Run Method", command=lambda: self.run_button_clicked())
        
        self.sp_run_button.pack()
        self.queue_compiler.sp_queue_header.pack(expand=True, fill="x")
        self.queue_compiler.sp_inputs.pack(expand=True, fill="x")

        

        # Initial Page
        self.page_type.set("Sample Prep")
        self.load_page()

        # Reconfigure que when reconfiguring window
        self.bind("<Configure>", lambda x: self.reset_scroll_region(x))

    def reset_scroll_region(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        canvas_width = self.canvas.winfo_width()
        self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)

    def load_page(self):
        page_type = self.page_type.get()
        self.queue_compiler.set_active_page(page_type)
        
        if page_type == "Sample Prep":
            self.upper_frame.pack_forget()
            self.queue_frame.pack_forget()
            self.active_queue_frame.pack_forget()
            self.sample_prep_frame.pack(pady=50, padx=50, expand=True, fill="x", side="top", anchor="n")

        elif page_type == "Mass Spec":
            self.queue_compiler.toggle_ms_frac_display()
            self.sample_prep_frame.pack_forget()
            self.active_queue_frame.pack_forget()
            self.upper_frame.pack(fill="x")
            self.queue_frame.pack(fill="both", expand=True, padx=50)
            self.update()
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)         
            
            
        elif page_type == "Fractionation":
            self.queue_compiler.toggle_ms_frac_display()
            self.sample_prep_frame.pack_forget()
            self.active_queue_frame.pack_forget()
            self.upper_frame.pack(fill="x")
            self.queue_frame.pack(fill="both", expand=True, padx=50)
            self.update()
            canvas_width = self.canvas.winfo_width()
            self.canvas.itemconfig(self.queue_grid_window, width = canvas_width-4)
            

        elif page_type == "Active Queue":
            self.sample_prep_frame.pack_forget()
            self.upper_frame.pack_forget()
            self.queue_frame.pack_forget()
            self.active_queue_frame.pack(expand=True, fill="both")
        
    def compile_queue_to_schedule(self):
        '''
        This function is used to pull the parameters out of the entry values and package them as pandas dataframe object.
        '''

        page_type = self.page_type.get()
        self.queue_compiler.set_active_page(page_type)
        
        if page_type == "Sample Prep":
            queue_to_schedule = pd.DataFrame({SP_HEADERS[0]: []})

            queue_to_schedule.loc[0] = [self.queue_compiler.sp_inputs.method_var.get()]

            return queue_to_schedule            

        elif page_type == "Mass Spec":
            # package MS queue
            queue_to_schedule = pd.DataFrame({MS_HEADERS[0]: [], MS_HEADERS[1]: [], MS_HEADERS[2]: [], MS_HEADERS[3]: []})
            for entry in self.queue_compiler.ms_queue[1:]:
                ms_inputs: MS_Queue_Row_Inputs = entry
            
                temp_list = [ms_inputs.stage_var.get(), ms_inputs.wellplate_var.get(), ms_inputs.well_var.get(), ms_inputs.method_var.get()]
                queue_to_schedule.loc[len(queue_to_schedule.index)] = temp_list

            return queue_to_schedule
        
        elif page_type == "Fractionation":
            # package Frac queue
            queue_to_schedule = pd.DataFrame({FRAC_HEADERS[0]: [], FRAC_HEADERS[1]: [], FRAC_HEADERS[2]: [], FRAC_HEADERS[3]: [], FRAC_HEADERS[4]: []})
            for row, entry in enumerate(self.queue_compiler.frac_queue, 1):
                frac_inputs: Frac_Queue_Row_Inputs = self.queue_compiler.frac_queue[row]
                temp_list = [frac_inputs.stage_var.get(), frac_inputs.wellplate_var.get(), frac_inputs.sample_wells_var.get(), frac_inputs.elution_wells_var.get(), frac_inputs.method_var.get()]
                queue_to_schedule.loc[len(queue_to_schedule)] = temp_list

            return queue_to_schedule
        
    def run_button_clicked(self):
        self.schedule_queue()
        time.sleep(0.5)

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
        if not self.my_reader.running:
            compiled_queue = self.compile_queue_to_schedule()
            self.active_queue_frame.active_queue_type = new_queue_type
            self.active_queue_frame.format_active_queue_display()
        elif (new_queue_type == self.active_queue_frame.active_queue_type):
            compiled_queue = self.compile_queue_to_schedule()
        else:
            print(f"\nCurrent running queue type: {self.active_queue_frame.active_queue_type}")
            print(f"Attempting to schecdule queue type: {new_queue_type}")
            print("\n\nYou Shall Not Queue!!!\n(Wait until current active que is finished to schedule new queue type)\n\n")
            return
        
        # verify methods in new queue (needs work)
        if not self.my_reader.verify(compiled_queue):
            return
        
        # add compiled methods to scheduled queue
        try:
            # if scheduled queue is an empty dataframe, this returns True
            # if not empty, this will return False 
            empty_queue = self.my_reader.scheduled_queue.empty
        except:
            # if scheduled queue doesn't exist
            empty_queue = True

        if empty_queue:
            self.my_reader.scheduled_queue = compiled_queue
            self.scheduled_queue_changed = True


        else:
            new_scheduled_queue = pd.concat([self.my_reader.scheduled_queue, compiled_queue])
            new_scheduled_queue = new_scheduled_queue.reset_index(drop=True)
            self.my_reader.scheduled_queue = new_scheduled_queue
            self.scheduled_queue_changed = True

        # if not already running, activate scheduled queue
        if not self.my_reader.running:
            # start queue in method_reader
            queueThread = threading.Thread(target = self.my_reader.run_scheduled_methods, args=[]) #finishes the run
            queueThread.start()
            # start thread to watch status
            watchThread = threading.Thread(target = self.active_queue_frame.watch_status, args=[]) #finishes the run
            watchThread.start()

        self.my_reader.scheduled_queue_changed = True
    
    def clear_queue(self):  # removes all entries from the proposed MS or Frac queue pages
        self.queue_compiler.delete_grid()
        self.queue_compiler.add_row()
    
    def save_queue(self): 
        filetypes = (
            ('CSV files', '*.csv'),
            ( 'All files', '*')
        )

        new_file = fd.asksaveasfilename(parent=self, title='Save a file', initialdir='queues', filetypes=filetypes)
        
        if new_file == "":  # in the event of a cancel 
            return

        if new_file.endswith(".csv"):
            pass
        else:
            new_file = new_file + ".csv"
        
        df = self.compile_queue_to_schedule()
        df.to_csv(new_file, index=False)  

    def load_queue_from_csv(self):
        filetypes = (
            ('csv files', '*.csv'),
            ('All files', '*')
        )

        queue_file = fd.askopenfilename(parent=self, title='Open a file', initialdir='queues', filetypes=filetypes)
        
        if queue_file == "":  # in the event of a cancel 
            return
        
        if queue_file.endswith(".csv"):
            pass
        else:
            queue_file = queue_file + ".csv"
        
        df_of_queue = pd.read_csv(queue_file)
        temp_queue_list = self.queue_compiler.compile_list_from_dataframe(df_of_queue)
        self.queue_compiler.delete_grid()

        if self.page_type.get() == 'Mass Spec':
            self.queue_compiler.ms_queue += temp_queue_list
        elif self.page_type.get() == 'Fractionation':
            self.queue_compiler.frac_queue += temp_queue_list
        elif self.page_type.get() == 'Sample Prep':
            self.queue_compiler.sp_inputs += temp_queue_list


        self.queue_compiler.update_grid()        

class Queue_Compiler:
    '''
    This class hanles the displays preparing queues (as opposed to the actively running queue display).
    Each display is customized around information needed for the type of operations being planned.
    Displays can be toggled without losing individual progress. 
    '''
    def __init__(self, queue_page, coordinator):
        self.queue_page: Queue_Gui = queue_page
        self.coordinator = coordinator
        self.active_page = None

        # these queue frames are nested inside a canvas set (queue_frame - canvas - queue_grid) for scrollbar use
        self.ms_queue_frame = tk.Frame(self.queue_page.queue_grid)
        self.frac_queue_frame = tk.Frame(self.queue_page.queue_grid)
        
        # buttons for ms and frac
        self.row_buttons_frame = tk.Frame(self.queue_page.queue_grid)
        self.row_buttons_frame.pack(side="left", fill="y")
        self.buttons_header = tk.Frame(self.row_buttons_frame)
        self.buttons_header.pack()
        self.add_row_button = tk.Button(self.buttons_header, text="Add Row", command= lambda: self.add_row())
        self.add_row_button.pack(side=tk.LEFT)

        # headers (input labels) for respective queues
        self.sp_queue_header = Sample_Prep_Inputs(self.queue_page.sample_prep_frame, self.coordinator)
        self.ms_queue_header = MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator)
        self.frac_queue_header = Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator)

        self.sp_queue_header.sp_headers()
        self.ms_queue_header.ms_headers()
        self.frac_queue_header.frac_headers()

        self.ms_queue =  [self.ms_queue_header]
        self.frac_queue = [self.frac_queue_header]
        self.queue_row_buttons = [self.buttons_header]

        # Add an initial row to queues
        self.ms_queue.insert(1, MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator))
        self.frac_queue.insert(1, Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator))
        self.sp_inputs = Sample_Prep_Inputs(self.queue_page.sample_prep_frame, self.coordinator)
        self.maintain_button_rows()
        
    
        
    # Queue maker display functions
    def delete_grid(self):

        if self.active_page == 'Mass Spec':
            while len(self.ms_queue) > 1:
                remove_item: MS_Queue_Row_Inputs = self.ms_queue.pop(-1)
                remove_item.destroy()
            # self.ms_queue.insert(1, MS_Queue_Row_Inputs(self.ms_queue_frame))
        elif self.active_page == 'Fractionation':
            while len(self.frac_queue) > 1:
                remove_item: Frac_Queue_Row_Inputs = self.frac_queue.pop(-1)
                remove_item.destroy()
            # self.frac_queue.insert(1, Frac_Queue_Row_Inputs(self.frac_queue_frame))

        self.update_grid()

    def toggle_ms_frac_display(self):
        '''
        Only called when switching queue types.
        It clears everything from the queue grid so the proper grid can be displayed
        '''

        if self.active_page == 'Mass Spec':
            self.frac_queue_frame.pack_forget()
            self.ms_queue_frame.pack(expand=True, fill="both", side="left")
            if len(self.ms_queue) == 1:
                self.add_row()
            

        elif self.active_page == 'Fractionation':
            self.ms_queue_frame.pack_forget()
            self.frac_queue_frame.pack(expand=True, fill="both", side="left")
            if len(self.frac_queue) == 1:
                self.add_row()
      
    def reset_grid(self):
        '''
        This function returns the column headers to the grid, then checks on the number of button rows needed.
        If the number of needed button rows has changed (eg we switch queue type), rows are added or removed.
        '''
        
        if self.active_page == 'Mass Spec':
            cnt = 1
             
            for frame in self.ms_queue:
                frame: tk.Frame = frame
                frame.pack_forget()
            
            for frame in self.ms_queue:
                frame: tk.Frame = frame
                frame.pack(fill="both", expand=True)
                cnt += 1
   
        elif self.active_page == 'Fractionation':
            for frame in self.frac_queue:
                frame: tk.Frame = frame
                frame.pack_forget()

            for frame in self.frac_queue:
                frame: tk.Frame = frame
                frame.pack(fill="both", expand=True)

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

    def  add_row(self, buttons_index=None):
        '''
        Creates a new row of buttons, then inserts a new set of inputs at the indicated index.
        '''
        if buttons_index == None:
            buttons_index = len(self.queue_row_buttons)
        # self.add_row_buttons(len(self.queue_row_buttons))

        if self.active_page == 'Mass Spec':
            new_row = MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator)
            self.ms_queue.insert(buttons_index, new_row)
        elif self.active_page == 'Fractionation':
            new_row = Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator)
            self.frac_queue.insert(buttons_index, new_row)

        new_row.pack(fill="both", expand=True)
        self.maintain_button_rows()

    def  insert_row(self, buttons_index=None):
        '''
        Creates a new row of buttons, then inserts a new set of inputs at the indicated index.
        '''
        if buttons_index == None:
            buttons_index = len(self.queue_row_buttons)
        # self.add_row_buttons(len(self.queue_row_buttons))

        if self.active_page == 'Mass Spec':
            self.ms_queue.insert(buttons_index, MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator))
        elif self.active_page == 'Fractionation':
            self.frac_queue.insert(buttons_index, Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator))

        self.update_grid()

    def move_up(self, row_index):
        '''
        Moves the indicated row's current inputs up one row by poping it out and reinserting it one index less.
        '''

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
        
        if self.active_page == 'Mass Spec':
            remove_item: MS_Queue_Row_Inputs = self.ms_queue.pop(row_index)
            remove_item.destroy()
        elif self.active_page == 'Fractionation':
            remove_item: Frac_Queue_Row_Inputs = self.frac_queue.pop(row_index)
            remove_item.destroy()

        self.update_grid()

    def compile_list_from_dataframe(self, dataframe: pd.DataFrame):
            '''
            This method takes rows from a dataframe and converts them into tkinter frames.
            The values in each row become entries in the frame.
            The frames are compiled to a list which is returned.
            '''

            dataframe_as_list = []

            try:
                if dataframe.empty == True:
                    print("Dataframe is empty")
                    pass    
            
                elif self.active_page == "Sample Prep":
                    for row_index in range(dataframe.shape[0]):
                        scheduled_run = Sample_Prep_Inputs(self.queue_page.sample_prep_frame, self.coordinator)
                        scheduled_run.method_var.set(dataframe[SP_HEADERS[0]].loc[dataframe.index[row_index]])

                        dataframe_as_list.append(scheduled_run)

                elif self.active_page == "Mass Spec":
                    for row_index in range(dataframe.shape[0]):
                        scheduled_run = MS_Queue_Row_Inputs(self.ms_queue_frame, self.coordinator)
                        scheduled_run.stage_var.set(dataframe[MS_HEADERS[0]].loc[dataframe.index[row_index]])
                        scheduled_run.wellplate_var.set(dataframe[MS_HEADERS[1]].loc[dataframe.index[row_index]])
                        scheduled_run.well_var.set(dataframe[MS_HEADERS[2]].loc[dataframe.index[row_index]])
                        scheduled_run.method_var.set(dataframe[MS_HEADERS[3]].loc[dataframe.index[row_index]])

                        dataframe_as_list.append(scheduled_run)
                
                elif self.active_page == "Fractionation":
                    for row_index in range(dataframe.shape[0]):
                        scheduled_run = Frac_Queue_Row_Inputs(self.frac_queue_frame, self.coordinator)
                        scheduled_run.stage_var.set(dataframe[FRAC_HEADERS[0]].loc[dataframe.index[row_index]])
                        scheduled_run.wellplate_var.set(dataframe[FRAC_HEADERS[1]].loc[dataframe.index[row_index]])
                        scheduled_run.sample_wells_var.set(dataframe[FRAC_HEADERS[2]].loc[dataframe.index[row_index]])
                        scheduled_run.elution_wells_var.set(dataframe[FRAC_HEADERS[3]].loc[dataframe.index[row_index]])
                        scheduled_run.method_var.set(dataframe[FRAC_HEADERS[4]].loc[dataframe.index[row_index]])

                        dataframe_as_list.append(scheduled_run)
            except:
                print("Hit a snag trying to compile list from dataframe!")
                dataframe_as_list = []

            return dataframe_as_list

    
class Active_Queue(tk.Frame,):
    '''
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame, coordinator):
        super().__init__(master_frame)
        self.queue_type_string = tk.StringVar(value="Nothing in the Active Queue")
        self.coordinator: Coordinator = coordinator
        self.my_reader = self.coordinator.myReader
        self.active_queue_type = None
        self.scheduled_queue_list = []

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
        # self.clear_selected_button.pack(fill="x") # README we have no way to select runs, so this doesn't work
        self.clear_all_button.pack(fill="x")

        # sample prep header
        self.sp_current_headers = Sample_Prep_Inputs(self.current_run_inner, self.coordinator)
        self.sp_current_headers.sp_headers()

        # ms headers 
        self.ms_current_headers = MS_Queue_Row_Inputs(self.current_run_inner, self.coordinator)
        self.ms_current_headers.ms_headers()

        self.ms_scheduled_headers = MS_Queue_Row_Inputs(self.scheduled_runs_inner, self.coordinator)
        self.ms_scheduled_headers.ms_headers()

        # frac headers 
        self.frac_current_headers = Frac_Queue_Row_Inputs(self.current_run_inner, self.coordinator)
        self.frac_current_headers.frac_headers()
        
        self.frac_scheduled_headers = Frac_Queue_Row_Inputs(self.scheduled_runs_inner, self.coordinator)
        self.frac_scheduled_headers.frac_headers()

        # spacers
        self.current_run_spacer = tk.Label(self.current_run_inner, text="")
        self.current_run_spacer_2 = tk.Label(self.current_run_inner, text="")
        self.scheduled_run_spacer = tk.Label(self.scheduled_runs_inner, text="")

        # finally
        self.format_active_queue_display()

    def format_active_queue_display(self):
        '''
        This method retrieves the values of the current active que run,
        stores them in an appropriate frame class,
        and displays the frame inside the current run frame 
        '''

        if self.active_queue_type == "Sample Prep":

            try:
                self.active_que_current_run.destroy()
            except:
                pass

            self.active_que_current_run = Sample_Prep_Inputs(self.current_run_inner, self.coordinator)

            # remove previous displays if any
            self.ms_current_headers.pack_forget()
            self.frac_current_headers.pack_forget()

            self.current_run_spacer.pack_forget()
            self.current_run_spacer_2.pack_forget()

            self.ms_scheduled_headers.pack_forget()
            self.frac_scheduled_headers.pack_forget()

            self.scheduled_runs_frame.pack_forget()

            # add sp header
            self.sp_current_headers.pack(side="top", fill="x")
            self.active_que_current_run.pack(side="top", fill="x")

        elif self.active_queue_type == "Mass Spec":

            try:
                self.active_que_current_run.destroy()
            except:
                pass

            self.active_que_current_run = MS_Queue_Row_Inputs(self.current_run_inner, self.coordinator)

            self.sp_current_headers.pack_forget()
            self.frac_current_headers.pack_forget()

            self.current_run_spacer.pack_forget()
            self.current_run_spacer_2.pack_forget()
            
            self.frac_scheduled_headers.pack_forget()

            # add ms headers
            self.ms_current_headers.pack(side="top", fill="x")
            self.ms_scheduled_headers.pack(side="top", fill="x")
            self.active_que_current_run.pack(side="top", fill="x")

            self.scheduled_runs_frame.pack(fill="both", expand=True)

        elif self.active_queue_type == "Fractionation":

            try:
                self.active_que_current_run.destroy()
            except:
                pass

            self.active_que_current_run = Frac_Queue_Row_Inputs(self.current_run_inner, self.coordinator)

            self.sp_current_headers.pack_forget()
            self.ms_current_headers.pack_forget()

            self.current_run_spacer.pack_forget()
            self.current_run_spacer_2.pack_forget()

            self.ms_scheduled_headers.pack_forget()

            self.frac_current_headers.pack(side="top", fill="x")
            self.frac_scheduled_headers.pack(side="top", fill="x")
            self.active_que_current_run.pack(side="top", fill="x")

            self.scheduled_runs_frame.pack(fill="both", expand=True)

        else:
            self.sp_current_headers.pack_forget()
            self.ms_current_headers.pack_forget()
            self.frac_current_headers.pack_forget()

            self.ms_scheduled_headers.pack_forget()
            self.frac_scheduled_headers.pack_forget()

            try:
                self.active_que_current_run.destroy()
            except:
                pass

            self.current_run_spacer.pack()
            self.current_run_spacer_2.pack()

            self.scheduled_runs_frame.pack(fill="both", expand=True)

    def update_current_run_display(self):
        '''
        This method retrieves the values of the current active que run,
        stores them in an appropriate frame class,
        and displays the frame inside the current run frame 
        '''

        if self.active_queue_type == "Sample Prep":

            try:
                self.active_que_current_run.method_var.set(self.my_reader.current_run[SP_HEADERS[0]])
            except:
                self.active_que_current_run.method_var.set("")

        elif self.active_queue_type == "Mass Spec":

            try:
                self.active_que_current_run.stage_var.set(self.my_reader.current_run[MS_HEADERS[0]])
                self.active_que_current_run.wellplate_var.set(self.my_reader.current_run[MS_HEADERS[1]])
                self.active_que_current_run.well_var.set(self.my_reader.current_run[MS_HEADERS[2]])
                self.active_que_current_run.method_var.set(self.my_reader.current_run[MS_HEADERS[3]])
            except:
                self.active_que_current_run.stage_var.set("")
                self.active_que_current_run.wellplate_var.set("")
                self.active_que_current_run.well_var.set("")
                self.active_que_current_run.method_var.set("")

        elif self.active_queue_type == "Fractionation":

            try:
                self.active_que_current_run.stage_var.set(self.my_reader.current_run[MS_HEADERS[0]])
                self.active_que_current_run.wellplate_var.set(self.my_reader.current_run[MS_HEADERS[1]])
                self.active_que_current_run.sample_wells_var.set(self.my_reader.current_run[MS_HEADERS[2]])
                self.active_que_current_run.elution_wells_var.set(self.my_reader.current_run[MS_HEADERS[3]])
                self.active_que_current_run.method_var.set(self.my_reader.current_run[MS_HEADERS[4]])
            except:
                self.active_que_current_run.stage_var.set("")
                self.active_que_current_run.wellplate_var.set("")
                self.active_que_current_run.sample_wells_var.set("")
                self.active_que_current_run.elution_wells_var.set("")
                self.active_que_current_run.method_var.set("")

        else:
            pass

    def display_scheduled_runs(self):
        '''
        This method populates the scheduled runs frame when there are runs in the scheduled queue
        '''
        
        if self.active_queue_type == "Sample Prep":
            pass

        elif self.active_queue_type in ("Mass Spec", "Fractionation"):
            frame: tk.Frame
            for frame in self.scheduled_queue_list:
                frame.pack(side="top", fill="x")

        else:
            pass

    def compile_list_from_dataframe(self, dataframe: pd.DataFrame, queue_type=None):
        '''
        This method takes rows from a dataframe and converts them into tkinter frames.
        The values in each row become entries in the frame.
        The frames are compiled to a list which is returned.
        '''

        dataframe_as_list = []
        skip = False

        if queue_type == None:
            queue_type = self.active_queue_type

        try:
            if dataframe.empty == True:
                skip = True
        except:
            # print("Dataframe not recognized!!!")
            skip = True

        if skip:
            pass

        elif queue_type == "Sample Prep":
            for row_index in range(dataframe.shape[0]):
                scheduled_run = Sample_Prep_Inputs(self.scheduled_runs_inner, self.coordinator)
                scheduled_run.method_var.set(dataframe[SP_HEADERS[0]].loc[dataframe.index[row_index]])

                dataframe_as_list.append(scheduled_run)

        elif queue_type == "Mass Spec":
            for row_index in range(dataframe.shape[0]):
                scheduled_run = MS_Queue_Row_Inputs(self.scheduled_runs_inner, self.coordinator)
                scheduled_run.stage_var.set(dataframe[MS_HEADERS[0]].loc[dataframe.index[row_index]])
                scheduled_run.wellplate_var.set(dataframe[MS_HEADERS[1]].loc[dataframe.index[row_index]])
                scheduled_run.well_var.set(dataframe[MS_HEADERS[2]].loc[dataframe.index[row_index]])
                scheduled_run.method_var.set(dataframe[MS_HEADERS[3]].loc[dataframe.index[row_index]])

                dataframe_as_list.append(scheduled_run)
        
        elif queue_type == "Fractionation":
            for row_index in range(dataframe.shape[0]):
                scheduled_run = Frac_Queue_Row_Inputs(self.scheduled_runs_inner, self.coordinator)
                scheduled_run.stage_var.set(dataframe[FRAC_HEADERS[0]].loc[dataframe.index[row_index]])
                scheduled_run.wellplate_var.set(dataframe[FRAC_HEADERS[1]].loc[dataframe.index[row_index]])
                scheduled_run.sample_wells_var.set(dataframe[FRAC_HEADERS[2]].loc[dataframe.index[row_index]])
                scheduled_run.elution_wells_var.set(dataframe[FRAC_HEADERS[3]].loc[dataframe.index[row_index]])
                scheduled_run.method_var.set(dataframe[FRAC_HEADERS[4]].loc[dataframe.index[row_index]])

                dataframe_as_list.append(scheduled_run)
        

        return dataframe_as_list

    def clear_scheduled_runs_display(self):
        '''
        This method removes all 
        '''

        frame: tk.Frame
        for frame in self.scheduled_queue_list:
            
            frame.destroy()
        
        self.scheduled_queue_list = []
        
    def update_scheduled_queues_display(self):

        self.clear_scheduled_runs_display()

        self.scheduled_queue_list = self.compile_list_from_dataframe(self.my_reader.scheduled_queue)

        self.display_scheduled_runs()
    
    def watch_status(self):
        
        while self.my_reader.running:
            time.sleep(1)

            # check if there is a current_run, value can be None or a pandas series
            try: 
                no_current_run = self.my_reader.current_run.empty()
            except:
                no_current_run = True

            if self.scheduled_queue_list == [] and no_current_run:
                self.my_reader.running = False
                self.my_reader.queue_paused = False
                self.pause_button.config(text="Pause")
                self.update_scheduled_queues_display()
                self.update_current_run_display()
                break

            if self.my_reader.scheduled_queue_changed:
                self.update_scheduled_queues_display()  # change this
                self.my_reader.scheduled_queue_changed = False

            if self.my_reader.current_run_changed:
                self.update_current_run_display()  # change this
                self.my_reader.current_run_changed = False

            if self.my_reader.update_pause_button:
                if self.my_reader.queue_paused:
                    self.pause_button.config(text="Resume")
                    self.my_reader.update_pause_button = False
                elif not self.my_reader.queue_paused:
                    self.pause_button.config(text="Pause")
                    self.my_reader.update_pause_button = False
            
    def stop_immediately(self):
        '''
        Pauses queue and interupts current run.
        '''
        if not self.my_reader.running:
            return

        if not self.scheduled_queue_list == []:
            self.my_reader.pause_scheduled_queue()

        self.my_reader.stop_current_run()

    def pause_resume_scheduled_queue(self):
        '''
        Pauses queue after finishing current run. 

        '''
        if not self.my_reader.running:
            print("Currently No Runs Scheduled")
            return
        
        if self.scheduled_queue_list == []:
            self.my_reader.queue_paused = False
            self.my_reader.update_pause_button = True
            print("Currently No Runs Scheduled")
            return
        
        if self.my_reader.queue_paused:
            self.my_reader.resume_scheduled_queue()
        elif not self.my_reader.queue_paused:
            self.my_reader.pause_scheduled_queue()

    def clear_selected_runs(self):
        '''
        Removes selected runs from scheduled queue (selected using row oriented checkboxes). 
        Does not affect current run. 
        '''
        print("\nclear selected - currently just prints this statement.\n")

        # self.scheduled_queue_changed = True

    def clear_all_runs(self):
        '''
        Remove all future runs from scheduled queue. Does not affect current run.
        '''
        if not self.my_reader.running:
            return
        
        if not self.scheduled_queue_list == []:
            self.my_reader.scheduled_queue = None  # overwrite any scheduled runs
            self.my_reader.scheduled_queue_changed = True
            self.my_reader.resume_scheduled_queue()  # if paused, resume
            print("Clearing scheduled queue. Current run will continue unless interupted.")


class Sample_Prep_Inputs(tk.Frame,):
    '''
    This class contains and displays the method for a sample prep protocol.
    It is designed to match the formating of the Mass Spec and Fractionation queues. 
    '''
    def __init__(self, master_frame, coordinator):
        super().__init__(master_frame)
        
        
        self.method_var = tk.StringVar()

        self.method_box = tk.Entry(self, textvariable=self.method_var)

        self.method_box.pack(expand=True, fill="x", side="left")
        
        self.method_box.bind('<Double-Button-1>', lambda x: self.select_method(x))


    # sample prep header
    def sp_headers(self):

        self.method_var.set(SP_HEADERS[0])
        self.method_box.config(state="readonly")

        self.method_box.unbind('<Double-Button-1>')

    def select_method(self, event):
        filetypes = (
            ('JSON files', '*.json'),
            ('All files', '*')
        )

        file_path = fd.askopenfilename(parent=self, title='Open a file', initialdir='methods', filetypes=filetypes)
        
        if file_path == "":  # in the event of a cancel 
            return
        
        self.method_var.set(file_path)
        

class MS_Queue_Row_Inputs(tk.Frame,):
    '''
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame, coordinator):
        super().__init__(master_frame)
        self.coordinator = coordinator
        
        self.stage_var = tk.StringVar()
        self.wellplate_var = tk.StringVar()
        self.well_var = tk.StringVar()
        self.method_var = tk.StringVar()

        try:
            self.stage_options = list(self.coordinator.myModules.myStages.keys())
        except:
            self.stage_options = []

        self.stage_box = ttk.Combobox(self, width=30, values=self.stage_options, textvariable=self.stage_var)
        self.wellplate_box = tk.Entry(self, width=30, textvariable=self.wellplate_var)  # changing this to combobox soon!
        self.well_box = tk.Entry(self, width=30, textvariable=self.well_var)
        self.method_box = tk.Entry(self, textvariable=self.method_var)

        self.stage_box.pack(side="left")
        self.wellplate_box.pack(side="left")
        self.well_box.pack(side="left")
        self.method_box.pack(expand=True, fill="x", side="left")
        
        self.method_box.bind('<Double-Button-1>', lambda x: self.select_method(x))


    # MS queue headers
    def ms_headers(self):
        self.stage_box.destroy()
        self.wellplate_box.destroy()
        self.well_box.pack_forget()
        self.method_box.pack_forget()

        self.stage_box = tk.Entry(self, width=33, textvariable=self.stage_var)
        self.wellplate_box = tk.Entry(self, width=30, textvariable=self.wellplate_var)

        self.stage_box.pack(side="left")
        self.wellplate_box.pack(side="left")
        self.well_box.pack(side="left")
        self.method_box.pack(expand=True, fill="x", side="left")

        self.stage_var.set(MS_HEADERS[0])
        self.wellplate_var.set(MS_HEADERS[1])
        self.well_var.set(MS_HEADERS[2])
        self.method_var.set(MS_HEADERS[3])

        self.stage_box.config(state="readonly")
        self.wellplate_box.config(state="readonly")
        self.well_box.config(state="readonly")
        self.method_box.config(state="readonly")

        self.method_box.unbind('<Double-Button-1>')


    def select_method(self, event):
        filetypes = (
            ('JSON files', '*.json'),
            ('All files', '*')
        )

        file_path = fd.askopenfilename(parent=self, title='Open a file', initialdir='methods', filetypes=filetypes)
        
        if file_path == "":  # in the event of a cancel 
            return
        
        self.method_var.set(file_path)


class Frac_Queue_Row_Inputs(tk.Frame,):
    '''
    Currently identical to MS_Queue_Row_Inputs
    
    This class contains and displays the inputs needed for each protocol in the queue.
    It assigns a row index to each instance in order to inform the affect those buttons have on the corresponding rows of inputs
    '''
    def __init__(self, master_frame, coordinator):
        super().__init__(master_frame)
        self.coordinator = coordinator
        self.entry_width = 30
        
        self.stage_var = tk.StringVar()
        self.wellplate_var = tk.StringVar()
        self.sample_wells_var = tk.StringVar()
        self.elution_wells_var = tk.StringVar()
        self.method_var = tk.StringVar()

        try:
            self.stage_options = list(self.coordinator.myModules.myStages.keys())
        except:
            self.stage_options = []
        
        self.stage_box = ttk.Combobox(self, width=self.entry_width, values=self.stage_options, textvariable=self.stage_var)
        self.wellplate_box = tk.Entry(self, width=self.entry_width, textvariable=self.wellplate_var)  # changing this to combobox soon!
        self.sample_wells_box = tk.Entry(self, width=self.entry_width, textvariable=self.sample_wells_var)
        self.elution_wells_box = tk.Entry(self, width=self.entry_width, textvariable=self.elution_wells_var)
        self.method_box = tk.Entry(self, textvariable=self.method_var)

        self.stage_box.pack(side="left")
        self.wellplate_box.pack(side="left")
        self.sample_wells_box.pack(side="left")
        self.elution_wells_box.pack(side="left")
        self.method_box.pack(expand=True, fill="x", side="left")        

        self.method_box.bind('<Double-Button-1>', lambda x: self.select_method(x))


    # fractionation queue headers
    def frac_headers(self):
        self.stage_box.destroy()
        self.wellplate_box.destroy()
        self.sample_wells_box.pack_forget()
        self.elution_wells_box.pack_forget()
        self.method_box.pack_forget()

        self.stage_options = []

        self.stage_box = tk.Entry(self, width=self.entry_width+3, textvariable=self.stage_var)
        self.wellplate_box = tk.Entry(self, width=self.entry_width, textvariable=self.wellplate_var)

        self.stage_box.pack(side="left")
        self.wellplate_box.pack(side="left")
        self.sample_wells_box.pack(side="left")
        self.elution_wells_box.pack(side="left")
        self.method_box.pack(expand=True, fill="x", side="left")  

        self.stage_var.set(FRAC_HEADERS[0])
        self.wellplate_var.set(FRAC_HEADERS[1])
        self.sample_wells_var.set(FRAC_HEADERS[2])
        self.elution_wells_var.set(FRAC_HEADERS[3])
        self.method_var.set(FRAC_HEADERS[4])

        self.stage_box.config(state="readonly")
        self.wellplate_box.config(state="readonly")
        self.sample_wells_box.config(state="readonly")
        self.elution_wells_box.config(state="readonly")
        self.method_box.config(state="readonly")

        self.method_box.unbind('<Double-Button-1>')

    def select_method(self, event):  # still needs work
        filetypes = (
            ('JSON files', '*.json'),
            ('All files', '*')
        )

        file_path = fd.askopenfilename(parent=self, title='Open a file', initialdir='methods', filetypes=filetypes)
        
        if file_path == "":  # in the event of a cancel 
            return
        
        self.method_var.set(file_path)
        

class Queue_Row_Buttons(tk.Frame,):
    '''
    This class is used to replicate the movement options for each queue row
    Each index has a row index to inform the affect those buttons have on the corresponding rows of inputs.
    Button rows do not need to move around as the inputs do, but the number of button rows should always match 
        the number of input rows.
    '''
    def __init__(self, master_frame, row_index, queue_compiler: Queue_Compiler):
        super().__init__(master_frame)
        self.row = row_index
        self.queue_compiler = queue_compiler

        self.insert = tk.Button(self, text="Insert", command=lambda: self.queue_compiler.insert_row(self.row))
        self.delete = tk.Button(self, text="Delete", command=lambda: self.queue_compiler.delete_row(self.row))
        self.move_up = tk.Button(self, text="Up", command=lambda: self.queue_compiler.move_up(self.row))
        self.move_down = tk.Button(self, text="Down", command=lambda: self.queue_compiler.move_down(self.row))

        self.insert.grid(row=0, column=0)
        self.delete.grid(row=0, column=1)
        self.move_up.grid(row=0, column=2)
        self.move_down.grid(row=0, column=3)