from __future__ import annotations

import os
import json
import csv
import pymongo
from pathlib import Path

from Simulation import Simulation
from Individual import Individual
from Rule import Rule
import PredicateSet
import CoopPredicateSet
import EVPredicateSet
import EVCoopPredicateSet
from DriverTest import DriverTest

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from AgentPool import AgentPool


class Tester(Simulation):
    def initClient(self):
        username = os.environ["MONGODB_USERNAME"]
        password = os.environ["MONGODB_PASSWORD"]

        self.client = pymongo.MongoClient(f"mongodb+srv://{username}:{password}@cluster0.a9379.mongodb.net/status?retryWrites=true&w=majority")
        self.db = self.client[self.databaseName]

    def getTestSimRunner(self):
        return DriverTest(self.cmd, self.setUpTuple, *self.getMaxSimulationTimes(), *self.getUserDefinedRules(), self.useShoutahead, self.useEVCoopPredicates)

    def initTestIndividual(self, agentPool: AgentPool):
        with open(f"rules/{self.ruleSetFolder}/{agentPool.getID()}.json", "r") as f:
            data = json.load(f)

        ruleSets = {}
        for ruleSet in data:
            rules = []
            for r in data[ruleSet]:
                rules.append(Rule(r["type"], r["conditions"], r["action"], agentPool))
            ruleSets[ruleSet] = rules

        agentPool.testIndividual = Individual("Test", agentPool, ruleSets["RS"], ruleSets["RSint"], ruleSets["RSev"], ruleSets["RSev_int"])

        agentPool.RSPredicates = PredicateSet.getPredicateSet()
        agentPool.RSintPredicates = CoopPredicateSet.getPredicateSet(agentPool)
        agentPool.RSevPredicates = EVPredicateSet.getPredicateSet()
        agentPool.RSev_intPredicates = EVCoopPredicateSet.getPredicateSet(agentPool)
        agentPool.EVLanePredicates = EVPredicateSet.getAgentSpecificPredicates(agentPool)

    def config(self):
        for ap in self.setUpTuple[2]:
            self.initTestIndividual(ap)

    def testRules(self, ruleSetFolder: str, UDRulesTuple, gui: bool, iterations: int):
        # override options
        self.maxGreenAndYellowPhaseTime_UDRule = UDRulesTuple[0]
        self.maxRedPhaseTime_UDRule = UDRulesTuple[1]
        self.assignGreenPhaseToSingleWaitingPhase_UDRule = UDRulesTuple[2]
        self.gui = gui
        self.ruleSetFolder = ruleSetFolder

        self.initCmd()
        self.initSetUpTuple()
        self.config()

        results = []
        for i in range(iterations):
            simRunner = self.getTestSimRunner()
            simRunner.runTest()

            res = simRunner.getResults()
            results.append(res)

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
            self.addBestIndividualsInGeneration(i)
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

    def addBestIndividualsInGeneration(self, generation):
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
                for rule in individual[ruleSet]:
                    self.addRule(apID, ruleSet, rule, self.ruleSetFolder)

    def findBestIndivs(self, databaseName, label):
        for apID in ["AP" + str(i) for i in range(1, 4)]:
            maxIndiv = {"fitness": 100000000}
            maxIndivGen = 0
            maxIndivIndex = 0
            for generation in range(1, 49):
                collection = self.client[databaseName][str(generation)]

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
            print(apID, maxIndiv["fitness"], maxIndivGen, maxIndivIndex)

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
