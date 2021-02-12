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


def main(status: Status, database: Database):
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
    runTimeSet = []
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
    status.initialize()
    status.update("total generations", totalGenerations)

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
        }
    })

    with open("credentials.json", "r") as f:
        credentials = json.load(f)
    notifier = Notifier(email=credentials["email"], password=credentials["password"], recipients=["michael.xu1816@gmail.com"])
    # -------------------------

    print(f"----- Start time: {getTime()} -----\n")
    setUpTuple = InitSetUp.run(sumoNetworkName, individualRunsPerGen)
    simRunner = DriverEV(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                         maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule, useShoutahead)
    generations = 1
    episode = 0
    allIndividualsTested = False
    simulationStartTime = getTime()
    generationRuntimes = []

    # Evolutionary learning loop
    while generations <= totalGenerations:
        database.setGeneration(generations)
        # Output management
        print(f"---------- GENERATION {generations} of {totalGenerations} ----------")
        print(f"This simulation began at: {simulationStartTime}")
        print(f"The average generation runtime is {sum(generationRuntimes)/generations}\n")
        genStart = getTime()
        startTime = time.time()
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
                maxSimulationTime = 6000
            elif generations >= 15:
                maxSimulationTime = 4000

            simRunner = DriverEV(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                                 maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule, useShoutahead)

            # Output management
            print(f"----- Episode {episode+1} of GENERATION {generations} of {totalGenerations} -----")
            print(f"Generation start time: {genStart}")
            print(f"The average generation runtime is {sum(generationRuntimes) / generations}")
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
            # allIndividualsTested = True # Uncomment for quick testing

        # Prepare individuals for the next run through
        for ap in setUpTuple[2]:
            ap.normalizeIndividualsFitnesses()  # Normalize the fitness values of each Individual in an agent pool for breeding purposes

        if generations + 1 < totalGenerations:
            EvolutionaryLearner.createNewGeneration(setUpTuple[2], database, useShoutahead)  # Update agent pools with a new generation of individuals
            for ap in setUpTuple[2]:
                for i in ap.getIndividualsSet():
                    i.resetSelectedCount()
                    i.resetAggregateVehicleWaitTime()
                    i.resetMeanEVSpeed()
                    i.resetEVStops()
            sys.stdout.flush()
        else:
            OutputManager.run(setUpTuple[2], sum(generationRuntimes)/50, (sum(generationRuntimes)/50)*50, database)
            print("Output file created.")

        print(f"Generation start time: {genStart} ----- End time: {getTime()}")
        generationRuntimes.append(time.time() - startTime)

        OutputManager.run(setUpTuple[2], sum(generationRuntimes)/50, (sum(generationRuntimes)/50)*50, database)
        notifier.run(setUpTuple[2], sum(generationRuntimes)/50, (sum(generationRuntimes)/50)*50, generations, totalGenerations)

        generations += 1

        sys.stdout.flush()

    print(f"Generation start time: {simulationStartTime} ----- End time: {getTime()}")
    print(f"This simulation began at: {simulationStartTime}")
    notifier.sendEmail(f"COMPLETE!", f"All {totalGenerations} have been completed.")
    sys.stdout.flush()


if __name__ == "__main__":
    status = Status(socket.gethostname())
    database = Database(datetime.datetime.now(pytz.timezone('America/Denver')).strftime('%a_%b_%d_%I:%M:%S_%p_%Y'))
    try:
        main(status, database)
        # cProfile.run("main()", sort="cumtime")
    except:
        status.terminate()
        print("end")
