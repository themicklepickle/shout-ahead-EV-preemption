#!/usr/bin/env python

import os
import sys
import optparse
import traci

import PredicateSet
import CoopPredicateSet
import EvolutionaryLearner
import ReinforcementLearner
from Rule import Rule
from Intention import Intention
from Driver import Driver
import time
from pprint import pprint


# NOTE: vehID in DriverEV.py refers to only the first element of the split,
#       whereas in Driver.py vehID was the split tuple

class DriverEV(Driver):
    # CONTAINS MAIN TRACI SIMULATION LOOP
    def run(self):
        numOfRSRulesApplied = 0
        numofRSintRulesApplied = 0
        # Start SUMO. Comment out if running Driver as standalone module.
        traci.start(self.sumoCmd)

        # Run set-up script and acquire list of user defined rules and traffic light agents in simulation
        userDefinedRules = self.setUpTuple[0]
        trafficLights = self.setUpTuple[1]
        rule = -1
        nextRule = -1

        # Assign each traffic light an individual from their agent pool for this simulation run, and a starting rule
        for tl in trafficLights:
            tl.assignIndividual()
            tl.updateCurrentPhase(
                traci.trafficlight.getPhaseName(tl.getName()))

            rule = self.applicableUserDefinedRule(
                tl, userDefinedRules)  # Check user-defined rules

            # If no user-defined rules can be applied, get a rule from Agent Pool
            if rule == False or rule is None:
                validRules = self.getValidRules(tl, tl.getAssignedIndividual())
                # Get a rule from assigned Individual
                rule = tl.getNextRule(
                    validRules[0], validRules[1], traci.simulation.getTime())

                # if no valid rule applicable, apply the Do Nothing rule.
                if rule == -1:
                    tl.doNothing()  # Update traffic light's Do Nothing counter
                    tl.getAssignedIndividual().updateFitnessPenalty(
                        False, 0)   # Update fitness penalty for individual

                else:
                    # If rule conditions are satisfied, apply its action. Otherwise, do nothing.
                    if not rule.hasDoNothingAction():
                        traci.trafficlight.setPhase(
                            tl.getName(), rule.getAction())
                        tl.resetTimeInCurrentPhase()
            else:
                self.applyUserDefinedRuleAction(
                    tl, traci.trafficlight.getPhaseName(tl.getName()), rule)
                tl.resetTimeInCurrentPhase()

            tl.setCurrentRule(rule)  # Set current rule in traffic light
            tl.updateTimePhaseSpentInRed(
                traci.trafficlight.getPhase(tl.getName()), 5)

        # Simulation loop
        step = 0
        # Variables for rule rewards
        carsWaitingBefore = {}
        carsWaitingAfter = {}
        while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < self.maxSimulationTime:

            tl.removeOldIntentions(traci.simulation.getTime())
            traci.simulationStep()  # Advance SUMO simulation one step (1 second)

            # TODO: TESTING
            for tl in trafficLights:
                # if self.getIsEVApproaching(tl):
                print(str(tl))
                # pprint(self.getVehicleDict(tl))

                # pprint(self.getEVs(tl))

                # for lane in tl.getLanes():
                #     print(lane, end=": ")
                #     pprint(self.getLeadingEV(tl, lane))

                pprint(self.get)
                print()
            print("\n" + 80 * "—" + "\n\n")

            # Traffic Light agents reevaluate their state every 5 seconds
            if step % 5 == 0:
                # For every traffic light in simulation, select and evaluate new rule from its agent pool
                for tl in trafficLights:

                    # USER DEFINED RULE CHECK
                    # -------------------------------------------------------
                    if self.assignGreenPhaseToSingleWaitingPhase_UDRule:
                        applied = self.checkAssignGreenPhaseToSingleWaitingPhaseRule(
                            tl)
                        if applied is True:
                            continue
                    if self.maxGreenAndYellow_UDRule:
                        applied = self.checkMaxGreenAndYellowPhaseRule(
                            tl, nextRule)
                        if applied is True:
                            continue

                    if self.maxRedPhaseTime_UDRule:
                        applied = self.checkMaxRedPhaseTimeRule(tl)
                        if applied is True:
                            continue

                    # END USER DEFINED RULE CHECK
                    # -------------------------------------------------------

                    tl.updateTimeInCurrentPhase(5)

                    carsWaitingBefore = tl.getCarsWaiting()
                    carsWaitingAfter = self.carsWaiting(tl)

                    # Check if a user-defined rule can be applied
                    nextRule = self.applicableUserDefinedRule(
                        tl, userDefinedRules)

                    # If no user-defined rules can be applied, get a rule from Agent Pool
                    if nextRule == False:
                        validRules = self.getValidRules(
                            tl, tl.getAssignedIndividual())
                        # print("Valid rules for RS are",
                        #       validRules[0], "and valid rules for RSint are", validRules[1], "\n\n")

                        if len(validRules[0]) == 0 and len(validRules[1]) == 0:
                            nextRule = -1  # -1 is used to represent "no valid next rule"
                        else:
                            # Get a rule from assigned Individual
                            nextRule = tl.getNextRule(
                                validRules[0], validRules[1], traci.simulation.getTime())

                        if nextRule == -1:
                            tl.doNothing()  # Update traffic light's Do Nothing counter
                            tl.getAssignedIndividual().updateFitnessPenalty(
                                False, False)   # Update fitness penalty for individual

                            # If next rule is not a user-defined rule, update the weight of the last applied rule
                        else:
                            oldRule = tl.getCurrentRule()
                            # If applied rule isn't user-defined, update its weight
                            if oldRule not in userDefinedRules:
                                if oldRule != -1:
                                    # Used to calculate fitness penalty to individual
                                    ruleWeightBefore = oldRule.getWeight()
                                    oldRule.updateWeight(ReinforcementLearner.updatedWeight(oldRule, nextRule, self.getThroughputRatio(self.getThroughput(tl, carsWaitingBefore, carsWaitingAfter), len(carsWaitingBefore)), self.getWaitTimeReducedRatio(
                                        self.getThroughputWaitingTime(tl, carsWaitingBefore, carsWaitingAfter), self.getTotalWaitingTime(carsWaitingBefore)), len(carsWaitingAfter) - len(carsWaitingBefore)))
                                    tl.getAssignedIndividual().updateFitnessPenalty(
                                        True, oldRule.getWeight() > ruleWeightBefore)

                                    # Apply the next rule; if action is -1 then action is do nothing
                                if not nextRule.hasDoNothingAction():
                                    traci.trafficlight.setPhase(
                                        tl.getName(), nextRule.getAction())

                                    if nextRule is not tl.getCurrentRule():
                                        traci.trafficlight.setPhase(
                                            tl.getName(), nextRule.getAction())
                                        tl.resetTimeInCurrentPhase()

                                if nextRule.getType() == 0:
                                    # print("Applying TL action from RS! Action is",
                                    #       nextRule.getAction(), "\n\n")
                                    numOfRSRulesApplied += 1
                                else:
                                    # print(
                                    #     "Applying TL action from RSint! Action is", nextRule.getAction(), "\n\n")
                                    numofRSintRulesApplied += 1
                    else:
                        self.applyUserDefinedRuleAction(
                            tl, traci.trafficlight.getPhaseName(tl.getName()), nextRule)
                        tl.resetTimeInCurrentPhase()

                        # USER DEFINED RULE CHECK
                    if self.maxGreenAndYellow_UDRule:
                        self.checkMaxGreenAndYellowPhaseRule(tl, nextRule)

                    if self.assignGreenPhaseToSingleWaitingPhase_UDRule:
                        self.checkAssignGreenPhaseToSingleWaitingPhaseRule(tl)

                    if self.maxRedPhaseTime_UDRule:
                        self.checkMaxRedPhaseTimeRule(tl)

                    # Update the currently applied rule in the traffic light
                    tl.setCurrentRule(nextRule)
                    # Set the number of cars waiting count within the TL itself
                    tl.updateCarsWaiting(carsWaitingAfter)

            step += 1  # Increment step in line with simulator

            # Update the fitnesses of the individuals involved in the simulation based on their fitnesses
        simRunTime = traci.simulation.getTime()
        # print("***SIMULATION TIME:", simRunTime, "\n\n")
        for tl in trafficLights:
            tl.resetRecievedIntentions()
            i = tl.getAssignedIndividual()
            i.updateLastRunTime(simRunTime)
            # print("Individual", i, "has a last runtime of", i.getLastRunTime())
            i.updateFitness(EvolutionaryLearner.rFit(
                i, simRunTime, i.getAggregateVehicleWaitTime()))
            # print(tl.getName(), "'s coop rules were invalid",
            #       tl.getCoopRuleValidRate(), "percent of the time.")
            # print(tl.getName(), "'s RS rules were invalid",
            #       tl.getRSRuleValidRate(), "percent of the time.")
            # print("\n\nA total of", numOfRSRulesApplied, "rules from RS were applied and",
            #       numofRSintRulesApplied, "rules from RSint were applied.")
        traci.close()       # End simulation

        # Returns all the agent pools to the main module
        return self.setUpTuple[2]
        sys.stdout.flush()

    def getState(self, trafficLight):
        state = {}
        leftTurnLane = ""
        for lane in trafficLight.getLanes():
            state[lane] = []

        # Loop to determine which vehicles are waiting at an intersection
        for vehID in traci.vehicle.getIDList():
            laneID = traci.vehicle.getLaneID(vehID)
            tlLanes = trafficLight.getLanes()
            identifer = ""

            # Operate only on vehicles in a lane controlled by traffic light
            if laneID in tlLanes:
                # Determine left turn lane if it exists
                if "_LTL" in laneID:
                    maxLaneNum = 0
                    for lane in tlLanes:
                        if lane == laneID:
                            laneSplit = lane.split("_")
                            if int(laneSplit[2]) > maxLaneNum:
                                leftTurnLane = lane

                # If vehicle is stopped, append relevant identifier to it
                if traci.vehicle.getSpeed(vehID) == 0:
                    if leftTurnLane == laneID:
                        identifer += "_Stopped_L"
                    else:
                        identifer += "_Stopped_S"

#------------------------------------ EV IDENTIFIER ------------------------------------#
                # If the vehicle is an EV, append relevant identifers to it
                # NOTE: EVs are not included in predicates for stopped vehicles, so the identifers are overidden
                if traci.vehicle.getVehicleClass(vehID.split("_")[0]) == "emergency":
                    if leftTurnLane == laneID:
                        identifer += "_EV_L"
                    else:
                        identifer += "_EV_S"  # TODO: change to the same as other predicates?

#---------------------------------- EV IDENTIFIER END ----------------------------------#

                state[laneID].append(vehID + identifer)

        return state

                        if "_Stopped_L" in veh:
                            vehIDSplit = veh.split("_")
                        if "_Stopped_S" in veh:
                            vehIDSplit = veh.split("_")
