import os
import sys
import InitSetUp
import OutputManager

import datetime
import timeit
import time

from DriverEV import DriverEV
import EvolutionaryLearner

from Notifier import Notifier

from Logger import Logger

# Importing needed python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


from sumolib import checkBinary  # Checks for the binary in environ vars
import traci

if __name__ == "__main__":
    with open("email login.txt", "r") as f:
        emailLogin = [line.strip() for line in f.readlines()]
    notifier = Notifier(
        email=emailLogin[0],
        password=emailLogin[1],
        recipients=[
            "michael.xu1816@gmail.com"
        ]
    )

    sys.stdout = Logger()

    # for _ in range(10):
    # --- TRAINING OPTIONS ---
    gui = False
    totalGenerations = 50
    # Min number of training runs an individual gets per generation
    individualRunsPerGen = 3
    # ----------------------

    # --- USER-DEFINED RULES TOGGLE ---
    maxGreenAndYellowPhaseTime_UDRule = True
    maxRedPhaseTime_UDRule = False
    assignGreenPhaseToSingleWaitingPhase_UDRule = True
    # ----------------------

    # Attributes of the simulation
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

    print("----- Start time:", datetime.datetime.now())
    setUpTuple = InitSetUp.run(sumoNetworkName, individualRunsPerGen)
    simRunner = DriverEV(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                         maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule)
    generations = 1
    episode = 0
    allIndividualsTested = False
    simulationStartTime = datetime.datetime.now()
    generationRuntimes = []

    # Evolutionary learning loop
    while generations <= totalGenerations:
        print('----- GENERATION {} of {}'.format(generations, totalGenerations))
        print("This simulation began at:", simulationStartTime)
        print("The average generation runtime is", sum(generationRuntimes)/generations)
        sys.stdout.flush()
        genStart = datetime.datetime.now()
        startTime = time.time()

        # Prepare for next simulation run
        allIndividualsTested = False
        for ap in setUpTuple[2]:
            for i in ap.getIndividualsSet():
                i.resetSelectedCount()
                # print("Generation includes Individual:", i.getID())

        # Reinforcement learning loop
        while not allIndividualsTested:
            # Adjust maximum simulation times for individuals based on generation count
            if generations >= 5 and generations < 15:
                maxSimulationTime = 6000
            elif generations >= 15:
                maxSimulationTime = 4000

            simRunner = DriverEV(sumoCmd, setUpTuple, maxGreenPhaseTime, maxYellowPhaseTime, maxSimulationTime,
                                 maxGreenAndYellowPhaseTime_UDRule, maxRedPhaseTime_UDRule, assignGreenPhaseToSingleWaitingPhase_UDRule)

            print('----- Episode {}'.format(episode+1),
                  "of GENERATION {} of {}".format(generations, totalGenerations))
            print("Generation start time:", genStart)
            print("The average generation runtime is",
                  sum(generationRuntimes)/generations)
            start = timeit.default_timer()
            resultingAgentPools = simRunner.run()  # run the simulation
            stop = timeit.default_timer()
            print('Time: ', round(stop - start, 1))
            episode += 1
            sys.stdout.flush()

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
            # Normalize the fitness values of each Individual in an agent pool for breeding purposes
            ap.normalizeIndividualsFitnesses()

        if generations + 1 < totalGenerations:
            # Update agent pools with a new generation of individuals
            EvolutionaryLearner.createNewGeneration(setUpTuple[2])
            for ap in setUpTuple[2]:
                for i in ap.getIndividualsSet():
                    i.resetSelectedCount()
                    i.resetAggregateVehicleWaitTime()
                    i.resetMeanEVSpeed()
                    i.resetEVStops()
            sys.stdout.flush()
        else:
            OutputManager.run(setUpTuple[2], sum(generationRuntimes)/50, (sum(generationRuntimes)/50)*50)
            print("Output file created.")

        print("Generation start time:", genStart,
              "----- End time:", datetime.datetime.now())
        generationRuntimes.append(time.time() - startTime)
        generations += 1
        notifier.sendEmail(f"Gen {generations} of {totalGenerations} complete!", f"Start: {genStart}\nEnd: {datetime.datetime.now()}")
        sys.stdout.flush()

    print("Start time:", simulationStartTime,
          "----- End time:", datetime.datetime.now())
    print("This simulation began at:", simulationStartTime)
    notifier.sendEmail(f"COMPLETE!", f"All {totalGenerations} have been completed.")
    sys.stdout.flush()

    # Do something to save session stats here
