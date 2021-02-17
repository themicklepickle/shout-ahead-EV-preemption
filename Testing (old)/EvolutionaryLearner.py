import os
import sys
import PredicateSet as PredicateSet
import CoopPredicateSet as CoopPredicateSet
import numpy.random as npr
import random

from Rule import Rule
from Individual import Individual
from random import randrange
from random import randint

    #  EVOLUTIONARY LEARNER ALGORITHM
# class EvolutionaryLearner:

    # Best runtime in seconds by the SUMO traffic light algorithm
global bestSUMORuntime
bestSUMORuntime = 1690
    # How many of the top individuals to breed for new generation
global numOfIndividualsToMutate
global percentOfLastGenerationBred
global maxNumOfMutations 

numOfIndividualsToMutate = 5
percentOfLastGenerationBred = .3
maxNumOfMutations = 1                   # maximum number of mutations to a rule


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

    # FITNESS FUNCTION FOR AN INDIVIDUAL AFTER ONE SIMULATION RUN/EPISODE
def rFit(individual, simTime, aggregateVehicleWaitTime):
        # If Individual's simulation time is less than the best time, its fitness is the difference between those two values
    if simTime < bestSUMORuntime:
        return simTime - bestSUMORuntime
    else:
        bestIndivAggregateVehWaitTime = individual.getAgentPool().getBestIndividualAggregateVehWaitTime()
        indivAggrVehWaitTime = individual.getAggregateVehicleWaitTime()

            # If Individual's simulation time is more than the best time, multiply it relative to how much worse it is
        if indivAggrVehWaitTime == bestIndivAggregateVehWaitTime:
            return bestIndivAggregateVehWaitTime

        elif indivAggrVehWaitTime - bestIndivAggregateVehWaitTime < bestIndivAggregateVehWaitTime*.1:
            return indivAggrVehWaitTime*10

        elif indivAggrVehWaitTime - bestIndivAggregateVehWaitTime < bestIndivAggregateVehWaitTime*.2:
            return indivAggrVehWaitTime*20

        elif indivAggrVehWaitTime - bestIndivAggregateVehWaitTime < bestIndivAggregateVehWaitTime*.3:
            return indivAggrVehWaitTime*30

        else:
            return indivAggrVehWaitTime*40

    # FITNESS FUNCTION FOR ONE GENERATION
def fit(simTime, agentPools):
    ruleWeights = getSumRuleWeights(agentPools)
    fit = runtimeFactor*(1/simTime) + ruleWeightFactor*(1-(1/ruleWeights))

    return fit

    # CREATES NEW GENERATION AFTER A SIMULATION RUN AND UPDATES AGENT POOLS' INDIVIDUAL SET WITH NEW GEN
def createNewGeneration(agentPools):
    print("Creating a new Generation.")
    for ap in agentPools:
        individuals = ap.getIndividualsSet()
        individuals.sort(key=lambda x: x.getFitness(), reverse = False)
        #individuals.len() # An error trip for the program to stop for testing

        lastIndex = int(len(individuals)*percentOfLastGenerationBred)
        newGeneration = individuals[0:lastIndex]
        numOfSurvivingIndividuals = len(newGeneration)

            # Create however many children possible to also leave room for max number of mutations
        for x in range((maxIndividuals-numOfSurvivingIndividuals)-numOfIndividualsToMutate):
            parent1 = chooseFirstParent(newGeneration)
            parent2 = chooseSecondParent(newGeneration, parent1)
            newGeneration.append(crossover(parent1, parent2))

            # Randomly mutate a random number of the children
        for i in range(numOfIndividualsToMutate):
            individualToMutate = newGeneration[randrange(0, len(newGeneration))]
            # Simulate deepcopy() without using deepcopy() because it is slooooow and mutate copied Individual
            newGeneration.append(mutate(Individual(individualToMutate.getID(), individualToMutate.getAgentPool(), individualToMutate.getRS(), individualToMutate.getRSint())))
        
        # Add first 
            # Lines 100 - 130 are file writing lines just for mid-simulation validation
        fileName = str(ap.getID())
        f = open(fileName, "w")
        f.write("New Generation includes these individuals and their rules.\n\n\n")

        individualCount = 1
        for i in newGeneration:
            ruleCount = 1
            f.write("Individual" + str(individualCount) + "has a fitness of " + str(i.getFitness()) + " and a last runtime of " + str(i.getLastRunTime()) + " and contains the following rules:\n\n")
            f.write("Rules in RS:\n")
            for rule in i.getRS():
                cond = ""
                for c in rule.getConditions():
                    cond += "," + c + " "

                f.write("\nRule" + str(ruleCount) + ": (" + str(rule) + ") <" + cond + ">, <" + str(rule.getAction()) + "> and rule has a weight of" + str(rule.getWeight()) + "\n\n")
                ruleCount += 1

            ruleCount = 1
            f.write("Rules in RSint:\n")
            for rule in i.getRSint():
                cond = ""
                for c in rule.getConditions():
                    cond += "," + c + " "

                f.write("\nRule" + str(ruleCount) + ": <" + cond + ">, <" + str(rule.getAction()) + "> and rule has a weight of" + str(rule.getWeight()) + "\n\n")
                ruleCount += 1

            f.write("-------------------\n\n")
            individualCount += 1

        f.write("\n*************END GENERATION*************\n\n\n")
        ap.updateIndividualsSet(newGeneration)

    # CREATE INDIVIDUALS WITH RANDOM RULES POPULATING THEIR RULE SETS BEFORE FIRST RUN
