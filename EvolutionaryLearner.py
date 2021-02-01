from __future__ import annotations

import numpy.random as npr
from random import randrange, randint, random, choice

import PredicateSet
import CoopPredicateSet
import EVPredicateSet
from Rule import Rule
from Individual import Individual

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Literal
    from AgentPool import AgentPool


# Best runtime in seconds by the SUMO traffic light algorithm
global bestSUMORuntime
bestSUMORuntime = 1690

# How many of the top individuals to breed for new generation
global numOfIndividualsToMutate
global percentOfLastGenerationBred
global maxNumOfMutations

numOfIndividualsToMutate = 0.1667
percentOfLastGenerationBred = .3
maxNumOfMutations = 1  # maximum number of mutations to a rule

# Specifications for making Individuals and Rules
global maxRulePredicates
global maxRules
global maxIndividuals
global newGenerationPoolSize

maxRulePredicates = 3
maxRules = 10
maxRulesInNewGenerationSet = 20
maxIndividuals = 30

# How much runtime and rule weights matter when determining fitness of a simulation run
global runtimeFactor
global ruleWeightFactor

runtimeFactor = 1
ruleWeightFactor = 1

# Specifications for making RSev
global EVPredicateProbability
global maxEVRules
global maxEVRulePredicates
global maxEVRulesInNewGenerationSet

EVPredicateProbability = 0.5  # The probability of choosing an EV predicate vs another one for RSev
maxEVRulePredicates = 6
maxEVRules = 30
maxEVRulesInNewGenerationSet = 60

# EV fitness parameters
global EVStopFitnessPenalty
global EVStopsFactor
global meanEVSpeedFactor

EVStopFitnessPenalty = -1  # Penalty applied to fitness for every EV stop
EVStopsFactor = 1
meanEVSpeedFactor = 10


def rFit(individual: Individual, simTime: int) -> float:
    """FITNESS FUNCTION FOR AN INDIVIDUAL AFTER ONE SIMULATION RUN/EPISODE"""
    # If Individual's simulation time is less than the best time, its fitness is the difference between those two values
    if simTime < bestSUMORuntime:
        fitness = simTime - bestSUMORuntime

        return fitness
    else:
        bestIndivAggregateVehWaitTime = individual.getAgentPool().getBestIndividualAggregateVehWaitTime()
        indivAggrVehWaitTime = individual.getAggregateVehicleWaitTime()

        fitness = 0

        # If Individual's simulation time is more than the best time, multiply it relative to how much worse it is
        if indivAggrVehWaitTime == bestIndivAggregateVehWaitTime:
            fitness += bestIndivAggregateVehWaitTime
        elif indivAggrVehWaitTime - bestIndivAggregateVehWaitTime < bestIndivAggregateVehWaitTime*.1:
            fitness += indivAggrVehWaitTime*10
        elif indivAggrVehWaitTime - bestIndivAggregateVehWaitTime < bestIndivAggregateVehWaitTime*.2:
            fitness += indivAggrVehWaitTime*20
        elif indivAggrVehWaitTime - bestIndivAggregateVehWaitTime < bestIndivAggregateVehWaitTime*.3:
            fitness += indivAggrVehWaitTime*30
        else:
            fitness += indivAggrVehWaitTime*40

        return fitness


def EVrFit(individual: Individual) -> float:
    """FITNESS FUNCTION FOR AN INDIVIDUAL AFTER ONE SIMULATION RUN/EPISODE FOR EV PARAMETERS"""
    fitness = 0

    print("mean EV speed:", individual.getMeanEVSpeed())
    print("EV stops:", individual.getEVStops())
    fitness += meanEVSpeedFactor * individual.getMeanEVSpeed()
    fitness += EVStopsFactor * (EVStopFitnessPenalty * individual.getEVStops())

    return fitness


