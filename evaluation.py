from Tester import Tester

tester = Tester()

#tester.testRules("blank", [True, False, True], False, 10)

#print(1, 0, 1)
#tester.testRules("Feb25_49", [True, False, True], False, 10)

# # controls
tester.testRules("noEV", [True, False, True], False, 10)
#tester.testRules("blank", [False, False, False], False, 10)
print("—"*80)

# # tester.findBestIndivs("Sun_Feb_28_11:44:26_PM_2021", "old agent pool")
# # tester.findBestGeneration([False, False, True], False, "Sun_Feb_28_11:44:26_PM_2021", "RSev_int+RSev+UD3")

# # tester.JSONToCSV("RSev_int+RSev+UD1")

# # tester.getTopFitnessesPerGeneration("Sun_Feb_28_11:44:26_PM_2021", "yo")

# tester.findBestGeneration([True, False, True], False, "Thu_Feb_25_10:02:43_PM_2021", "yikes")
