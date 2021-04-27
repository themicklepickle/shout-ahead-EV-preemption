### SETUP ###
# %%
from API.Tester import Tester

tester = Tester()

base_system = "Fri_Apr_23_02:54:35_PM_2021"
EV_layered_1 = "Sun_Apr_25_02:05:54_PM_2021"
EV_layered_2 = "Sun_Apr_25_02:05:51_PM_2021"


### CONTROL ###
# %%
tester.testRules("blank", [0, 0, 1], False, 1)


### EV LAYERED #2 (FULL) ###
# %%
name = "EV_layered_2_51_average_EV_speed"
tester.addBestPoolInGeneration(51, "averageEVSpeed", EV_layered_2, name)
tester.addRuleSetToRuleSet(name, "base_system_59_average_EV_speed")
tester.testRules(name, [0, 0, 1], False, 1000, True)


### BASE SYSTEM (FULL) ###
# %%
name = "base_system_59_average_EV_speed"
tester.addBestPoolInGeneration(59, "averageEVSpeed", base_system, name)
tester.testRules(name, [0, 0, 1], False, 1000, True)


### EV LAYERED #1 (FULL) ###
# %%
name = "EV_layered_1_58_average_EV_speed"
tester.addBestPoolInGeneration(58, "averageEVSpeed", EV_layered_1, name)
tester.addRuleSetToRuleSet(name, "base_system_59_average_EV_speed")
tester.testRules(name, [0, 0, 1], False, 1000, True)


### EV LAYERED #2 (NO COOP) ###
# %%
name = "EV_layered_2_51_average_EV_speed"
tester.addBestPoolInGeneration(51, "averageEVSpeed", EV_layered_2, name)
tester.addRuleSetToRuleSet(name, "base_system_59_average_EV_speed")
tester.removeOneRuleSet(name, "RSint")
tester.testRules(name, [0, 0, 1], False, 1000, True)

### BASE SYSTEM (NO COOP) ###
# %%
name = "base_system_59_average_EV_speed"
tester.addBestPoolInGeneration(59, "averageEVSpeed", base_system, name)
tester.removeOneRuleSet(name, "RSint")
tester.testRules(name, [0, 0, 1], False, 1000, True)


### EV LAYERED #1 (NO COOP) ###
# %%
name = "EV_layered_1_58_average_EV_speed"
tester.addBestPoolInGeneration(58, "averageEVSpeed", EV_layered_1, name)
tester.addRuleSetToRuleSet(name, "base_system_59_average_EV_speed")
tester.removeOneRuleSet(name, "RSint")
tester.testRules(name, [0, 0, 1], False, 1000, True)