def createNewGeneration(agentPools: List[AgentPool], folderName: str, generations: int):
    """CREATES NEW GENERATION AFTER A SIMULATION RUN AND UPDATES AGENT POOLS' INDIVIDUAL SET WITH NEW GEN"""
    print("Creating a new Generation.")
    for ap in agentPools:
        individuals = ap.getIndividualsSet()
        individuals.sort(key=lambda x: x.getFitness(), reverse=False)

        lastIndex = int(len(individuals)*percentOfLastGenerationBred)
        newGeneration = individuals[0:lastIndex]
        numOfSurvivingIndividuals = len(newGeneration)

        # Create however many children possible to also leave room for max number of mutations
        for _ in range(int((maxIndividuals-numOfSurvivingIndividuals)-numOfIndividualsToMutate)):
            parent1 = chooseFirstParent(newGeneration)
            parent2 = chooseSecondParent(newGeneration, parent1)
            newGeneration.append(crossover(parent1, parent2))

        # Randomly mutate a random number of the children
        for i in range(int(numOfIndividualsToMutate*len(newGeneration))):
            individualToMutate = newGeneration[randrange(0, len(newGeneration))]
            # Simulate deepcopy() without using deepcopy() because it is slooooow and mutate copied Individual
            newGeneration.append(mutate(Individual(individualToMutate.getID(), individualToMutate.getAgentPool(),
                                                   individualToMutate.getRS(), individualToMutate.getRSint(), individualToMutate.getRSev())))

        # Add first

        fileName = f"log/{folderName}/gen_{generations}/{ap.getID()}.txt"
        f = open(fileName, "w")
        f.write("New Generation includes these individuals and their rules.\n\n\n")

        individualCount = 1
        for i in newGeneration:
            f.write(f"Individual {individualCount}) has a fitness of {i.getFitness()} and a last runtime of {i.getLastRunTime()} and contains the following rules:\n\n")

            f.write("Rules in RS:\n")
            for rule in i.getRS():
                f.write(rule)

            f.write("Rules in RSint:\n")
            for rule in i.getRSint():
                f.write(rule)

            f.write("Rules in RSint:\n")
            for rule in i.getRSev():
                f.write(rule)

            f.write("-------------------\n\n")
            individualCount += 1

        f.write("\n*************END GENERATION*************\n\n\n")
        ap.updateIndividualsSet(newGeneration)


# CREATE INDIVIDUALS WITH RANDOM RULES POPULATING THEIR RULE SETS BEFORE FIRST RUN
def initIndividuals(agentPool: AgentPool):
    individuals: List[Individual] = []
    for x in range(maxIndividuals):
        RS: List[Rule] = []  # RS is a rule set with no shout-ahead predicates
        RSint: List[Rule] = []  # RSint is a rule set with shout-ahead predicates
        RSev: List[Rule] = []
        # Populate rule sets
        for _ in range(maxRules):
            RS.append(createRandomRule(agentPool, 0))
            RSint.append(createRandomRule(agentPool, 1))
        for _ in range(maxEVRules):
            RSev.append(createRandomRule(agentPool, 2))

        individuals.append(Individual(x+1, agentPool, RS, RSint, RSev))

    return individuals


# CREATE A RANDOM RULE USING RANDOM PREDICATES AND AN AGENT POOL RELATED ACTION
def createRandomRule(agentPool: AgentPool, ruleType: Literal[-1, 0, 1, 2]):
    conditions: List[str] = []  # Conditions for a rule

    # RS rule
    if ruleType == 0:
        # Set conditions of rules as a random amount of random predicates
        for _ in range(randint(1, maxRulePredicates)):
            newCond = PredicateSet.getRandomPredicate()
            if checkValidCond(newCond, conditions):
                conditions.append(newCond)

    # RSint rule
    elif ruleType == 1:
        # Set conditions of rules as a random amount of random predicates
        for _ in range(randint(1, maxRulePredicates)):
            newCond = agentPool.getRandomRSintPredicate()  # different from RS because RSint predicates are unique to each AP
            if checkValidCond(newCond, conditions):
                conditions.append(newCond)
                # print("Conditions set now contains", conditions, "\n\n")

    # RSev rule
    elif ruleType == 2:
        EVCondPicked: bool = False
        # Set conditions of rules as a random amount of random predicates
        for _ in range(randint(1, maxEVRulePredicates)):
            if random() < EVPredicateProbability:
                newCond = EVPredicateSet.getRandomPredicate(agentPool)
            else:
                newCond = PredicateSet.getRandomPredicate()
            if checkValidCond(newCond, conditions):
                conditions.append(newCond)
                if newCond in EVPredicateSet.getPredicateSet(agentPool):
                    EVCondPicked = True

        # Ensure that at least one of the conditions is relating to an EV
        if not EVCondPicked:
            if len(conditions) == maxEVRulePredicates:
                del conditions[randrange(len(conditions))]  # Remove an element if the max number of rule predicates has already been reached
            while True:
                newCond = EVPredicateSet.getRandomPredicate(agentPool)  # Pick a new predicate from the EV predicate set
                if checkValidCond(newCond, conditions):
                    conditions.append(newCond)  # Append the new condition and break out of the loop when a valid condition has been chosen
                    break

        # Add a lane predicate
        conditions.append(EVPredicateSet.getRandomLanePredicate(agentPool))

    # Get index of possible action. SUMO changes phases on indexes
    action = randrange(0, len(agentPool.getActionSet()))  # Set rule action to a random action from ActionSet pertaining to Agent Pool being serviced
    if action == -1:
        import pdb
        pdb.set_trace()  # print("The action set is:", agentPool.getActionSet())
    rule = Rule(ruleType, conditions, action, agentPool)

    return rule


