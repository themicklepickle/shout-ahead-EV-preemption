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


def main():
    # --- TRAINING OPTIONS ---
    gui = False
    useShoutahead = True
    useEVCoopPredicates = True
    totalGenerations = 50
    individualRunsPerGen = 3  # Min number of training runs an individual gets per generation
    # ------------------------

    # --- USER-DEFINED RULES TOGGLE ---
    maxGreenAndYellowPhaseTime_UDRule = True
    maxRedPhaseTime_UDRule = True
    assignGreenPhaseToSingleWaitingPhase_UDRule = True
    # ----------------------------------

    # --- SIMULATION ATTRIBUTES ---
    folderName = "EV Traffic Flow 225"
    sumoNetworkName = f"{folderName}/simpleNetwork.net.xml"
    maxGreenPhaseTime = 225
    maxYellowPhaseTime = 5
    maxSimulationTime = 7000
    # -----------------------------

    # --- TESTING OPTIONS ---
    ruleSetFolder = "Sat_Feb_13_12:34:59_AM_2021"

    # --- SUMO BINARY SETUP ---
    if gui == False:
        sumoBinary = checkBinary('sumo')
        sumoCmd = [sumoBinary, "-c", f"{folderName}/config_file.sumocfg", "--waiting-time-memory", "5", "--time-to-teleport", "-1"]
    else:
        sumoBinary = checkBinary('sumo-gui')
        sumoCmd = [sumoBinary, "-c", f"{folderName}/config_file.sumocfg", "--waiting-time-memory", "5", "--time-to-teleport", "-1", "-Q", "true", "-S", "true"]  #

    # # load rule
    # setUpTuple = InitSetUp.run(sumoNetworkName, individualRunsPerGen, useShoutahead, useEVCoopPredicates)
    # ConfigTesting.run(setUpTuple[2], ruleSetFolder)

    # # run simulation
    # simRunner = DriverTest(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
    #                        maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule, useShoutahead)
    # simRunner.runTest()

    # results = simRunner.getResults()
    # results.pop("averageEVSpeedsList")
    # for key, val in results.items():
    #     print(f"{key}: {val}")

    generations = []

    for i in range(1, 48):
        # load rule
        ConfigTesting.addBestIndividualsInGeneration(i)
        setUpTuple = InitSetUp.run(sumoNetworkName, individualRunsPerGen, useShoutahead, useEVCoopPredicates)
        ConfigTesting.run(setUpTuple[2], ruleSetFolder)

        # run simulation
        simRunner = DriverTest(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                               maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule, useShoutahead)
        simRunner.runTest()
        results = simRunner.getResults()
        results.pop("averageEVSpeedsList")
        results["generation"] = i

        generations.append(results)

        print("generation", i)
        for key, val in results.items():
            print(f"{key}: {val}")

    with open(f"results/hi.json", "w") as f:
        json.dump(generations, f)

    generations.sort(key=lambda x: x["simulationTime"])
    print("best simulationTime", generations[0]["generation"])

    generations.sort(key=lambda x: x["averageEVSpeed"], reverse=True)
    print("best averageEVSpeed", generations[0]["generation"])

    generations.sort(key=lambda x: x["EVStops"])
    print("best EVstops", generations[0]["generation"])


if __name__ == "__main__":
    # --- OUTPUT OPTIONS ---
    # storeInDatabase = True
    # ----------------------

    # database = Database(datetime.datetime.now(pytz.timezone('America/Denver')).strftime('%a_%b_%d_%I:%M:%S_%p_%Y')) if storeInDatabase else None

    try:
        main()
        # cProfile.run("main(status, database, notifier)", sort="cumtime")
    except:
        traceback.print_exc()
