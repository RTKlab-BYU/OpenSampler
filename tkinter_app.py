from gui.Home import HomePage
from Classes.coordinator import Coordinator

myCoordinator = Coordinator()

myHomePage = HomePage(myCoordinator)
myHomePage.homePage.mainloop() 