def initIndividuals(agentPool):
    individuals = []
    for x in range(maxIndividuals):
        RS = []     # RS is a rule set with no shout-ahead predicates
        RSint = []  # RSint is a rule set with shout-ahead predicates
            # Populate a rule set
        for i in range(maxRules):
            RS.append(createRandomRule(agentPool, 0))
            RSint.append(createRandomRule(agentPool, 1))

        individuals.append(Individual(x+1, agentPool, RS, RSint))

    return individuals

    # CREATE A RANDOM RULE USING RANDOM PREDICATES AND AN AGENT POOL RELATED ACTION
def createRandomRule(agentPool, ruleType):
    conditions = [] # Conditions for a rule

        # RS rule
    if ruleType == 0:
            # Set conditions of rules as a random amount of random predicates
        for i in range(randint(1, maxRulePredicates)):
            newCond = PredicateSet.getRandomPredicate()
            if checkValidCond(newCond, conditions):
                conditions.append(newCond)

        # RSint rule
    elif ruleType == 1:
            # Set conditions of rules as a random amount of random predicates
        for i in range(randint(1, maxRulePredicates)):
            newCond = agentPool.getRandomRSintPredicate()
            if checkValidCond(newCond, conditions):
                conditions.append(newCond)
                #print("Conditions set now contains", conditions, "\n\n")

        # Get index of possible action. SUMO changes phases on indexes
    action = randrange(0, len(agentPool.getActionSet()))     # Set rule action to a random action from ActionSet pertaining to Agent Pool being serviced
    if action == -1:    
        import pdb
        #print("Rule with action", action, "set.")
        pdb.set_trace()    #print("The action set is:", agentPool.getActionSet())
    rule = Rule(ruleType, conditions, action, agentPool)

    return rule

    # CREATE A CHILD RULE BY BREEDING TWO PARENT RULES
