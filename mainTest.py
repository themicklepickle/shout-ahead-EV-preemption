import os
import sys
from pathlib import Path
import datetime
import timeit
import time
import pytz
import socket
import cProfile
import json
import traceback
import traci
import csv

import InitSetUp
import OutputManager
from DriverTest import DriverTest
import EvolutionaryLearner
from Database import Database
import ConfigTesting

# Importing needed python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")


from sumolib import checkBinary  # Checks for the binary in environ vars


def getTime():
    return datetime.datetime.now(pytz.timezone('America/Denver')).strftime('%a %b %d %I:%M:%S %p %Y')


def main(mode: str, ruleSetFolder: str, UDRulesTuple, gui: bool):
    print("\n")
    print(ruleSetFolder)
    # --- TRAINING OPTIONS ---
    useShoutahead = True
    useEVCoopPredicates = True
    totalGenerations = 50
    individualRunsPerGen = 3  # Min number of training runs an individual gets per generation
    # ------------------------

    # --- USER-DEFINED RULES TOGGLE ---
    maxGreenAndYellowPhaseTime_UDRule = UDRulesTuple[0]
    maxRedPhaseTime_UDRule = UDRulesTuple[1]
    assignGreenPhaseToSingleWaitingPhase_UDRule = UDRulesTuple[2]
    # ----------------------------------

    # --- SIMULATION ATTRIBUTES ---
    folderName = "EV Traffic Flow 75"
    sumoNetworkName = f"{folderName}/simpleNetwork.net.xml"
    maxGreenPhaseTime = 225
    maxYellowPhaseTime = 5
    maxSimulationTime = 2000
    # -----------------------------

    # --- SUMO BINARY SETUP ---
    autoStart = False
    autoQuit = True
    if gui == False:
        sumoBinary = checkBinary('sumo')
        sumoCmd = [sumoBinary, "-c", f"{folderName}/config_file.sumocfg", "--waiting-time-memory", "5", "--time-to-teleport", "-1", "--no-step-log", "true", "-W", "true"]
    else:
        sumoBinary = checkBinary('sumo-gui')
        sumoCmd = [sumoBinary, "-c", f"{folderName}/config_file.sumocfg", "--waiting-time-memory", "5", "--time-to-teleport", "-1", "--no-step-log", "true", "-W", "true"]
        if autoStart:
            sumoCmd += ["-S", "true"]
        if autoQuit:
            sumoCmd += ["-Q", "true"]
    # -------------------------

    if mode == "singleGen":
        # load rule
        setUpTuple = InitSetUp.run(sumoNetworkName, individualRunsPerGen, useShoutahead, useEVCoopPredicates)
        ConfigTesting.run(setUpTuple[2], ruleSetFolder)

        # run simulation
        simRunner = DriverTest(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                               maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule, useShoutahead, useEVCoopPredicates)
        simRunner.runTest()
        # simRunner.runATL()

        results = simRunner.getResults()
        results.pop("averageEVSpeedsList")
        for key, val in results.items():
            print(f"{key}: {val}")

    elif mode == "findBestGen":

        generations = []

        for i in range(50, 0, -1):
            # load rule
            ConfigTesting.addBestIndividualsInGeneration(ruleSetFolder, ruleSetFolder, i)
            setUpTuple = InitSetUp.run(sumoNetworkName, individualRunsPerGen, useShoutahead, useEVCoopPredicates)
            ConfigTesting.run(setUpTuple[2], ruleSetFolder)

            # run simulation
            simRunner = DriverTest(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                                   maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule, useShoutahead, useEVCoopPredicates)
            simRunner.runTest()
            results = simRunner.getResults()
            results.pop("averageEVSpeedsList")
            results["generation"] = i

            generations.append(results)

            print("generation", i)
            for key, val in results.items():
                if key != "generation":
                    print(f"  {key}: {val}")
            print('\n')

        with open(f"results/feb28.json", "w") as f:
            json.dump(generations, f)

        generations.sort(key=lambda x: x["simulationTime"])
        print("best simulationTime:", generations[0]["simulationTime"], f'({generations[0]["generation"]})')

        generations.sort(key=lambda x: x["averageEVSpeed"], reverse=True)
        print("best averageEVSpeed:", generations[0]["averageEVSpeed"], f'({generations[0]["generation"]})')

        generations.sort(key=lambda x: x["EVStops"])
        print("best EVstops:", generations[0]["EVStops"], f'({generations[0]["generation"]})')


if __name__ == "__main__":
    print("\n\n", "—"*100, "\n")
    print("1, 0, 1")
    main(mode="findBestGen", ruleSetFolder="Thu_Feb_25_10:02:43_PM_2021", UDRulesTuple=[True, False, True], gui=False)

    print("\n\n", "—"*100, "\n")
    print("1, 0, 0")
    main(mode="findBestGen", ruleSetFolder="Thu_Feb_25_10:02:43_PM_2021", UDRulesTuple=[True, False, False], gui=False)

    print("\n\n", "—"*100, "\n")
    print("0, 0, 1")
    main(mode="findBestGen", ruleSetFolder="Thu_Feb_25_10:02:43_PM_2021", UDRulesTuple=[False, False, True], gui=False)

    print("\n\n", "—"*100, "\n")
    print("0, 0, 0")
    main(mode="findBestGen", ruleSetFolder="Thu_Feb_25_10:02:43_PM_2021", UDRulesTuple=[False, False, False], gui=False)

    print("\n\n", "—"*100, "\n")
    print("1, 0, 1 (blank)")
    main(mode="singleGen", ruleSetFolder="blank", UDRulesTuple=[True, False, True], gui=False)

    print("\n\n", "—"*100, "\n")
    print("1, 0, 0 (blank)")
    main(mode="singleGen", ruleSetFolder="blank", UDRulesTuple=[True, False, False], gui=False)

    print("\n\n", "—"*100, "\n")
    print("0, 0, 1 (blank)")
    main(mode="singleGen", ruleSetFolder="blank", UDRulesTuple=[False, False, True], gui=False)

    print("\n\n", "—"*100, "\n")
    print("0, 0, 0 (blank)")
    main(mode="singleGen", ruleSetFolder="blank", UDRulesTuple=[False, False, False], gui=False)
    # main(mode="singleGen", ruleSetFolder="Feb27_50", UDRulesTuple=[False, False, False], gui=True)
    # main(mode="singleGen", ruleSetFolder="Feb25_30", UDRulesTuple=[True, False, True], gui=False)
    # main(mode="singleGen", ruleSetFolder="Feb25_20", UDRulesTuple=[True, False, True], gui=False)
    # main(mode="singleGen", ruleSetFolder="Feb25_49", UDRulesTuple=[True, False, True], gui=False)
    # main(mode="singleGen", ruleSetFolder="Sat_Feb_13_12:34:59_AM_2021", UDRulesTuple=[True, False, True], gui=False)
    # main(mode="singleGen", ruleSetFolder="noEV", UDRulesTuple=[False, False, False], gui=False)
    # main(mode="singleGen", ruleSetFolder="blank", UDRulesTuple=[False, False, False], gui=False)
    # main(mode="findBestGen", ruleSetFolder="Mon_Feb_22_11:10:10_PM_2021", UDRulesTuple=[False, False, False], gui=False)
