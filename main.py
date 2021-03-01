from Simulation import Simulation
from Tester import Tester


Simulation().run()


tester = Tester()

tester.testRules("Thu_Feb_25_10:02:43_PM_2021", [True, False, True], gui=False)