# CREATE A CHILD RULE BY BREEDING TWO PARENT RULES
def crossover(indiv1: Individual, indiv2: Individual):
    identifier = str(indiv1.getID()) + "." + str(indiv2.getID())
    identifier = identifier[-4:]  # Memory saving line
    agentPool = indiv1.getAgentPool()

    # RS
    superRS = indiv1.getRS() + indiv2.getRS()
    superRS = removeDuplicateRules(superRS)  # Remove duplicate rules from set
    while len(superRS) < maxRulesInNewGenerationSet:
        superRS.append(createRandomRule(agentPool, 0))
    superRS.sort(key=lambda x: x.getWeight(), reverse=True)

    # RSint
    superRSint = indiv1.getRSint() + indiv2.getRSint()
    superRSint = removeDuplicateRules(superRSint)
    while len(superRSint) < maxRulesInNewGenerationSet:
        superRSint.append(createRandomRule(agentPool, 1))
    superRSint.sort(key=lambda x: x.getWeight(), reverse=True)  # yikes Christian

    # RSev
    superRSev = indiv1.getRSev() + indiv2.getRSev()
    superRSev = removeDuplicateRules(superRSev)
    while len(superRSev) < maxEVRulesInNewGenerationSet:
        superRSev.append(createRandomRule(agentPool, 1))
    superRSev.sort(key=lambda x: x.getWeight(), reverse=True)

    newRS = superRS[0:maxRules]
    newRSint = superRSint[0:maxRules]
    newRSev = superRSev[0:maxEVRules]

    # Ensure duplicate rules (with or without different weights) haven't been added to rule set. If they have, keep the one with the higher weight and mutate the other
    for rule in newRS:
        for r in newRS:
            if rule is not r:
                while set(rule.getConditions()) == set(r.getConditions()) and rule.getAction() == r.getAction():
                    if rule.getWeight() < r.getWeight():
                        newRS.append(mutateRule(rule, agentPool))
                        newRS.remove(rule)
                    else:
                        newRS.append(mutateRule(r, agentPool))
                        newRS.remove(r)

    # Ensure the same rule with different weights haven't been added to rule set. If they have, keep the one with the higher weight and mutate the other
    for rule in newRSint:
        for r in newRSint:
            if rule is not r:
                while set(rule.getConditions()) == set(r.getConditions()) and rule.getAction() == r.getAction():
                    if rule.getWeight() < r.getWeight():
                        newRS.append(mutateRule(rule, agentPool))
                        newRS.remove(rule)
                    else:
                        newRS.append(mutateRule(r, agentPool))
                        newRS.remove(r)

    # Ensure duplicate rules (with or without different weights) haven't been added to rule set. If they have, keep the one with the higher weight and mutate the other
    for rule in newRSev:
        for r in newRSev:
            if rule is not r:
                while set(rule.getConditions()) == set(r.getConditions()) and rule.getAction() == r.getAction():
                    if rule.getWeight() < r.getWeight():
                        newRS.append(mutateRule(rule, agentPool, agentPool))
                        newRS.remove(rule)
                    else:
                        newRS.append(mutateRule(r, agentPool))
                        newRS.remove(r)

    # All while loops below ensure the rule sets are not identical
    while ruleSetsAreDuplicate(newRS, indiv1.getRS()) or ruleSetsAreDuplicate(newRS, indiv2.getRS()):
        newRS.sort(key=lambda x: x.getWeight(), reverse=True)
        ruleToMutate = newRS[len(newRS)-1]
        newRS.append(mutateRule(ruleToMutate, agentPool))
        newRS.remove(newRS[len(newRS)-2])

    while ruleSetsAreDuplicate(newRSint, indiv1.getRSint()) or ruleSetsAreDuplicate(newRSint, indiv2.getRSint()):
        newRSint.sort(key=lambda x: x.getWeight(), reverse=True)
        ruleToMutate = newRS[len(newRSint)-1]
        newRSint.append(mutateRule(ruleToMutate, agentPool))
        newRSint.remove(newRSint[len(newRSint)-2])

    while ruleSetsAreDuplicate(newRSev, indiv1.getRSev()) or ruleSetsAreDuplicate(newRSev, indiv2.getRSev()):
        newRSev.sort(key=lambda x: x.getWeight(), reverse=True)
        ruleToMutate = newRSev[len(newRSev)-1]
        newRSev.append(mutateRule(ruleToMutate, agentPool))
        newRSev.remove(newRSev[len(newRSev)-2])

    newIndividual = Individual(identifier, agentPool, newRS, newRSint, newRSev)

    return newIndividual


