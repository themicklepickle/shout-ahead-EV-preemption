import os
import sys
import inspect

import PredicateSet 
import CoopPredicateSet

import EvolutionaryLearner as EvolutionaryLearner
from TrafficLight import TrafficLight
from Rule import Rule
from random import randrange
from operator import attrgetter

class AgentPool:
                
        # INTIALIZE AGENT POOL VARIABLES
    def __init__(self, identifier, actionSet, minIndividualRunsPerGen, trafficLightsAssigned):
        self.id = identifier                                            # AgentPool name
        self.actionSet = actionSet                                      # A list of action names that can be applied by assigned TL's of the pool
        self.addDoNothingAction()                                       # Add "do nothing" action to action set 
        self.trafficLightsAssigned = []                                 # List of traffic lights using Agent Pool 
        self.setTrafficLightsAssigned(trafficLightsAssigned)
        self.individuals = []                   
        self.userDefinedRuleSet = [Rule(-1, ["emergencyVehicleApproachingVertical"], -1, self), Rule(-1, ["emergencyVehicleApproachingHorizontal"], -1, self), Rule(-1, ["maxGreenPhaseTimeReached"], -1, self), Rule(-1, ["maxYellowPhaseTimeReached"], -1, self)]
        self.minIndividualRunsPerGen = minIndividualRunsPerGen

    def getID(self):
        return self.id

    def getActionSet(self):
        return self.actionSet
    
    def getCoopPredicates(self):
        return self.coopPredicates

    def getIndividualsSet(self):
        return self.individuals
    
    def updateIndividualsSet(self, individuals):
        self.individuals = individuals
    
    def initIndividuals(self):
        self.individuals = EvolutionaryLearner.initIndividuals(self)

    def getAssignedTrafficLights(self):
        return self.trafficLightsAssigned
    
    def setTrafficLightsAssigned(self, trafficLightsAssigned):
        if isinstance(trafficLightsAssigned, list):
            for tl in trafficLightsAssigned:
                self.trafficLightsAssigned.append(tl)
                tl.assignToAgentPool(self)
                #print(tl.getName(), "is assigned to agent pool", tl.getAgentPool().getID())
        else:
            trafficLightsAssigned.assignToAgentPool(self)

    def addNewTrafficLight(self, trafficLight):
        #print("Adding", trafficLight.getName(), "to", self.getID())
        self.trafficLightsAssigned.append(trafficLight)
        trafficLight.assignToAgentPool(self)
    
    def addDoNothingAction(self):
        self.actionSet.append("DoNothing")

        # COMPLETES THE INITIALIZATION OF AGENT POOL COMPONENTS THAT REQUIRE ALL AGENT POOLS TO BE INITIALIZED FIRST
    def finishSetUp(self):
        self.coopPredicates = self.initCoopPredicates()                 # Store Observations of communicated intentions here since they are agent specific
        self.initIndividuals()                                          # Populate Agent Pool's own rule set with random rules
        for tl in self.trafficLightsAssigned:
            tl.initPhaseTimeSpentInRedArray()

        # SELECTS AN INDIVIDUAL TO PASS TO A TRAFFIC LIGHT WHEN REQUESTED
    def selectIndividual(self):
        self.individualsNeedingRuns = []
        for i in self.individuals:
            if i.getSelectedCount() < self.minIndividualRunsPerGen:
                self.individualsNeedingRuns.append(i)
        
        if len(self.individualsNeedingRuns) == 0:
            return self.getIndividualsSet()[randrange(0, len(self.getIndividualsSet()))] # Currently returning a random rule
        
        elif len(self.individualsNeedingRuns) == 1:
            return self.individualsNeedingRuns[0]
        else:
            return self.individualsNeedingRuns[randrange(0, len(self.individualsNeedingRuns))]

        # RETURN RANDOM PREDICATE FROM coopPredicate LIST FOR A RULE IN RSint
    def getRandomRSintPredicate(self):
        return self.coopPredicates[randrange(len(self.coopPredicates))]
    
    def initCoopPredicates(self):
        return CoopPredicateSet.getPredicateSet(self)
    
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

    def normalizeIndividualsFitnesses(self):
        #print("Normalizing fitnesses.")
        self.individuals.sort(key=lambda x: x.getNegatedFitness(), reverse = True) # Sort individuals by fitness 
        #print("The top individual is", self.individuals[0], "and it has a fitness of", self.individuals[0].getFitness())

        if (self.individuals[0].getNegatedFitness() - self.individuals[len(self.individuals)-1].getNegatedFitness()) == 0:
            for i in self.individuals:
                i.setNormalizedFitness(0.0001)  # Set normalized fitness to an arbitrary, small value
        else:        
                # Calculate normalized fitness value for each individual in the agent pool
            for i in self.individuals:
                i.setNormalizedFitness((i.getNegatedFitness()-self.individuals[len(self.individuals)-1].getNegatedFitness())/(self.individuals[0].getNegatedFitness()-self.individuals[len(self.individuals)-1].getNegatedFitness())) 
                #print("Normalized fitness value of", i, "is", (i.getNegatedFitness() - self.individuals[len(self.individuals)-1].getNegatedFitness()) / (self.individuals[0].getNegatedFitness() - self.individuals[len(self.individuals)-1].getNegatedFitness()))
# def run():
#     ap = AgentPool("ap1", ["H_S_G", "H_S_Y", "H_L_G", "H_L_Y"])
#     for i in ap.getIndividualsSet():    
#         print("Individual", i.getID(), "has rules with the following conditions and actions:\n")
#         for r in i.getRuleSet():
#             print(r.getConditions(), "and the action is:", r.getAction(), "\n\n")

# if __name__ == "__main__":
#     run()