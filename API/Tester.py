from __future__ import annotations

import os
import json
import csv
from bson.objectid import ObjectId
import pymongo
from pathlib import Path

from API.Simulation import Simulation
from shout_ahead.Individual import Individual
from shout_ahead.Rule import Rule
from predicate_sets import PredicateSet
from predicate_sets import CoopPredicateSet
from predicate_sets import EVPredicateSet
from predicate_sets import EVCoopPredicateSet
from drivers.DriverTest import DriverTest

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from shout_ahead.AgentPool import AgentPool
    from typing import Literal


class Tester(Simulation):
    def initClient(self):
        username = os.environ["MONGODB_USERNAME"]
        password = os.environ["MONGODB_PASSWORD"]
        cluster = os.environ["MONGODB_CLUSTER"]

        self.client = pymongo.MongoClient(f"mongodb+srv://{username}:{password}@{cluster}.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
        self.db = self.client[self.databaseName]

    def getTestSimRunner(self):
        return DriverTest(self.cmd, self.setUpTuple, *self.getMaxSimulationTimes(), *self.getUserDefinedRules(), self.useShoutahead, self.ruleSetOptions)

    def initTestIndividual(self, agentPool: AgentPool):
        with open(f"rules/{self.ruleSetFolder}/{agentPool.getID()}.json", "r") as f:
            data = json.load(f)

        ruleSets = {}
        for ruleSet in data:
            rules = []
            for r in data[ruleSet]:
                rules.append(Rule(r["type"], r["conditions"], r["action"], agentPool))
            ruleSets[ruleSet] = rules

        agentPool.testIndividual = Individual("Test", agentPool, ruleSets["RS"], ruleSets["RSint"])

        agentPool.RSPredicates = PredicateSet.getPredicateSet()
        agentPool.RSintPredicates = CoopPredicateSet.getPredicateSet(agentPool)
        agentPool.RSevPredicates = EVPredicateSet.getPredicateSet()
        agentPool.RSev_intPredicates = EVCoopPredicateSet.getPredicateSet(agentPool)
        agentPool.EVLanePredicates = EVPredicateSet.getAgentSpecificPredicates(agentPool)

    def config(self):
        for ap in self.setUpTuple[2]:
            self.initTestIndividual(ap)

    def testRules(self, name: str, ruleSetFolder: str, UDRulesTuple, gui: bool, iterations: int,  saveResults: bool = True, docID=None):
        # override options
        self.maxGreenAndYellowPhaseTime_UDRule = UDRulesTuple[0]
        self.maxRedPhaseTime_UDRule = UDRulesTuple[1]
        self.assignGreenPhaseToSingleWaitingPhase_UDRule = UDRulesTuple[2]
        self.gui = gui
        self.ruleSetFolder = ruleSetFolder

        self.databaseName = "evaluation"
        self.initClient()
        self.initCmd()
        self.initSetUpTuple()
        self.config()

        if saveResults:
            docID = docID or self.db["test results"].insert_one({
                "name": name,
                "ruleSetFolder": ruleSetFolder,
                "time": self.getTime(),
                "iterations": iterations,
                "results": []
            }).inserted_id

        results = []
        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}")

            simRunner = self.getTestSimRunner()
            simRunner.runTest()

            res = simRunner.getResults()
            results.append(res)

            if saveResults:
                self.db["test results"].update_one({"_id": docID}, {"$set": {"results": results}})

        print("\n")
        print(ruleSetFolder, UDRulesTuple, gui)

        for key in results[0]:
            print(f"{key}: {[res[key] for res in results]}")
            print(f"average {key}: {sum(res[key] for res in results) / len(results)}")
            print()

    def findBestGeneration(self, UDRulesTuple, gui: bool, databaseName: str, outputFile: str):
        # override options
        self.maxGreenAndYellowPhaseTime_UDRule = UDRulesTuple[0]
        self.maxRedPhaseTime_UDRule = UDRulesTuple[1]
        self.assignGreenPhaseToSingleWaitingPhase_UDRule = UDRulesTuple[2]
        self.gui = gui
        self.databaseName = databaseName
        self.ruleSetFolder = databaseName

        self.initClient()
        self.initCmd()

        generations = []

        for i in range(50, 0, -1):
            self.addBestPoolInGeneration(i, "averageEVSpeed")
            self.initSetUpTuple()
            self.config()

            simRunner = self.getTestSimRunner()
            simRunner.runTest()

            results = simRunner.getResults()
            results["generation"] = i
            generations.append(results)

            print("generation", i)
            for key, val in results.items():
                if key == "generation":
                    continue
                print(f"  {key}: {val}")
            print('\n')

        with open(f"results/{outputFile}.json", "w") as f:
            json.dump(generations, f)

        reverseList = ["averageEVSpeed"]
        for key in generations[0]:
            if key == "generation":
                continue
            generations.sort(key=lambda x: x[key], reverse=key in reverseList)
            print(f"best {key}: {generations[0][key]} (gen {generations[0]['generation']})")

    def addRule(self, apID, ruleSet, rule, folder):
        filepath = f"rules/{folder}/{apID}.json"

        # get existing dict
        if not Path(filepath).is_file():
            Path(f"rules/{folder}").mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump({
                    "RS": [],
                    "RSint": [],
                    "RSev": [],
                    'RSev_int': []
                }, f, indent=2)
        with open(filepath, "r") as f:
            data = json.load(f)

        # remove useless parameters
        rule.pop("agentPool")
        rule.pop("timesSelected")
        rule.pop("normalizedWeight")
        rule.pop("doNothingAction")

        # add rule to existing dict if it doesn't already exist
        valid = True
        for existingRule in data[ruleSet]:
            if set(existingRule["conditions"]) == set(rule["conditions"]):
                if rule["weight"] > existingRule["weight"]:
                    data[ruleSet].remove(existingRule)
                else:
                    valid = False
        if valid and "customPredicate" not in rule["conditions"]:
            data[ruleSet].append(rule)

        # save dict
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def addBestIndividualsInGeneration(self, generation,  databaseName=None, ruleSetFolder=None):
        if databaseName:
            self.databaseName = databaseName
            self.ruleSetFolder = ruleSetFolder
            self.initClient()
        collection = self.db[str(generation)]

        for apID in ["AP" + str(i) for i in range(1, 4)]:
            filepath = f"rules/{self.ruleSetFolder}/{apID}.json"

            # create folder if it doesn't exist
            if not Path(filepath).is_file():
                Path(f"rules/{self.ruleSetFolder}").mkdir(parents=True, exist_ok=True)

            # clear contents of folder
            with open(filepath, "w") as f:
                json.dump({
                    "RS": [],
                    "RSint": [],
                    "RSev": [],
                    "RSev_int": []
                }, f, indent=2)

            # get document from MongoDB
            document = collection.find_one({"label": "output"})

            # get desired individual from document
            individual = document["data"]["bestIndividuals"][apID]

            # add ruleSets of individual to the file
            for ruleSet in ["RS", "RSint", "RSev", "RSev_int"]:
                if ruleSet not in individual:
                    continue
                for rule in individual[ruleSet]:
                    self.addRule(apID, ruleSet, rule, self.ruleSetFolder)

    def addBestPoolInGeneration(self, generation, metric: Literal["simulationTime", "EVStops", "averageEVSpeed"], databaseName=None, ruleSetFolder=None):
        if databaseName:
            self.databaseName = databaseName
            if ruleSetFolder:
                self.ruleSetFolder = ruleSetFolder
            else:
                self.ruleSetFolder = databaseName
            self.initClient()

        collection = self.db[str(generation)]

        for apID in ["AP" + str(i) for i in range(1, 4)]:
            filepath = f"rules/{self.ruleSetFolder}/{apID}.json"

            # create folder if it doesn't exist
            if not Path(filepath).is_file():
                Path(f"rules/{self.ruleSetFolder}").mkdir(parents=True, exist_ok=True)

            # clear contents of folder
            with open(filepath, "w") as f:
                json.dump({
                    "RS": [],
                    "RSint": [],
                    "RSev": [],
                    "RSev_int": []
                }, f, indent=2)

            # get document from MongoDB
            document = collection.find_one({"label": "output"})

            # get desired individual from document
            individual = document["data"]["stats"]["bestResults"][metric]["trafficLights"][apID]

            # add ruleSets of individual to the file
            for ruleSet in ["RS", "RSint"]:
                for rule in individual[ruleSet]:
                    self.addRule(apID, ruleSet, rule, self.ruleSetFolder)

    def findBestIndivs(self, databaseName, label):
        self.databaseName = databaseName
        self.initClient()

        for apID in ["AP" + str(i) for i in range(1, 4)]:
            maxIndiv = {"fitness": 100000000}
            maxIndivGen = 0
            maxIndivIndex = 0
            for generation in range(1, 49):
                collection = self.db[str(generation)]

                document = collection.find_one({
                    "label": label,
                    "id": apID
                })
                individuals = document["data"]
                for i, indiv in enumerate(individuals):
                    if indiv["fitness"] < maxIndiv["fitness"]:
                        maxIndiv = indiv
                        maxIndivGen = generation
                        maxIndivIndex = i
            print(apID)
            print(f'fitness: {maxIndiv["fitness"]}')
            print(f'generation: {maxIndivGen}')
            print(f'index: {maxIndivIndex}')
            print()

    def JSONToCSV(self, filename: str):
        with open(f"results/{filename}.json", "r") as f:
            apData = json.load(f)
        fieldnames = [
            "generation",
            "simulationTime",
            "EVStops",
            "averageEVSpeed"
        ]
        with open(f"results/{filename}.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in apData:
                writer.writerow(row)

    def getTopFitnessesPerGeneration(self, databaseName: str, filename: str):
        self.databaseName = databaseName
        self.initClient()

        data = []

        for generation in range(60, 0, -1):
            genData = {"generation": generation}
            for apID in ["AP" + str(x) for x in range(1, 4)]:
                collection = self.db[str(generation)]
                document = collection.find_one({"label": "output"})
                individual = document["data"]["bestIndividuals"][apID]
                genData[f"{apID} topFitness"] = individual["fitness"]
                # genData[f"{apID} topNormalizedFitness"] = individual["normalizedFitness"]
            data.append(genData)

        fieldnames = ["generation"]
        for apID in ["AP" + str(x) for x in range(1, 4)]:
            fieldnames.append(f"{apID} topFitness")
            # fieldnames.append(f"{apID} topNormalizedFitness")
        with open(f"results/{filename}.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    def getBestResultsPerGeneration(self, databaseName: str, filename: str):
        self.databaseName = databaseName
        self.initClient()

        data = []

        for generation in range(60, 0, -1):
            genData = {"generation": generation}

            collection = self.db[str(generation)]
            document = collection.find_one({"label": "output"})
            bestResults = document["data"]["stats"]["bestResults"]

            for key, value in bestResults.items():
                genData[key] = value["value"]
            data.append(genData)

        fieldnames = ["generation", "EVStops", "averageEVSpeed", "simulationTime", "totalFitness"]
        with open(f"results/{filename}.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    def addRuleSetToRuleSet(self, mainRuleSetName: str, otherRuleSetName: str):
        for apID in ["AP" + str(i) for i in range(1, 4)]:
            # get rule sets from files
            with open(f"rules/{mainRuleSetName}/{apID}.json", "r") as f:
                mainRules = json.load(f)
            with open(f"rules/{otherRuleSetName}/{apID}.json", "r") as f:
                otherRules = json.load(f)

            # combine them
            for key, val in otherRules.items():
                for rule in val:
                    mainRules[key].append(rule)

            # rewrite the
            with open(f"rules/{mainRuleSetName}/{apID}.json", "w") as f:
                json.dump(mainRules, f, indent=2)

    def removeOneRuleSet(self, ruleSetFolderName, ruleSetName: Literal["RS", "RSint"]):
        for apID in ["AP" + str(i) for i in range(1, 4)]:
            with open(f"rules/{ruleSetFolderName}/{apID}.json", "r") as f:
                ruleSets = json.load(f)
            ruleSets[ruleSetName] = []
            with open(f"rules/{ruleSetFolderName}/{apID}.json", "w") as f:
                json.dump(ruleSets, f, indent=2)

    def getTestResultsFromDB(self, docID, outputFileName):
        self.databaseName = "evaluation"
        self.initClient()
        testResults = self.db["test results"]

        results = testResults.find_one(ObjectId(docID))["results"]

        with open(f"results/final/{outputFileName}.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            for row in results:
                writer.writerow(row)