def mutate(individual: Individual):
    # TODO: check why only RS rules are mutated????
    agentPool = individual.getAgentPool()
    # RS
    chosenRule = individual.getRS()[randrange(0, len(individual.getRS()))]
    newRule = mutateRule(chosenRule, agentPool)
    individual.getRS().append(newRule)
    individual.getRS().remove(chosenRule)

    # RSint
    chosenRule = individual.getRSint()[randrange(0, len(individual.getRSint()))]
    newRule = mutateRule(chosenRule, agentPool)
    individual.getRSint().append(newRule)
    individual.getRSint().remove(chosenRule)

    # RSev
    chosenRule = individual.getRSev()[randrange(0, len(individual.getRSev()))]
    newRule = mutateRule(chosenRule, agentPool)
    individual.getRSev().append(newRule)
    individual.getRSev().remove(chosenRule)

    return individual


# MUTATES A RULE A RANDOM NUMBER OF TIMES (MAX MUTATIONS IS USER-DEFINED)
def mutateRule(rule: Rule, agentPool: AgentPool):
    ruleCond = rule.getConditions()
    # Remove a random number of conditions and add a random number of random conditions
    for _ in range(randint(1, maxNumOfMutations)):

        if len(ruleCond) == 1:
            numCondToRemove = 1
        else:
            numCondToRemove = randrange(1, len(ruleCond))

        for _ in range(numCondToRemove):
            ruleCond.remove(ruleCond[randrange(len(ruleCond))])

        # If rule is from RS
        if rule.getType() == 0:
            numCondToAdd = randint(1, maxRulePredicates - len(ruleCond))
            for _ in range(numCondToAdd):
                newPredicate = PredicateSet.getRandomPredicate()
                # If new random predicate is valid, append it to the conditions list
                if checkValidCond(newPredicate, ruleCond):
                    ruleCond.append(newPredicate)

        # If rule is from RSint
        elif rule.getType() == 1:
            numCondToAdd = randint(1, maxRulePredicates - len(ruleCond))
            for _ in range(numCondToAdd):
                newPredicate = CoopPredicateSet.getRandomPredicate(rule.getAgentPool())
                # If new random predicate is valid, append it to the conditions list
                if checkValidCond(newPredicate, ruleCond):
                    ruleCond.append(newPredicate)

        # If rule is from RSev
        elif rule.getType() == 2:
            numCondToAdd = randint(1, maxEVRulePredicates - len(ruleCond))
            EVCondPicked = False
            for _ in range(numCondToAdd):
                if random() < EVPredicateProbability:
                    newPredicate = EVPredicateSet.getRandomPredicate(rule.getAgentPool())
                else:
                    newPredicate = PredicateSet.getRandomPredicate()
                # If new random predicate is valid, append it to the conditions list
                if checkValidCond(newPredicate, ruleCond):
                    ruleCond.append(newPredicate)
                    if newPredicate in EVPredicateSet.getPredicateSet(rule.getAgentPool()):
                        EVCondPicked = True

            # Ensure that at least one of the conditions is relating to an EV
            if not EVCondPicked:
                if len(ruleCond) == maxEVRulePredicates:
                    del ruleCond[randrange(len(ruleCond))]  # Remove an element if the max number of rule predicates has already been reached
                while True:
                    newPredicate = EVPredicateSet.getRandomPredicate(rule.getAgentPool())  # Pick a new predicate from the EV predicate set
                    if checkValidCond(newPredicate, ruleCond):
                        ruleCond.append(newPredicate)  # Append the new condition and break out of the loop when a valid condition has been chosen
                        break

            # Add a lane predicate
            ruleCond.append(EVPredicateSet.getRandomLanePredicate(agentPool))

    rule.setConditions(ruleCond)  # set rule's new conditions
    rule.setAction(rule.getAgentPool().getActionSet()[randrange(0, len(rule.getAgentPool().getActionSet()))])
    rule.setWeight(0)
    return rule


