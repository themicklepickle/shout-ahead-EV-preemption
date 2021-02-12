from __future__ import annotations

import statistics
from numpy.random import choice
from random import randrange

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Union, Literal, Tuple
    from AgentPool import AgentPool
    from Rule import Rule


class Individual:
    global epsilon  # paramater between 0 and 1 used to determine importance of doing exploration (higher epsilon = more exploration)
    epsilon = 0.5
    global defaultFitness
    defaultFitness = 10000.0

    # INTIALIZE OBJECT VARIABLES
    def __init__(self, identifier: str, agentPool: AgentPool, RS: List[Rule], RSint: List[Rule], RSev: List[Rule]) -> None:
        self.id = identifier
        self.RS = RS                                # Set of rules without observations of communicated intentions
        self.RSint = RSint                          # Set of rules with observations of communicated intentions
        self.RSev = RSev
        self.selectedCount = 0                      # Number of times individual has been chosen during a generation
        self.totalSelectedCount = 0                 # Total number of times individual has been chosen during a training period
        self.agentPool = agentPool                  # AgentPool name
        self.fitness = defaultFitness               # Default fitness value is large
        self.normalizedFitness = defaultFitness     # Normalized fitness value is equal to the regular fitness value
        self.runFitnessResults: List[float] = []
        self.lastRunTime: float = 2.2250738585072014e-308
        self.ruleWeightSum: float = 0
        self.aggregateVehicleWaitTime: float = 0
        self.fitnessRuleApplicationPenalty: float = 0      # A penalty applied to the fitness of an Individual when its rule aren't applied, or result in negative outcomes, in a simulation
        self.meanEVSpeedsList: List[float] = []
        self.meanEVSpeed: float = 0
        self.EVStops: int = 0

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self) -> str:
        return str(self.id)

    def getJSON(self) -> dict:
        return {
            "id": self.id,
            "actionSet": self.agentPool.getActionSet(),
            "RS": [rule.getJSON() for rule in self.RS],
            "RSint": [rule.getJSON() for rule in self.RSint],
            "RSev": [rule.getJSON() for rule in self.RSev],
            "fitness": self.fitness,
            "agentPool": self.agentPool,
            "selectedCount": self.selectedCount,
            "totalSelectedCount": self.totalSelectedCount,
            "normalizedFitness": self.normalizedFitness,
            "lastRunTime": self.lastRunTime,
            "runFitnessResults": self.runFitnessResults,
            "ruleWeightSum": self.ruleWeightSum,
            "aggregateVehicleWaitTime": self.aggregateVehicleWaitTime,
            "fitnessRuleApplicationPenalty": self.fitnessRuleApplicationPenalty,
            "meanEVSpeedList": self.meanEVSpeedsList,
            "meanEVSpeed": self.meanEVSpeed,
            "EVStops": self.EVStops
        }

    # RETURN INDIVIDUAL IDENTIFIER
    def getID(self):
        return self.id

    # RETURN INDIVIDUAL'S RULE SET
    def getRS(self):
        return self.RS

    # RETURN INDIVIDUAL'S COOP RULE SET
    def getRSint(self):
        return self.RSint

    # RETURN INDIVIDUAL'S EV RULE SET
    def getRSev(self):
        return self.RSev

    # INCREMENT selectedCount BY ONE FOR EVOLUTIONARY LEARNING PURPOSES
    def selected(self):
        self.selectedCount += 1
        self.totalSelectedCount += 1

    # RESET selectedCount TO ZERO
    def resetSelectedCount(self):
        self.selectedCount = 0

    # RETURN selectedCount
    def getSelectedCount(self):
        return self.selectedCount

    def getTotalSelectedCount(self):
        return self.totalSelectedCount

    # RETURN INDIVIDUAL'S FITNESS SCORE
    def getFitness(self):
        return self.fitness

    def getNegatedFitness(self):
        return self.fitness * -1

    # UPDATE INDIVIDUAL'S FITNESS SCORE
    def updateFitness(self, fitness: float, EVFitness: float):
        # Add run fitness plus rule application penalty minus EV fitness to master rFit list
        self.runFitnessResults.append(fitness + self.fitnessRuleApplicationPenalty - EVFitness)  # minus EV fitness cause we are trying to minimize fitness values

        # Reset values for next simulation run
        self.fitnessRuleApplicationPenalty = 0
        self.resetEVStops()
        self.resetMeanEVSpeed()

        # Calculate fitness
        if sum(self.runFitnessResults) == 0:
            self.fitness = defaultFitness
        elif self.totalSelectedCount == 0:
            self.fitness = sum(self.runFitnessResults) / 1
        else:
            self.fitness = sum(self.runFitnessResults) / self.totalSelectedCount

    def getNormalizedFitness(self):
        return self.normalizedFitness

    def setNormalizedFitness(self, fitnessValue: float):
        self.normalizedFitness = fitnessValue

    # RETURN THE LENGTH OF THE LAST RUN THE INDIVIDUAL PARTICIPATED IN
    def getLastRunTime(self):
        return self.lastRunTime

    # UPDATE THE LENGTH OF THE LAST RUN THE INDIVIDUAL PARTICIPATED IN
    def updateLastRunTime(self, runtime: float):
        self.lastRunTime = runtime

    def resetLastRunTime(self):
        self.lastRunTime = 0

    def getAggregateVehicleWaitTime(self):
        return self.aggregateVehicleWaitTime

    def updateAggregateVehicleWaitTime(self, waitTime: float):
        self.aggregateVehicleWaitTime += waitTime

    def resetAggregateVehicleWaitTime(self):
        self.aggregateVehicleWaitTime = 0

    # ----------- EVs ----------- #
    def getMeanEVSpeed(self):
        return self.meanEVSpeed

    def updateMeanEVSpeed(self, EVSpeedsList: List[float]):
        if EVSpeedsList == []:
            return
        self.meanEVSpeedsList.append(statistics.mean(EVSpeedsList))
        self.meanEVSpeed = statistics.mean(self.meanEVSpeedsList)

    def resetMeanEVSpeed(self):
        self.meanEVSpeedsList = []
        self.meanEVSpeed = 0

    def getEVStops(self):
        return self.EVStops

    def updateEVStops(self, numEVStops: int):
        self.EVStops += numEVStops

    def resetEVStops(self):
        self.EVStops = 0
    # ----------- END ----------- #

    # RETURN SUM OF ALL WEIGHTS IN A RULE SET
    def getSumRuleWeights(self) -> float:
        ruleSet = self.getRS() + self.getRSev()
        self.ruleWeightSum = sum(rule.getWeight() for rule in ruleSet)

        return self.ruleWeightSum

    # RETURN A RULE FROM RS BASED ON THEIR PROBABILITIES
    def selectRule(self, validRules: List[Rule]) -> Union[Rule, Literal[-1]]:
        if len(validRules) == 0:
            return -1
        elif len(validRules) == 1:
            return validRules[0]

        rsMax, rsRest = self.subDivideValidRules(validRules)

        rules: List[Rule] = []
        probabilities: List[float] = []

        # Add a number of max weight rules to selection set relative to their probabilities
        for rule in rsMax:
            probability = self.getRuleProbabilityMax(rule, rsMax, rsRest)
            rules.append(rule)
            probabilities.append(probability)

        # If rsRest contains elements too, calculate their probabilities
        if len(rsRest) > 0:
            # Acquire sum of weights in rsRest
            sumOfWeights = self.getSumOfWeights(rsRest)

            # If sum of weights is 0, assign a weight based on the available probability left
            if sumOfWeights == 0:
                probability = (1 - sum(probabilities)) / len(rsRest)

                # If sum of weights is 0, assign equal part of the remaining probability to each rule
                for rule in rsRest:
                    rules.append(rule)
                    probabilities.append(probability)
            else:
                # If weights do not sum to 0, normalize them between 0 and 1 (0.1 and 1.1 technically) and calculate their probabilities
                weightsList = self.getWeightsList(rsRest)
                self.normalizeRuleWeights(rsRest, weightsList)
                sumOfWeights = self.getSumOfWeights(self.getNormalizedWeightsList(rsRest))

                # Individually calculate probabilities
                for rule in rsRest:
                    probability = self.getRuleProbabilityRest(rule, probabilities, sumOfWeights, rsRest)
                    rules.append(rule)
                    probabilities.append(probability)

        # print("Probabilities have a sum of:", sum(probabilities))
        if sum(probabilities) == 0:
            for i in range(len(probabilities)):
                probabilities[i] = 1 / len(probabilities)
        rule: List[Rule] = choice(rules, 1, p=probabilities)  # Returns a list (of size 1) of rules based on their probabilities

        return rule[0]  # Choice function returns an array, so we take the only element in it

    # RETURN A RULE FROM RSint BASED ON THEIR PROBABILITIES
    def selectCoopRule(self, validRules: List[Rule]) -> Union[Rule, Literal[-1]]:
        if len(validRules) == 0:
            return -1
        elif len(validRules) == 1:
            return validRules[0]

        rsMax, rsRest = self.subDivideValidRules(validRules)

        rules: List[Rule] = []
        probabilities: List[float] = []

        if len(rsMax) > 0:
            # Add a number of max weight rules to selection set relative to their probabilities
            for rule in rsMax:
                probability = int(self.getRuleProbabilityMax(rule, rsMax, rsRest))
                rules.append(rule)
                probabilities.append(probability)

        # If rsRest contains elements too, calculate their probabilities
        if len(rsRest) > 0:
            # Acquire sum of weights in rsRest
            sumOfWeights = self.getSumOfWeights(rsRest)

            # If sum of weights is 0, assign a weight based on the available probability left
            if sumOfWeights == 0:
                probability = (1 - sum(probabilities)) / len(rsRest)

                # If sum of weights is 0, assign equal part of the remaining probability to each rule
                for rule in rsRest:
                    rules.append(rule)
                    probabilities.append(probability)
            else:
                # If weights do not sum to 0, normalize them between 0 and 1 (0.1 and 1.1 technically) and calculate their probabilities
                weightsList = self.getWeightsList(rsRest)
                self.normalizeWeights(rsRest, weightsList)
                sumOfWeights = self.getSumOfWeights(self.getNormalizedWeightsList(rsRest))

                # Individually calculate probabilities
                for rule in rsRest:
                    probability = self.getRuleProbabilityRest(rule, probabilities, sumOfWeights, rsRest)
                    rules.append(rule)
                    probabilities.append(probability)

        # print("Probabilities have a sum of:", sum(probabilities))
        if sum(probabilities) == 0:
            for i in range(len(probabilities)):
                probabilities[i] = 1/len(probabilities)
        rule: List[Rule] = choice(rules, 1, p=probabilities)  # Returns a list (of size 1) of rules based on their probabilities

        return rule[0]  # Choice function returns an array, so we take the only element in it

    # RETURN AGENT POOL THE INDIVIDUAL BELONGS TO
    def getAgentPool(self):
        return self.agentPool

    # RETURN PROBABILITY OF SELECTION FOR A RULE IN rsMax
    def getRuleProbabilityMax(self, rule: Rule, rsMax: List[Rule], rsRest: List[Rule]) -> float:
        weight = rule.getWeight()

        if len(rsRest) == 0:
            return 1 / len(rsMax)

        # Avoid dividing by zero
        if weight == 0:
            weight = 2.2250738585072014e-308

        return ((1 - epsilon) * (weight / (weight * len(rsMax))))

    # RETURN PROBABILITY OF SELECTION FOR A RULE IN rsRest
    def getRuleProbabilityRest(self, rule: Rule, probabilities: List[int], sumOfWeights: float, rsRest: List[Rule]):
        weight = rule.getNormalizedWeight()

        return epsilon * (weight / sumOfWeights)

    # RETURN SUM OF ALL WEIGHTS IN A RULE SET
    def getSumOfWeights(self, setOfRules: List[Rule]) -> float:
        return sum(rule.getNormalizedWeight() for rule in setOfRules)

    # RETURN A LIST OF ALL WEIGHTS IN A LIST OF RULES
    def getWeightsList(self, setOfRules: List[Rule]) -> List[float]:
        weightsList: List[float] = []
        for r in setOfRules:
            weightsList.append(r.getWeight())

        return weightsList

    # RETURN A LIST OF WEIGHTS NORMALIZED BETWEEN 0.1 AND 1.1
    def getNormalizedWeightsList(self, setOfRules: List[Rule]) -> List[float]:
        weightsList: List[float] = []
        for r in setOfRules:
            weightsList.append(r.getNormalizedWeight())

        return weightsList

    # NORMALIZE WEIGHTS BETWEEN 0.1 AND 1.1 (WEIGHTS ARE NORMALIZED BETWEEN 0 AND 1, AND 0.1 IS ADDED TO AVOID WEIGHTS OF 0)
    def normalizeWeights(self, setOfRules: List[Rule], weightsList: List[float]):
        for r in setOfRules:
            r.setNormalizedWeight(((r.getWeight() - min(weightsList)) / (max(weightsList) - min(weightsList))) + 0.1)

    # SEPERATE RULES INTO rsMax AND rsRest
    def subDivideValidRules(self, validRules: List[Rule]) -> Tuple[List[Rule], List[Rule]]:
        rsMax: List[Rule] = []
        ruleWeights: List[float] = []

        # Add all the valid rule weights into a list to sort
        for rule in validRules:
            ruleWeights.append(rule.getWeight())

        ruleWeights.sort(reverse=True)  # Sort rule weights from highest to lowest

        # Add rules with highest weight into rsMax, and then remove them from primary list
        for rule in validRules:
            if rule.getWeight() == ruleWeights[0]:
                rsMax.append(rule)
                validRules.remove(rule)

        return (rsMax, validRules)  # Return the two rule sets (validRules now serves as rsRest)

    def updateFitnessPenalty(self, ruleApplied: bool, positiveRuleReward: float):
        # If no rule is applied, add a big penalty to the fitness
        if not ruleApplied:
            self.fitnessRuleApplicationPenalty += 30

        # If rule is applied but reward is negative, add a smaller penalty to the fitness
        elif not positiveRuleReward:
            self.fitnessRuleApplicationPenalty += 10
