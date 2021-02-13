from __future__ import annotations

from random import randrange

import PredicateSet
import CoopPredicateSet
import EVPredicateSet
import EvolutionaryLearner as EvolutionaryLearner

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from Individual import Individual
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
        self.EVLanePredicates: List[str]

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

    def getEVLanePredicates(self):
        return self.EVLanePredicates

    def getIndividualsSet(self):
        return self.individuals

    def updateIndividualsSet(self, individuals: List[Individual]):
        self.individuals = individuals

    def initIndividuals(self, useShoutahead):
        self.individuals = EvolutionaryLearner.initIndividuals(self, useShoutahead)

    def getAssignedTrafficLights(self):
        return self.trafficLightsAssigned

    def setTrafficLightsAssigned(self, trafficLightsAssigned: List[TrafficLight]):
        if isinstance(trafficLightsAssigned, list):
            for tl in trafficLightsAssigned:
                self.trafficLightsAssigned.append(tl)
                tl.assignToAgentPool(self)
                #print(tl.getName(), "is assigned to agent pool", tl.getAgentPool().getID())
        else:
            trafficLightsAssigned.assignToAgentPool(self)

    def addNewTrafficLight(self, trafficLight: TrafficLight):
        self.trafficLightsAssigned.append(trafficLight)
        trafficLight.assignToAgentPool(self)

    def addDoNothingAction(self):
        self.actionSet.append("DoNothing")

        # COMPLETES THE INITIALIZATION OF AGENT POOL COMPONENTS THAT REQUIRE ALL AGENT POOLS TO BE INITIALIZED FIRST
    def finishSetUp(self, useShoutahead):
        self.RSPredicates = PredicateSet.getPredicateSet()
        self.RSintPredicates = CoopPredicateSet.getPredicateSet(self)
        self.RSevPredicates = EVPredicateSet.getPredicateSet()
        self.EVLanePredicates = EVPredicateSet.getAgentSpecificPredicates(self)

        self.initIndividuals(useShoutahead)  # Populate Agent Pool's own rule set with random rules
        for tl in self.trafficLightsAssigned:
            tl.initPhaseTimeSpentInRedArray()

    # SELECTS AN INDIVIDUAL TO PASS TO A TRAFFIC LIGHT WHEN REQUESTED
    def selectIndividual(self):
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

    def getBestIndividualMeanEVSpeed(self):
        bestMeanEVSpeedList = sorted(self.individuals, key=lambda x: x.getMeanEVSpeed(), reverse=True)
        return bestMeanEVSpeedList[0].getMeanEVSpeed()

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
