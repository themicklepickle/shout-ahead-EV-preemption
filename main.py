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

import InitSetUp
import OutputManager
from DriverEV import DriverEV
import EvolutionaryLearner
from Notifier import Notifier
from Status import Status
from Database import Database

# Importing needed python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")


from sumolib import checkBinary  # Checks for the binary in environ vars


def getTime():
    return datetime.datetime.now(pytz.timezone('America/Denver')).strftime('%a %b %d %I:%M:%S %p %Y')


def main(status: Status, database: Database, notifier: Notifier):
    # --- TRAINING OPTIONS ---
    gui = False
    totalGenerations = 50
    individualRunsPerGen = 3  # Min number of training runs an individual gets per generation
    # ------------------------

    # --- USER-DEFINED RULES TOGGLE ---
    maxGreenAndYellowPhaseTime_UDRule = False
    maxRedPhaseTime_UDRule = False
    assignGreenPhaseToSingleWaitingPhase_UDRule = False
    # ----------------------------------

    # --- SIMULATION ATTRIBUTES ---
    folderName = "EV Traffic Flow 300"
    useShoutahead = True
    sumoNetworkName = f"{folderName}/simpleNetwork.net.xml"
    maxGreenPhaseTime = 225
    maxYellowPhaseTime = 5
    maxSimulationTime = 10000
    maxSimulationTime_5_15 = 6000
    maxSimulationTime_15 = 4000
    # -----------------------------

    # --- SUMO BINARY SETUP ---
    if gui == False:
        sumoBinary = checkBinary('sumo')
        sumoCmd = [sumoBinary, "-c", f"{folderName}/config_file.sumocfg", "--waiting-time-memory", "5", "--time-to-teleport", "-1"]
    else:
        sumoBinary = checkBinary('sumo-gui')
        sumoCmd = [sumoBinary, "-c", f"{folderName}/config_file.sumocfg", "--waiting-time-memory", "5", "--time-to-teleport", "-1", "-Q", "true", "-S", "true"]
    # -------------------------

    # --- OUTPUT MANAGEMENT ---
    if status:
        status.initialize()
        status.update("total generations", totalGenerations)
    if database:
        database.setOptions({
            "deviceName": socket.gethostname(),
            "trainingOptions": {
                "gui": gui,
                "totalGenerations": totalGenerations,
                "individualRunsPerGen": individualRunsPerGen,
            },
            "userDefinedRulesToggle": {
                "maxGreenAndYellowPhaseTime_UDRule": maxGreenAndYellowPhaseTime_UDRule,
                "maxRedPhaseTime_UDRule": maxRedPhaseTime_UDRule,
                "assignGreenPhaseToSingleWaitingPhase_UDRule": assignGreenPhaseToSingleWaitingPhase_UDRule,

            },
            "simulationAttributes": {
                "useShoutahead": useShoutahead,
                "sumoNetworkName": sumoNetworkName,
                "maxGreenPhaseTime": maxGreenPhaseTime,
                "maxYellowPhaseTime": maxYellowPhaseTime,
                "maxSimulationTime": maxSimulationTime,
                "maxSimulationTime_5_15": maxSimulationTime_5_15,
                "maxSimulationTime_15": maxSimulationTime_15,
            },
            "output": {
                "displayStatus": bool(status),
                "storeInDatabase": bool(database),
                "notify": bool(notifier)
            }
        })

    # -------------------------

    print(f"----- Start time: {getTime()} -----\n")
    setUpTuple = InitSetUp.run(sumoNetworkName, individualRunsPerGen, useShoutahead)
    simRunner = DriverEV(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                         maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule, useShoutahead)
    generations = 1
    episode = 0
    allIndividualsTested = False
    simulationStartTime = getTime()
    generationRuntimes = []

    # Evolutionary learning loop
    while generations <= totalGenerations:
        if database:
            database.setGeneration(generations)
        # Output management
        print(f"---------- GENERATION {generations} of {totalGenerations} ----------")
        print(f"This simulation began at: {simulationStartTime}")
        print(f"The average generation runtime is {sum(generationRuntimes)/generations}\n")
        genStart = getTime()
        startTime = time.time()
        if status:
            status.update("generation", generations)
        sys.stdout.flush()

        # Prepare for next simulation run
        allIndividualsTested = False
        for ap in setUpTuple[2]:
            for i in ap.getIndividualsSet():
                i.resetSelectedCount()

        # Reinforcement learning loop
        while not allIndividualsTested:
            # Adjust maximum simulation times for individuals based on generation count
            if generations >= 5 and generations < 15:
                maxSimulationTime = maxSimulationTime_5_15
            elif generations >= 15:
                maxSimulationTime = maxSimulationTime_15

            simRunner = DriverEV(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                                 maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule, useShoutahead)

            # Output management
            print(f"----- Episode {episode+1} of GENERATION {generations} of {totalGenerations} -----")
            print(f"Generation start time: {genStart}")
            print(f"The average generation runtime is {sum(generationRuntimes) / generations}")
            if status:
                status.update("episode", episode+1)
            start = timeit.default_timer()
            resultingAgentPools = simRunner.run()  # run the simulation
            stop = timeit.default_timer()
            print(f"Time: {round(stop - start, 1)}")
            sys.stdout.flush()

            episode += 1

            needsTesting = []
            for ap in resultingAgentPools:
                for i in ap.getIndividualsSet():
                    if i.getSelectedCount() < individualRunsPerGen:
                        needsTesting.append(True)
                    else:
                        needsTesting.append(False)

            if True not in needsTesting:
                allIndividualsTested = True
                for ap in resultingAgentPools:
                    for i in ap.getIndividualsSet():
                        continue
            # allIndividualsTested = True  # Uncomment for quick testing

        # Prepare individuals for the next run through
        for ap in setUpTuple[2]:
            ap.normalizeIndividualsFitnesses()  # Normalize the fitness values of each Individual in an agent pool for breeding purposes

        if generations + 1 < totalGenerations:
            EvolutionaryLearner.createNewGeneration(setUpTuple[2], useShoutahead, database)  # Update agent pools with a new generation of individuals
            for ap in setUpTuple[2]:
                for i in ap.getIndividualsSet():
                    i.resetSelectedCount()
                    i.resetAggregateVehicleWaitTime()
                    i.resetAverageEVSpeed()
                    i.resetEVStops()
            sys.stdout.flush()
        elif database:
            OutputManager.run(setUpTuple[2], sum(generationRuntimes)/50, (sum(generationRuntimes)/50)*50, database)
            print("Output file created.")

        print(f"Generation start time: {genStart} ----- End time: {getTime()}")
        generationRuntimes.append(time.time() - startTime)

        if database:
            OutputManager.run(setUpTuple[2], sum(generationRuntimes)/50, (sum(generationRuntimes)/50)*50, database)
        if notifier:
            notifier.run(setUpTuple[2], sum(generationRuntimes)/50, (sum(generationRuntimes)/50)*50, generations, totalGenerations)

        generations += 1

        sys.stdout.flush()

    print(f"Generation start time: {simulationStartTime} ----- End time: {getTime()}")
    print(f"This simulation began at: {simulationStartTime}")
    if notifier:
        notifier.sendEmail(f"COMPLETE!", f"All {totalGenerations} have been completed.")
    sys.stdout.flush()


if __name__ == "__main__":
    # --- OUTPUT OPTIONS ---
    displayStatus = True
    storeInDatabase = True
    notify = True
    # ----------------------

    status = Status(socket.gethostname()) if displayStatus else None
    database = Database(datetime.datetime.now(pytz.timezone('America/Denver')).strftime('%a_%b_%d_%I:%M:%S_%p_%Y')) if storeInDatabase else None
    with open("credentials.json", "r") as f:
        credentials = json.load(f)
    notifier = Notifier(email=credentials["email"], password=credentials["password"], recipients=["michael.xu1816@gmail.com"]) if notify else None

    try:
        main(status, database, notifier)
        # cProfile.run("main(status, database, notifier)", sort="cumtime")
    except:
        traceback.print_exc()
        if displayStatus:
            status.terminate()
