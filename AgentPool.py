from __future__ import annotations

from random import randrange

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
        self.individuals = []
        self.minIndividualRunsPerGen = minIndividualRunsPerGen
        self.individuals: List[Individual]
        self.individualsNeedingRuns: List[Individual]
        self.coopPredicates: List[str]
        self.EVPredicates: List[str]

    def getID(self):
        return self.id

    def getActionSet(self):
        return self.actionSet

    def getCoopPredicates(self):
        return self.coopPredicates

    def getEVPredicates(self):
        return self.EVPredicates

    def getIndividualsSet(self):
        return self.individuals

    def updateIndividualsSet(self, individuals: List[Individual]):
        self.individuals = individuals

    def initIndividuals(self):
        self.individuals = EvolutionaryLearner.initIndividuals(self)

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
    def finishSetUp(self):
        self.coopPredicates = self.initCoopPredicates()  # Store Observations of communicated intentions here since they are agent specific
        self.EVPredicates = self.initEVPredicates()
        self.initIndividuals()  # Populate Agent Pool's own rule set with random rules
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

    # RETURN RANDOM PREDICATE FROM coopPredicate LIST FOR A RULE IN RSint
    def getRandomRSintPredicate(self):
        return self.coopPredicates[randrange(len(self.coopPredicates))]

    def getRandomRSevPredicate(self):
        return self.EVPredicates[randrange(len(self.EVPredicates))]

    def initCoopPredicates(self):
        return CoopPredicateSet.getPredicateSet(self)

    def initEVPredicates(self):
        return EVPredicateSet.getPredicateSet(self)

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
            lastIndividual = self.individuals[len(self.individuals)-1]
            firstIndividual = self.individuals[0]
            for i in self.individuals:
                i.setNormalizedFitness((i.getNegatedFitness() - lastIndividual.getNegatedFitness()) /
                                       (firstIndividual.getNegatedFitness() - lastIndividual.getNegatedFitness()))

# def run():
#     ap = AgentPool("ap1", ["H_S_G", "H_S_Y", "H_L_G", "H_L_Y"])
#     for i in ap.getIndividualsSet():
#         print("Individual", i.getID(), "has rules with the following conditions and actions:\n")
#         for r in i.getRuleSet():
#             print(r.getConditions(), "and the action is:", r.getAction(), "\n\n")

# if __name__ == "__main__":
#     run()
