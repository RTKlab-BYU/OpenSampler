from gui.Basic_Connect import Connect
from gui.Labware import Labware
from gui.Method_Creation import Method_Creator
from gui.Queue_Page import Queue_Gui
from gui.Manual import Manual

import tkinter as tk

from PIL import ImageTk
import PIL.Image


class HomePage:
    def __init__(self, coordinator):
        self.homePage = tk.Tk()
        self.homePage.geometry("750x750")
        self.homePage.title("OpenLC")

        self.coordinator = coordinator
        
        tk.Label(self.homePage, text="OpenLC Home Page", font="Helvetica 24",justify=tk.LEFT).pack(side=tk.TOP)
        
        #######Nav Buttons#############
        navBar = tk.Frame(self.homePage)
        navBar.pack(side=tk.TOP)

        self.system = None
        self.labware = None
        self.methods = None
        self.queue = None
        self.manual_control = None

        self.system_button = tk.Button(navBar, text="System", command=self.open_system_page)
        self.labware_button = tk.Button(navBar, text="Labware", command=self.open_labware_page)
        self.methods_button = tk.Button(navBar, text="Methods", command=self.open_methods_page)
        self.queue_button = tk.Button(navBar, text="Queue", command=self.open_queue_page)
        self.manual_control_button = tk.Button(navBar, text="Manual Control", command=self.open_manual_control_page)

        self.system_button.grid(row=0, column=0)
        self.labware_button.grid(row=0, column=1)
        self.methods_button.grid(row=0, column=2)
        self.queue_button.grid(row=0, column=3)
        self.manual_control_button.grid(row=0, column=4)

        home_image = PIL.Image.open("images/8port-Home.png")
        home_image = home_image.resize((400,400))
        home_image_tk = ImageTk.PhotoImage(home_image)
        image_label = tk.Label(self.homePage, image=home_image_tk)
        image_label.image = home_image_tk
        image_label.pack(side=tk.TOP)

    def open_system_page(self):
        if not self.system or not self.system.winfo_exists():
            self.system = Connect(self.coordinator)
        else:
            self.system.deiconify()

    def open_labware_page(self):
        if not self.labware or not self.labware.winfo_exists():
            self.labware = Labware(self.coordinator)
            
        else:
            self.labware.deiconify()

    def open_methods_page(self):
        if not self.methods or not self.methods.winfo_exists():
            self.methods = Method_Creator(self.coordinator)
        else:
            self.methods.deiconify()

    def open_queue_page(self):
        if not self.queue or not self.queue.winfo_exists():
            self.queue = Queue_Gui(self.coordinator)
        else:
            self.queue.deiconify()

    def open_manual_control_page(self):
        if not self.manual_control or not self.manual_control.winfo_exists():
            self.manual_control = Manual(self.coordinator)
        else:
            self.manual_control.deiconify()

if __name__ == "__main__":
    
    myHomePage = HomePage()
    myHomePage.homePage.mainloop()