def crossover(indiv1, indiv2):
    identifier = str(indiv1.getID()) + "." + str(indiv2.getID())
    identifier = identifier[-4:] # Memory saving line
    agentPool = indiv1.getAgentPool()

    superRS = indiv1.getRS() + indiv2.getRS()
    superRS = removeDuplicateRules(superRS)    # Remove duplicate rules from set

    while len(superRS) < maxRulesInNewGenerationSet:
        superRS.append(createRandomRule(agentPool, 0))

    superRS.sort(key=lambda x: x.getWeight(), reverse = True)

    superRSint = indiv1.getRSint() + indiv2.getRSint()
    superRSint = removeDuplicateRules(superRSint)

    while len(superRSint) < maxRulesInNewGenerationSet:
        superRSint.append(createRandomRule(agentPool, 1))

    superRS.sort(key=lambda x: x.getWeight(), reverse = True)

    newRS = superRS[0:maxRules]
    newRSint = superRSint[0:maxRules]

    # counter = 1
    # for rule in newRS:
    #     print("Rule", counter, "contains conditions", rule.getConditions(), "and action", rule.getAction(), "\n\n")
    #     counter += 1

        # Ensure duplicate rules (with or without different weights) haven't been added to rule set. If they have, keep the one with the higher weight and mutate the other
    for rule in newRS:
        for r in newRS:
            if rule is not r:
                while set(rule.getConditions()) == set(r.getConditions()) and rule.getAction() == r.getAction():
                    if rule.getWeight() < r.getWeight():
                        # print("rule has less weight than r")
                        newRS.append(mutateRule(rule))
                        newRS.remove(rule)
                    else:
                        newRule = mutateRule(r)
                        newRS.append(mutateRule(r))
                        newRS.remove(r)

        # Ensure the same rule with different weights haven't been added to rule set. If they have, keep the one with the higher weight and mutate the other
    for rule in newRSint:
        for r in newRSint:
            if rule is not r:
                while set(rule.getConditions()) == set(r.getConditions()) and rule.getAction() == r.getAction():
                    if rule.getWeight() < r.getWeight():
                        # print("rule has less weight than r")
                        newRS.append(mutateRule(rule))
                        newRS.remove(rule)
                    else:
                        newRule = mutateRule(r)
                        newRS.append(mutateRule(r))
                        newRS.remove(r)

        # Both while loops below ensure the rule sets are not identical
    while ruleSetsAreDuplicate(newRS, indiv1.getRS()) or ruleSetsAreDuplicate(newRS, indiv2.getRS()):
        newRS.sort(key=lambda x: x.getWeight(), reverse = True)
        ruleToMutate = newRS[len(newRS)-1]
        newRS.append(mutateRule(ruleToMutate))
        newRS.remove(newRS[len(newRS)-2])

    while ruleSetsAreDuplicate(newRSint, indiv1.getRSint()) or ruleSetsAreDuplicate(newRSint, indiv2.getRSint()):
        # print("Indiv 1 compare is", ruleSetsAreDuplicate(newRSint, indiv1.getRSint()))
        # print('Indiv 2 compare is', ruleSetsAreDuplicate(newRSint, indiv2.getRSint()))
        # print("Rule set RSint is the same as parent's RSint")
        newRSint.sort(key=lambda x: x.getWeight(), reverse = True)
        ruleToMutate = newRS[len(newRSint)-1]
        newRSint.append(mutateRule(ruleToMutate))
        newRSint.remove(newRSint[len(newRSint)-2])

    newIndividual = Individual(identifier, agentPool, newRS, newRSint)

    # counter = 1
    # for rule in newIndividual.getRS():
    #     for r in newIndividual.getRS():
    #         print("Rule", counter, "is", rule, "and contains conditions", rule.getConditions(), "and action", rule.getAction(),"while r is", r, "and contains conditions", r.getConditions(), "and action", r.getAction())
    #         if rule is not r:
    #             print("The two rules are different.\nEqual conditions?", set(rule.getConditions()) == set(r.getConditions()), "\nEqual actions?", rule.getAction() == r.getAction(), "\n\n")
    #         counter += 1

    return newIndividual

def mutate(individual):
    chosenRule = individual.getRS()[randrange(0,len(individual.getRS()))]
    newRule = mutateRule(chosenRule)

    if newRule.getType() == 0:
        individual.getRS().append(newRule)
        individual.getRS().remove(chosenRule)
    else:
        individual.getRSint().append(newRule)
        individual.getRSint().remove(chosenRule)

    return individual

    # MUTATES A RULE A RANDOM NUMBER OF TIMES (MAX MUTATIONS IS USER-DEFINED)
