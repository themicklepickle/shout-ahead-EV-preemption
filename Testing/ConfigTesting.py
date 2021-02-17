from __future__ import annotations

import json
import os
import pymongo
from pathlib import Path

from Individual import Individual
from Rule import Rule
import PredicateSet
import CoopPredicateSet
import EVPredicateSet

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from AgentPool import AgentPool


def initTestIndividual(agentPool: AgentPool, folder: str):
    with open(f"rules/{folder}/{agentPool.getID()}.json", "r") as f:
        data = json.load(f)

    ruleSets = {}
    for ruleSet in data:
        rules = []
        for r in data[ruleSet]:
            rules.append(Rule(r["type"], r["conditions"], r["action"], agentPool))
        ruleSets[ruleSet] = rules

    agentPool.testIndividual = Individual("Test", agentPool, ruleSets["RS"], ruleSets["RSint"], ruleSets["RSev"])
    agentPool.RSPredicates = PredicateSet.getPredicateSet()
    agentPool.RSintPredicates = CoopPredicateSet.getPredicateSet(agentPool, True)
    agentPool.RSevPredicates = EVPredicateSet.getPredicateSet()
    agentPool.EVLanePredicates = EVPredicateSet.getAgentSpecificPredicates(agentPool)


def run(agentPools: AgentPool, folder: str):
    for ap in agentPools:
        initTestIndividual(ap, folder)


def addRule(apID, ruleSet, rule, folder):
    filepath = f"rules/{folder}/{apID}.json"

    # get existing dict
    if not Path(filepath).is_file():
        Path(f"rules/{folder}").mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump({
                "RS": [],
                "RSint": [],
                "RSev": []
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
    # print(data)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def findBestIndivs():
    username = os.environ["MONGODB_USERNAME"]
    password = os.environ["MONGODB_PASSWORD"]
    client = pymongo.MongoClient(f"mongodb+srv://{username}:{password}@status.rxyk4.mongodb.net/status?retryWrites=true&w=majority")

    startTime = "Sat_Feb_13_12:34:59_AM_2021"
    label = "old agent pool"

    for apID in ["AP" + str(i) for i in range(1, 4)]:
        maxIndiv = {"fitness": 100000000}
        maxIndivGen = 0
        maxIndivIndex = 0
        for generation in range(1, 49):
            collection = client[startTime][str(generation)]

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


def addBestIndividualsInGeneration(generation):

    username = os.environ["MONGODB_USERNAME"]
    password = os.environ["MONGODB_PASSWORD"]
    client = pymongo.MongoClient(f"mongodb+srv://{username}:{password}@status.rxyk4.mongodb.net/status?retryWrites=true&w=majority")

    startTime = "Sat_Feb_13_12:34:59_AM_2021"
    # generation = 3
    label = "new agent pool"
    individualIndex = 1
    folder = "Sat_Feb_13_12:34:59_AM_2021"

    collection = client[startTime][str(generation)]

    for apID in ["AP" + str(i) for i in range(1, 4)]:
        filepath = f"rules/{folder}/{apID}.json"
        with open(filepath, "w") as f:
            json.dump({
                "RS": [],
                "RSint": [],
                "RSev": []
            }, f, indent=2)

        document = collection.find_one({
            "label": label,
            "id": apID
        })
        individual = document["data"][individualIndex]
        for ruleSet in ["RS", "RSint", "RSev"]:
            # for ruleSet in ["RSev"]:
            for rule in individual[ruleSet]:
                # if rule["weight"] != 0:
                addRule(apID, ruleSet, rule, folder)


if __name__ == "__main__":
    addBestIndividualsInGeneration(1)
