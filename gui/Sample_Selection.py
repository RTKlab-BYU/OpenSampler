import tkinter as tk


class Sample_Selector(tk.Toplevel,):
    def __init__(self, coordinator):
        tk.Toplevel.__init__(self)    
      
        self.title("Choose Sample")
        self.geometry("750x750")
        