def mutateRule(rule):
    ruleCond = rule.getConditions()
    #print("*Rule to be mutated has conditions:", rule.getConditions())
    #print('Mutating...')
        # Remove a random number of conditions and add a random number of random conditions
    for x in range(randint(1, maxNumOfMutations)):

        if len(ruleCond) == 1:
            numCondToRemove = 1
        else:
            numCondToRemove = randrange(1, len(ruleCond))

        for i in range(numCondToRemove):
            # print("Rule is of type", rule.getType(), "conds were", ruleCond)
            ruleCond.remove(ruleCond[randrange(len(ruleCond))])
            # print("Rule conds are NOW:", ruleCond)
            # #print("*Rule to be mutated has conditions:", rule.getConditions())

        numCondToAdd = randint(1, maxRulePredicates - len(ruleCond))
        #print("Num conds to add are", numCondToAdd)
            # If rule is from RS
        if rule.getType() == 0:
            #print("Adding conds to type 0")
            for i in range(numCondToAdd):
                newPredicate = PredicateSet.getRandomPredicate()
                #print("New predicate being added is:", newPredicate)
                    # If new random predicate is valid, append it to the conditions list
                if checkValidCond(newPredicate, ruleCond):
                    #print("New condition is valid and is being added! Old predicate set is:", ruleCond)
                    ruleCond.append(newPredicate)
                    #print("New predicate set is:", ruleCond)

            # If rule is from RSint
        elif rule.getType() == 1:
            for i in range(numCondToAdd):
                newPredicate = CoopPredicateSet.getRandomPredicate(rule.getAgentPool())
                    # If new random predicate is valid, append it to the conditions list
                if checkValidCond(newPredicate, ruleCond):
                    ruleCond.append(newPredicate)

    rule.setConditions(ruleCond) # set rule's new conditions
    rule.setAction(rule.getAgentPool().getActionSet()[randrange(0, len(rule.getAgentPool().getActionSet()))])
    rule.setWeight(0)
    # if rule.getAction() == -1:
    #     print("Rule has action -1!")
    #     print(x)
    return rule

    # RETURNS A PARENT TO BE BREED BASED ON FITNESS PROPOTIONAL SELECTION
def chooseFirstParent(breedingPopulation):
    totalFitness = sum([i.getNormalizedFitness() for i in breedingPopulation]) # Adjust fitnesses to benefit the smallest
    if totalFitness != 0:
        selection_probs = [i.getNormalizedFitness()/totalFitness for i in breedingPopulation]
        return breedingPopulation[npr.choice(len(breedingPopulation), p=selection_probs)]
    else:
        return random.choice(breedingPopulation)

    # RETURNS A PARENT TO BE BREED BASED ON FITNESS PROPOTIONAL SELECTION
def chooseSecondParent(breedingPopulation, parent1):
    adjustedPopulation = breedingPopulation.copy()
    adjustedPopulation.remove(parent1)
    totalFitness = sum([i.getNormalizedFitness() for i in adjustedPopulation])
    if totalFitness != 0:
        selection_probs = [i.getNormalizedFitness()/totalFitness for i in adjustedPopulation]
        return adjustedPopulation[npr.choice(len(adjustedPopulation), p=selection_probs)]
    else:
        return random.choice(breedingPopulation)


    # ENSURE UNIQUE PREDICATE TYPES IN CONDITIONS
def checkValidCond(cond, conditions):
    predicateType = cond.split("_")
    condPredicateTypes = []

    for x in conditions:
        predSplit = x.split("_")
        condPredicateTypes.append(predSplit[0])

    #print('New conditions is', predicateType[0], "and the conditions set is", condPredicateTypes)
        #If predicate type already exists in conditions, return false
    if predicateType[0] in condPredicateTypes:
       # print("Predicate type already exists in conditions set.")
        return False
    else:
        #print("Predicate type DOES NOT exist in conditions set.")
        return True

def removeDuplicateRules(ruleSet):
    for rule in ruleSet:
        for otherRule in ruleSet:
            if rulesAreDuplicate(rule, otherRule):
                ruleSet.remove(otherRule)
    return ruleSet

    # CHECK IF TWO RULES ARE DUPLICATES OF EACH OTHER
def rulesAreDuplicate(rule1, rule2):
    conds1 = rule1.getConditions()
    conds2 = rule2.getConditions()

    act1 = rule1.getAction()
    act2 = rule2.getAction()

    if rule1 is rule2 or (set(conds1) == set(conds2) and act1 == act2):
        return True
    else:
        return False

    # CHECK IF TWO RULE SETS ARE DUPLICATES OF EACH OTHER
def ruleSetsAreDuplicate(rs1, rs2):
    return set(rs1) == set(rs2)

    # RETURN SUM OF ALL WEIGHTS IN A RULE SET
def getSumRuleWeights(agentPools):
    weightSum = 0

    for ap in agentPools:
        individuals = ap.getIndividualsSet()
        # For each individual, sum all their rule weights
        for i in individuals:
            ruleSet = i.getRS()
            weightSum += sum(rule.getWeight() for rule in ruleSet)

    if weightSum == 0:
        weightSum = 2.2250738585072014e-308

    return weightSum

