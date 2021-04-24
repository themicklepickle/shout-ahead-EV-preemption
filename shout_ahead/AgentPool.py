from __future__ import annotations

from random import randrange
import json

import PredicateSet
import CoopPredicateSet
import EVPredicateSet
import EVCoopPredicateSet
import EvolutionaryLearner as EvolutionaryLearner
from shout_ahead.Rule import Rule

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from shout_ahead.Individual import Individual
    from TrafficLight import TrafficLight


class AgentPool:

    # INTIALIZE AGENT POOL VARIABLES
    def __init__(self, identifier: str, actionSet: List[str], minIndividualRunsPerGen: int, trafficLightsAssigned: List[TrafficLight]):
        self.id = identifier                                            # AgentPool name
        self.actionSet = actionSet                                      # A list of action names that can be applied by assigned TL's of the pool
        self.addDoNothingAction()                                       # Add "do nothing" action to action set
        self.trafficLightsAssigned: List[TrafficLight] = []                                 # List of traffic lights using Agent Pool
        self.setTrafficLightsAssigned(trafficLightsAssigned)
        self.individuals: List[Individual] = []
        self.minIndividualRunsPerGen = minIndividualRunsPerGen
        self.individualsNeedingRuns: List[Individual]
        self.RSPredicates: List[str]
        self.RSintPredicates: List[str]
        self.RSevPredicates: List[str]
        self.RSev_intPredicates: List[str]
        self.EVLanePredicates: List[str]
        self.RSlearned: List[Rule]
        self.RSlearned_int: List[Rule]

    def getID(self):
        return self.id

    def getActionSet(self):
        return self.actionSet

    def getRSPredicates(self):
        return self.RSPredicates

    def getRSintPredicates(self):
        return self.RSintPredicates

    def getRSevPredicates(self):
        return self.RSevPredicates

    def getRSev_intPredicates(self):
        return self.RSev_intPredicates

    def getEVLanePredicates(self):
        return self.EVLanePredicates

    def getRSlearned(self):
        return self.RSlearned

    def setRSlearned(self, RSlearned: List[Rule]):
        self.RSlearned = RSlearned

    def getRSlearned_int(self):
        return self.RSlearned_int

    def setRSlearned_int(self, RSlearned_int: List[Rule]):
        self.RSlearned_int = RSlearned_int

    def getIndividualsSet(self):
        return self.individuals

    def updateIndividualsSet(self, individuals: List[Individual]):
        self.individuals = individuals

    def getAssignedTrafficLights(self):
        return self.trafficLightsAssigned

    def setTrafficLightsAssigned(self, trafficLightsAssigned: List[TrafficLight]):
        if isinstance(trafficLightsAssigned, list):
            for tl in trafficLightsAssigned:
                self.trafficLightsAssigned.append(tl)
                tl.assignToAgentPool(self)
                # print(tl.getName(), "is assigned to agent pool", tl.getAgentPool().getID())
        else:
            trafficLightsAssigned.assignToAgentPool(self)

    def addNewTrafficLight(self, trafficLight: TrafficLight):
        self.trafficLightsAssigned.append(trafficLight)
        trafficLight.assignToAgentPool(self)

    def addDoNothingAction(self):
        self.actionSet.append("DoNothing")

    def getLearnedRuleSet(self, ruleType: str, folder: str):
        opposites = {
            "RS": "RSev",
            "RSev": "RS",
            "RSint": "RSev_int",
            "RSev_int": "RSint"
        }

        # get rule set in JSON format
        with open(f"rules/{folder}/{self.id}.json", "r") as f:
            ruleSets = json.load(f)
        JSONRuleSet = ruleSets[opposites[ruleType]]

        # convert JSON rules to Rule objects
        ruleSet = []
        for r in JSONRuleSet:
            rule = Rule("learned", r["conditions"], r["action"], self)
            rule.setWeight(r["weight"])
            ruleSet.append(rule)

        return ruleSet

    def finishSetUp(self, useShoutahead: bool, ruleSetOptions: List[str]):
        # get predicates for each rule set
        self.RSPredicates = PredicateSet.getPredicateSet()
        self.RSintPredicates = CoopPredicateSet.getPredicateSet(self)
        self.RSevPredicates = EVPredicateSet.getPredicateSet()
        self.RSev_intPredicates = EVCoopPredicateSet.getPredicateSet(self)
        self.EVLanePredicates = EVPredicateSet.getAgentSpecificPredicates(self)

        # get the previously learned rules
        localRSType, coopRSType, learnedLocalRSFolder, learnedCoopRSFolder = ruleSetOptions
        self.RSlearned = self.getLearnedRuleSet(localRSType, learnedLocalRSFolder)
        if useShoutahead:
            self.RSlearned_int = self.getLearnedRuleSet(coopRSType, learnedCoopRSFolder)

        # intialize the individuals
        self.individuals = EvolutionaryLearner.initIndividuals(self, useShoutahead, ruleSetOptions)
        for tl in self.trafficLightsAssigned:
            tl.initPhaseTimeSpentInRedArray()

    def selectIndividual(self, testing):
        if testing:
            return self.testIndividual
        self.individualsNeedingRuns = []
        for i in self.individuals:
            if i.getSelectedCount() < self.minIndividualRunsPerGen:
                self.individualsNeedingRuns.append(i)

        if len(self.individualsNeedingRuns) == 0:
            return self.getIndividualsSet()[randrange(0, len(self.getIndividualsSet()))]  # Currently returning a random rule

        elif len(self.individualsNeedingRuns) == 1:
            return self.individualsNeedingRuns[0]
        else:
            return self.individualsNeedingRuns[randrange(0, len(self.individualsNeedingRuns))]

    def getRandomRSPredicate(self):
        return self.RSPredicates[randrange(len(self.RSPredicates))]

    def getRandomRSintPredicate(self):
        return self.RSintPredicates[randrange(len(self.RSintPredicates))]

    def getRandomRSevPredicate(self):
        return self.RSevPredicates[randrange(len(self.RSevPredicates))]

    def getRandomRSev_intPredicate(self):
        if len(self.RSev_intPredicates) == 0:
            return None
        return self.RSev_intPredicates[randrange(len(self.RSev_intPredicates))]

    def getRandomEVLanePredicate(self):
        return self.EVLanePredicates[randrange(len(self.EVLanePredicates))]

    def getBestIndividual(self):
        bestIndivList = sorted(self.individuals, key=lambda x: x.getFitness())
        return bestIndivList[0]

    # RETURN THE BEST SIMULATION TIME
    def getBestIndividualSimulationTime(self):
        bestIndivSimTimeList = sorted(self.individuals, key=lambda x: x.getLastRunTime())
        return bestIndivSimTimeList[0].getLastRunTime()

    def getBestIndividualAggregateVehWaitTime(self):
        bestIndivAggregateVehWaitTimeList = sorted(self.individuals, key=lambda x: x.getAggregateVehicleWaitTime())
        return bestIndivAggregateVehWaitTimeList[0].getAggregateVehicleWaitTime()

    def getBestIndividualAverageEVSpeed(self):
        bestIndividualAverageEVSpeed = max(self.individuals, key=lambda x: x.getAverageEVSpeed())
        return bestIndividualAverageEVSpeed

    def getBestIndividualEVStops(self):
        bestEVStopsList = sorted(self.individuals, key=lambda x: x.getEVStops())
        return bestEVStopsList[0].getEVStops()

    def normalizeIndividualsFitnesses(self):
        self.individuals.sort(key=lambda x: x.getNegatedFitness(), reverse=True)  # Sort individuals by fitness

        if (self.individuals[0].getNegatedFitness() - self.individuals[len(self.individuals)-1].getNegatedFitness()) == 0:
            for i in self.individuals:
                i.setNormalizedFitness(0.0001)  # Set normalized fitness to an arbitrary, small value
        else:
            # Calculate normalized fitness value for each individual in the agent pool
            for i in self.individuals:
                i.setNormalizedFitness((i.getNegatedFitness()-self.individuals[len(self.individuals)-1].getNegatedFitness()) /
                                       (self.individuals[0].getNegatedFitness()-self.individuals[len(self.individuals)-1].getNegatedFitness()))

# def run():
#     ap = AgentPool("ap1", ["H_S_G", "H_S_Y", "H_L_G", "H_L_Y"])
#     for i in ap.getIndividualsSet():
#         print("Individual", i.getID(), "has rules with the following conditions and actions:\n")
#         for r in i.getRuleSet():
#             print(r.getConditions(), "and the action is:", r.getAction(), "\n\n")

# if __name__ == "__main__":
#     run()
