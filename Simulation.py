from TrafficLight import TrafficLight
from AgentPool import AgentPool
from sumolib import checkBinary  # Checks for the binary in environ vars
import os
import sys
import datetime
import timeit
import time
import pytz
import socket
import json
import traceback
from operator import attrgetter

import InitSetUp
from DriverEV import DriverEV
import EvolutionaryLearner
from Notifier import Notifier
from Status import Status
from Database import Database
from typing import List


class Simulation:
    def __init__(self) -> None:
        self.initSUMO()
        self.initOptions()

    def initSUMO(self):
        if "SUMO_HOME" in os.environ:
            tools = os.path.join(os.environ["SUMO_HOME"], "tools")
            sys.path.append(tools)
        else:
            sys.exit("Please declare environment variable 'SUMO_HOME'")

    def initOptions(self):
        with open("options.json", "r") as f:
            self.options = json.load(f)

        deviceOptions = self.options["device"]
        self.deviceName = deviceOptions["name"] if deviceOptions["name"] != "" else socket.gethostname()

        trainingOptions = self.options["training"]
        self.useShoutahead = trainingOptions["useShoutahead"]
        self.totalGenerations = trainingOptions["totalGenerations"]
        self.individualRunsPerGen = trainingOptions["individualRunsPerGen"]

        ruleSetOptions = self.options["ruleSets"]
        self.ruleSetOptions = [
            ruleSetOptions["local"],
            ruleSetOptions["cooperation"],
            ruleSetOptions["learnedLocal"],
            ruleSetOptions["learnedCooperation"]
        ]

        userDefinedRuleToggle = self.options["userDefinedRules"]
        self.maxGreenAndYellowPhaseTime_UDRule = userDefinedRuleToggle["maxGreenAndYellowPhaseTime_UDRule"]
        self.maxRedPhaseTime_UDRule = userDefinedRuleToggle["maxRedPhaseTime_UDRule"]
        self.assignGreenPhaseToSingleWaitingPhase_UDRule = userDefinedRuleToggle["assignGreenPhaseToSingleWaitingPhase_UDRule"]

        simulationOptions = self.options["simulation"]
        self.sumoNetworkName = simulationOptions["sumoNetworkName"]
        self.maxGreenPhaseTime = simulationOptions["maxGreenPhaseTime"]
        self.maxYellowPhaseTime = simulationOptions["maxYellowPhaseTime"]
        self.maxSimulationTime = simulationOptions["maxSimulationTime"]["default"]
        self.maxSimulationTime_5_15 = simulationOptions["maxSimulationTime"]["5-15"]
        self.maxSimulationTime_15 = simulationOptions["maxSimulationTime"]["15+"]

        binaryOptions = self.options["binary"]
        self.gui = binaryOptions["gui"]
        self.autoStart = binaryOptions["autoStart"]
        self.autoQuit = binaryOptions["autoQuit"]

        outputOptions = self.options["output"]
        self.displayStatus = outputOptions["displayStatus"]
        self.storeInDatabase = outputOptions["storeInDatabase"]
        self.notify = outputOptions["notify"]

    def initCmd(self):
        sumoOptions = {
            "-c": f"Traffic Flows/{self.sumoNetworkName}/config_file.sumocfg",
            "--waiting-time-memory": "5",
            "--time-to-teleport": "-1",
            "--no-step-log": "true",
            "-W": "true",
            "-S": "true" if self.autoStart else "false",
            "-Q": "true" if self.autoQuit else "false"
        }
        sumoBinary = checkBinary("sumo-gui" if self.gui else "sumo")

        self.cmd = [sumoBinary] + [element for option in sumoOptions.items() for element in option]

    def initOutput(self):
        self.status = None
        if self.displayStatus:
            self.status = Status(self.deviceName)
            self.status.initialize()
            self.status.update("total generation", self.totalGenerations)

        self.database = None
        if self.storeInDatabase:
            startTimeObj = datetime.datetime.strptime(self.simulationStartTime, "%a %b %d %I:%M:%S %p %Y")
            databaseName = startTimeObj.strftime("%a_%b_%d_%I:%M:%S_%p_%Y")

            self.database = Database(databaseName)
            self.database.setOptions(self.options)

        self.notifier = None
        if self.notify:
            with open("credentials.json", "r") as f:
                credentials = json.load(f)
            self.notifier = Notifier(credentials["email"], credentials["password"], ["michael.xu1816@gmail.com"], self.deviceName)

    def initSetUpTuple(self):
        sumoNetworkName = f"Traffic Flows/{self.sumoNetworkName}/simpleNetwork.net.xml"
        self.setUpTuple = InitSetUp.run(sumoNetworkName, self.individualRunsPerGen, self.useShoutahead, self.ruleSetOptions)
        self.getSimRunner()

    def initVariables(self):
        self.generation = 1
        self.episode = 0
        self.generationEpisode = 0
        self.allIndividualsTested = False
        self.simulationStartTime = self.getTime()
        self.generationRuntimes = []

    def initBestResults(self, trafficLights: List[TrafficLight]):
        self.bestResults = {}
        for key, value in self.results.items():
            self.bestResults[key] = {
                "value": value,
                "trafficLights": {}
            }
            for tl in trafficLights:
                self.bestResults[key]["trafficLights"][tl.getAgentPool().getID()] = tl.getAssignedIndividual().getJSON()

    def isBetter(self, newValue, oldValue, attributeName):
        if "EVStops" == attributeName:
            return newValue < oldValue
        if "averageEVSpeed" == attributeName:
            return newValue > oldValue
        if "simulationTime" == attributeName:
            return newValue < oldValue
        if "totalFitness" == attributeName:
            return newValue < oldValue

    def updateBestResults(self, trafficLights: List[TrafficLight]):
        for key, value in self.results.items():
            if self.isBetter(value, self.bestResults[key]["value"], key):
                self.bestResults[key] = {
                    "value": value,
                    "trafficLights": {}
                }
                for tl in trafficLights:
                    self.bestResults[key]["trafficLights"][tl.getAgentPool().getID()] = tl.getAssignedIndividual().getJSON()

    def displayResults(self):
        print("    Results:")
        for key, value in self.results.items():
            print(f"      {key}: {value} ({self.bestResults[key]['value']})")

    def getMaxSimulationTimes(self):
        return [
            self.maxGreenPhaseTime,
            self.maxYellowPhaseTime,
            self.maxSimulationTime
        ]

    def getUserDefinedRules(self):
        return [
            self.maxGreenAndYellowPhaseTime_UDRule,
            self.maxRedPhaseTime_UDRule,
            self.assignGreenPhaseToSingleWaitingPhase_UDRule
        ]

    def getSimRunner(self):
        return DriverEV(self.cmd, self.setUpTuple, *self.getMaxSimulationTimes(), *self.getUserDefinedRules(), self.useShoutahead, self.ruleSetOptions)

    def getTime(self):
        return datetime.datetime.now(pytz.timezone("America/Denver")).strftime("%a %b %d %I:%M:%S %p %Y")

    def newGeneration(self):
        print(f"---------- GENERATION {self.generation} of {self.totalGenerations} ----------")
        print(f"    Simulation start time: {self.simulationStartTime}")
        print(f"    Average generation runtime: {sum(self.generationRuntimes) / self.generation}\n")
        sys.stdout.flush()

        if self.storeInDatabase:
            self.database.setGeneration(self.generation)

        if self.displayStatus:
            self.status.update("generation", self.generation)

        self.genStart = self.getTime()
        self.startTime = time.time()
        self.episodeRuntimes = []
        self.allIndividualsTested = False
        self.generationEpisode = 0

        for ap in self.setUpTuple[2]:
            for i in ap.getIndividualsSet():
                i.resetSelectedCount()

    def indivRun(self):
        self.episode += 1
        self.generationEpisode += 1

        print(f"--- Episode {self.episode} of GENERATION {self.generation} of {self.totalGenerations} ---")
        print(f"    Generation start time: {self.genStart}")
        print(f"    Average generation runtime: {sum(self.generationRuntimes) / self.generation}")
        if self.episodeRuntimes:
            print(f"    Average episode runtime: {sum(self.episodeRuntimes) / len(self.episodeRuntimes)}")

        if self.displayStatus:
            self.status.update("episode", self.episode)

        # Adjust maximum simulation times for individuals based on generation count
        if self.generation >= 5 and self.generation < 15:
            self.maxSimulationTime = self.maxSimulationTime_5_15
        elif self.generation >= 15:
            self.maxSimulationTime = self.maxSimulationTime_15

        simRunner = self.getSimRunner()

        start = timeit.default_timer()
        resultingAgentPools, trafficLights = simRunner.run()
        self.results = simRunner.getResults()
        if self.generationEpisode == 1:
            self.initBestResults(trafficLights)
        else:
            self.displayResults()
            self.updateBestResults(trafficLights)

        runtime = timeit.default_timer() - start
        print(f"    Time: {round(runtime, 1)}")
        sys.stdout.flush()
        self.episodeRuntimes.append(runtime)

        needsTesting = []
        for ap in resultingAgentPools:
            for i in ap.getIndividualsSet():
                needsTesting.append(i.getSelectedCount() < self.individualRunsPerGen)

        if True not in needsTesting:
            self.allIndividualsTested = True
            for ap in resultingAgentPools:
                for i in ap.getIndividualsSet():
                    continue

        # self.allIndividualsTested = True  # Uncomment for quick testing

    def storeGeneration(self):
        genTime = self.generationRuntimes[-1]
        averageGenTime = sum(self.generationRuntimes) / len(self.generationRuntimes)
        generations = len(self.generationRuntimes)
        averageEpisodeTime = sum(self.episodeRuntimes) / len(self.episodeRuntimes)
        episodes = len(self.episodeRuntimes)

        # Create new output file and add generation runtime information
        outputData = {
            "stats": {
                "genTime": genTime,
                "averageGenTime": averageGenTime,
                "averageEpisodeTime": averageEpisodeTime,
                "generations": generations,
                "episodes": episodes,
                "bestResults": self.bestResults
            }
        }
        bestIndividuals = {}

        for ap in self.setUpTuple[2]:
            agentPoolData = [i.getJSON() for i in ap.getIndividualsSet()]
            self.database.updateAgentPool(ap.getID(), agentPoolData, "old")

            individuals = ap.getIndividualsSet()
            topIndividual = min(individuals, key=attrgetter("fitness"))

            bestIndividuals[ap.getID()] = topIndividual.getJSON()

        outputData["bestIndividuals"] = bestIndividuals

        self.database.storeOutput(outputData)

    def generationComplete(self):
        print(f"Generation {self.generation} complete!")
        print(f"    Start time: {self.genStart}")
        print(f"    End time: {self.getTime()}")

        self.generationRuntimes.append(time.time() - self.startTime)

        if self.storeInDatabase:
            self.storeGeneration()

        if self.notify:
            self.notifier.run(self.setUpTuple[2], self.generationRuntimes, self.episodeRuntimes, self.totalGenerations)

        # Normalize the fitness values of each Individual in an agent pool for breeding purposes
        for ap in self.setUpTuple[2]:
            ap.normalizeIndividualsFitnesses()

        if self.generation + 1 < self.totalGenerations:
            EvolutionaryLearner.createNewGeneration(self.setUpTuple[2], self.useShoutahead, self.ruleSetOptions, self.database)

        for ap in self.setUpTuple[2]:
            for i in ap.getIndividualsSet():
                i.resetSelectedCount()
                i.resetAggregateVehicleWaitTime()
                i.resetAverageEVSpeed()
                i.resetEVStops()

        self.generation += 1

        sys.stdout.flush()

    def run(self) -> None:
        self.initCmd()
        self.initSetUpTuple()
        self.initVariables()
        self.initOutput()

        try:
            print(f"----- Start time: {self.simulationStartTime} -----\n")

            # Evolutionary learning loop
            while self.generation <= self.totalGenerations:
                self.newGeneration()

                # Reinforcement learning loop
                while not self.allIndividualsTested:
                    self.indivRun()

                # Prepare individuals for the next run through
                self.generationComplete()

            print("LEARNING COMPLETE!")
            print(f"Simulation start time: {self.simulationStartTime}")
            sys.stdout.flush()

            if self.notify:
                self.notifier.sendEmail(f"COMPLETE!", f"All {self.totalGenerations} have been completed.")

            self.status.terminate()
        except:
            traceback.print_exc()
            if self.displayStatus:
                self.status.terminate()
