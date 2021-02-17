import os
import sys
import InitSetUp 
import OutputManager

import datetime
import timeit
import time

from Driver import Driver
import EvolutionaryLearner


# Importing needed python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


from sumolib import checkBinary  # Checks for the binary in environ vars
import traci

if __name__ == "__main__":
    print("Working...")
    # --- TRAINING OPTIONS ---
    gui = False
    totalGenerations = 20
    individualRunsPerGen = 1  # Min number of training runs an individual gets per generation
    # ----------------------
    
    # --- USER-DEFINED RULES TOGGLE ---
    maxGreenAndYellowPhaseTime_UDRule = True
    maxRedPhaseTime_UDRule = False
    assignGreenPhaseToSingleWaitingPhase_UDRule = True
    # ----------------------

    # Attributes of the simulation
    numOfConfigFiles = 10
    resultsSuffixOptions = ["UDLearned", "NoUD", "UDAfter"]
    resultsSuffix = resultsSuffixOptions[0]                 # Used to run multiple instances and create different files
    sumoNetworkName = "simpleNetwork.net.xml"
    maxGreenPhaseTime = 225
    maxYellowPhaseTime = 5
    maxSimulationTime = 10000
    runTimeSet = []


    # setting the cmd mode or the visual mode
    if gui == False:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # initializations
    #sumoCmd = [sumoBinary, "-c", "intersection/tlcs_config_train.sumocfg", "--no-step-log", "true", "--waiting-time-memory", str(max_steps)]
    sumoCmd = [sumoBinary, "-c", "config_file.sumocfg", "--waiting-time-memory", "5", "--time-to-teleport", "-1"]
    generationRuntimes = []
    generations = 1
    resultsFileName = "TestResults_" + resultsSuffix + ".txt"
    f = open(resultsFileName, "w")
    f.close()
    i = 0

for i in range(numOfConfigFiles):
    if numOfConfigFiles == 1:
        configFile = "config_file.sumocfg"
    else:
        configFile = "config_file_" + str(i+1) + ".sumocfg"

    while generations <= totalGenerations:
        print("----- Start time:", datetime.datetime.now())
        setUpTuple = InitSetUp.run(sumoNetworkName, individualRunsPerGen)
        genStart = datetime.datetime.now()

        for tl in setUpTuple[1]:
            tl.setMaxRedPhaseTime(maxGreenPhaseTime, maxYellowPhaseTime)
            tl.initPhaseTimeSpentInRedArray()

        simulationStartTime = datetime.datetime.now()

        # Evolutionary learning loop 
        print("This simulation began at:", simulationStartTime)
        genStart = datetime.datetime.now()
        startTime = time.time()
        
        sumoCmd = [sumoBinary, "-c", configFile, "--waiting-time-memory", "5", "--time-to-teleport", "-1"]
        simRunner = Driver(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime, maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule)

        print("Generation start time:", genStart)
        print("Gener")
        start = timeit.default_timer()
        simRuntime = simRunner.run()  # run the simulation
        stop = timeit.default_timer()
        print('Time: ', round(stop - start, 1))

        sys.stdout.flush()               

        print("Start time:", simulationStartTime, "----- End time:", datetime.datetime.now())
        print("This simulation began at:", simulationStartTime)
        generationRuntimes.append(simRuntime)
        if generations <= totalGenerations:    
            generations += 1
        
    # Do something to save session stats here        
    f = open(resultsFileName, "a")
    f.write("Altered Flow " + str(i+1) + ": " + str(sum(generationRuntimes)/totalGenerations) + "s\n")
    f.close()

    generations = 0
    generationRuntimes = []
    print(generationRuntimes)
    print("Average simulation time of", configFile, "is", sum(generationRuntimes)/totalGenerations)

