"""
# This file controls the stoping of the system. It basically acts as storge for the hardStop and stopLoad variable.
# It can edit those variables when the buttons are pressed and they can be checked by the script reader.
#
# hardStop: it will stop a queue all together, No more loading, Gradient, or LC. this could be becuase there is a leak in the tubing. 
# stopLoad: it will stop after the current load. That sample and the previous samples will still make it to the MS for measurement. 
#
#
"""

class StopIndicator:
    def __init__(self):
        self.hardStop = False
        self.stopLoad = False
        self.paused = False

    def turn_on_hardStop(self):
        self.hardStop = True
        self.paused = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
    
    def reset(self):
        self.turn_off_stopLoad()
        self.turn_off_hardStop()




