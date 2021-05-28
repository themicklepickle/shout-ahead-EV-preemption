from __future__ import annotations

from numpy.random import choice

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Union, Literal, Tuple
    from shout_ahead.AgentPool import AgentPool
    from shout_ahead.Rule import Rule


class Individual:
    global epsilon  # paramater between 0 and 1 used to determine importance of doing exploration (higher epsilon = more exploration)
    epsilon = 0.5
    global defaultFitness
    defaultFitness = 10000.0

    # INTIALIZE OBJECT VARIABLES
    def __init__(self, identifier: str, agentPool: AgentPool, RS: List[Rule], RSint: List[Rule]) -> None:
        self.id = identifier
        self.RS = RS                                # Set of rules without observations of communicated intentions
        self.RSint = RSint                          # Set of rules with observations of communicated intentions
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
        self.averageEVSpeedsList: List[float] = []
        self.averageEVSpeed: float = 0
        self.EVStops: int = 0
        self.history = []

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
            "fitness": self.fitness,
            "agentPool": self.agentPool.getID(),
            "selectedCount": self.selectedCount,
            "totalSelectedCount": self.totalSelectedCount,
            "normalizedFitness": self.normalizedFitness,
            "lastRunTime": self.lastRunTime,
            "runFitnessResults": self.runFitnessResults,
        }

    def getID(self):
        return self.id

    def getRS(self):
        return self.RS

    def getRSint(self):
        return self.RSint

    def selected(self):
        self.selectedCount += 1
        self.totalSelectedCount += 1

    def resetSelectedCount(self):
        self.selectedCount = 0

    def getSelectedCount(self):
        return self.selectedCount

    def getTotalSelectedCount(self):
        return self.totalSelectedCount

    def getFitness(self):
        return self.fitness

    def getNegatedFitness(self):
        return self.fitness * -1

    def storeHistory(self):
        self.history.append({
            "fitnessRuleApplicationPenalty": self.fitnessRuleApplicationPenalty,
            "EVStops": self.EVStops,
            "averageEVSpeed": self.averageEVSpeed,
            "averageEVSpeedsList": self.averageEVSpeedsList,
        })

    def resetIndividual(self):
        # Reset values for next simulation run
        self.fitnessRuleApplicationPenalty = 0
        self.resetEVStops()
        self.resetAverageEVSpeed()

    def updateFitness(self, fitness: float, EVFitness: float):
        # Add run fitness plus rule application penalty minus EV fitness to master rFit list
        self.runFitnessResults.append(fitness + self.fitnessRuleApplicationPenalty - EVFitness)  # minus EV fitness cause we are trying to minimize fitness values

        # Reset values for next simulation run after storing them
        self.storeHistory()
        self.resetIndividual()

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

    def getLastRunTime(self):
        return self.lastRunTime

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
    def getAverageEVSpeed(self):
        return self.averageEVSpeed

    def updateAverageEVSpeed(self, averageEVSpeed: float):
        if averageEVSpeed is not None:
            self.averageEVSpeedsList.append(averageEVSpeed)
        if len(self.averageEVSpeedsList) > 0:
            self.averageEVSpeed = sum(self.averageEVSpeedsList) / len(self.averageEVSpeedsList)

    def resetAverageEVSpeed(self):
        self.averageEVSpeedsList = []
        self.averageEVSpeed = 0

    def getEVStops(self):
        return self.EVStops

    def updateEVStops(self, numEVStops: int):
        self.EVStops += numEVStops

    def resetEVStops(self):
        self.EVStops = 0
    # ----------- END ----------- #

    def getSumRuleWeights(self) -> float:
        ruleSet = self.getRS()
        self.ruleWeightSum = sum(rule.getWeight() for rule in ruleSet)

        return self.ruleWeightSum

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

    def getAgentPool(self):
        return self.agentPool

    def getRuleProbabilityMax(self, rule: Rule, rsMax: List[Rule], rsRest: List[Rule]) -> float:
        weight = rule.getWeight()

        if len(rsRest) == 0:
            return 1 / len(rsMax)

        # Avoid dividing by zero
        if weight == 0:
            weight = 2.2250738585072014e-308

        return ((1 - epsilon) * (weight / (weight * len(rsMax))))

    def getRuleProbabilityRest(self, rule: Rule, probabilities: List[int], sumOfWeights: float, rsRest: List[Rule]):
        weight = rule.getNormalizedWeight()

        return epsilon * (weight / sumOfWeights)

    def getSumOfWeights(self, setOfRules: List[Rule]) -> float:
        return sum(rule.getNormalizedWeight() for rule in setOfRules)

    def getWeightsList(self, setOfRules: List[Rule]) -> List[float]:
        weightsList: List[float] = []
        for r in setOfRules:
            weightsList.append(r.getWeight())

        return weightsList

    def getNormalizedWeightsList(self, setOfRules: List[Rule]) -> List[float]:
        weightsList: List[float] = []
        for r in setOfRules:
            weightsList.append(r.getNormalizedWeight())

        return weightsList

    def normalizeWeights(self, setOfRules: List[Rule], weightsList: List[float]):
        for r in setOfRules:
            r.setNormalizedWeight(((r.getWeight() - min(weightsList)) / (max(weightsList) - min(weightsList))) + 0.1)

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
