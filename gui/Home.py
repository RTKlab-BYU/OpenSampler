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
        self.homePage.title("customLC")
        
        tk.Label(self.homePage, text="customLC Home Page", font="Helvetica 24",justify=tk.LEFT).pack(side=tk.TOP)
        
        #######Nav Buttons#############
        navBar = tk.Frame(self.homePage)
        navBar.pack(side=tk.TOP)

        tk.Button(navBar, text="System",command=lambda: Connect(coordinator),justify=tk.LEFT).grid(row=0,column=0, columnspan=1)
        tk.Button(navBar, text="Labware",command=lambda: Labware(coordinator),justify=tk.LEFT).grid(row=0,column=1)
        tk.Button(navBar, text="Methods",command=lambda: Method_Creator(coordinator),justify=tk.LEFT).grid(row=0,column=2)
        tk.Button(navBar, text="Queue",command=lambda: Queue_Gui(coordinator),justify=tk.LEFT).grid(row=0,column=3)
        tk.Button(navBar, text="Manual Control",command=lambda: Manual(coordinator),justify=tk.LEFT).grid(row=0,column=4)


        home_image = PIL.Image.open("images/8port-Home.png")
        home_image = home_image.resize((400,400))
        home_image_tk = ImageTk.PhotoImage(home_image)
        image_label = tk.Label(self.homePage, image=home_image_tk)
        image_label.image = home_image_tk
        image_label.pack(side=tk.TOP)

if __name__ == "__main__":
    
    myHomePage = HomePage()
    myHomePage.homePage.mainloop()