# RETURNS A PARENT TO BE BREED BASED ON FITNESS PROPOTIONAL SELECTION
def chooseFirstParent(breedingPopulation: List[Individual]):
    totalFitness = sum([i.getNormalizedFitness() for i in breedingPopulation])  # Adjust fitnesses to benefit the smallest
    if totalFitness != 0:
        selection_probs = [i.getNormalizedFitness()/totalFitness for i in breedingPopulation]
        return breedingPopulation[npr.choice(len(breedingPopulation), p=selection_probs)]
    else:
        return choice(breedingPopulation)


# RETURNS A PARENT TO BE BREED BASED ON FITNESS PROPOTIONAL SELECTION
def chooseSecondParent(breedingPopulation: List[Individual], parent1: Individual):
    adjustedPopulation = breedingPopulation.copy()
    adjustedPopulation.remove(parent1)
    totalFitness = sum([i.getNormalizedFitness() for i in adjustedPopulation])
    if totalFitness != 0:
        selection_probs = [i.getNormalizedFitness()/totalFitness for i in adjustedPopulation]
        return adjustedPopulation[npr.choice(len(adjustedPopulation), p=selection_probs)]
    else:
        return choice(breedingPopulation)


# ENSURE UNIQUE PREDICATE TYPES IN CONDITIONS
def checkValidCond(cond: str, conditions: List[str]):
    predicateType = cond.split("_")
    condPredicateTypes = []

    for x in conditions:
        predSplit = x.split("_")
        condPredicateTypes.append(predSplit[0])

    # If predicate type already exists in conditions, return false
    if predicateType[0] in condPredicateTypes:
        return False
    else:
        return True


def removeDuplicateRules(ruleSet: List[Rule]):
    for rule in ruleSet:
        for otherRule in ruleSet:
            if rulesAreDuplicate(rule, otherRule):
                ruleSet.remove(otherRule)
    return ruleSet


# CHECK IF TWO RULES ARE DUPLICATES OF EACH OTHER
def rulesAreDuplicate(rule1: Rule, rule2: Rule):
    conds1 = rule1.getConditions()
    conds2 = rule2.getConditions()

    act1 = rule1.getAction()
    act2 = rule2.getAction()

    if rule1 is rule2 or (set(conds1) == set(conds2) and act1 == act2):
        return True
    else:
        return False


# CHECK IF TWO RULE SETS ARE DUPLICATES OF EACH OTHER
def ruleSetsAreDuplicate(rs1: List[Rule], rs2: List[Rule]):
    return set(rs1) == set(rs2)


# RETURN SUM OF ALL WEIGHTS IN A RULE SET
def getSumRuleWeights(agentPools: List[AgentPool]) -> float:
    weightSum = 0

    for ap in agentPools:
        individuals = ap.getIndividualsSet()
        # For each individual, sum all their rule weights
        for i in individuals:
            weightSum += (sum(rule.getWeight() for rule in i.getRS()) + sum(rule.getWeight() for rule in i.getRSev)) / 2  # TODO: do something better than just average

    if weightSum == 0:
        weightSum = 2.2250738585072014e-308  # Smallest number besides 0 in Python

    return weightSum
