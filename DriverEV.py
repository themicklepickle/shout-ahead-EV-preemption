from __future__ import annotations

import traci

from Driver import Driver
import PredicateSet
import EVPredicateSet
import EvolutionaryLearner
import ReinforcementLearner
from EmergencyVehicle import EmergencyVehicle

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Dict, Union, Tuple, Literal
    from Individual import Individual
    from TrafficLight import TrafficLight
    from Rule import Rule

# NOTE: vehID in DriverEV.py refers to only the first element of the split, in Driver.py vehID was the split tuple


class DriverEV(Driver):

    # CONTAINS MAIN TRACI SIMULATION LOOP
    def run(self) -> None:
        numOfRSRulesApplied: int = 0
        numOfRSintRulesApplied: int = 0
        numOfRSevRulesApplied: int = 0

        # Start SUMO. Comment out if running Driver as standalone module.
        traci.start(self.sumoCmd)

        # Run set-up script and acquire list of user defined rules and traffic light agents in simulation
        userDefinedRules = self.setUpTuple[0]
        trafficLights = self.setUpTuple[1]
        rule: Union[Rule, Literal[-1]] = -1
        nextRule: Union[Rule, Literal[-1]] = -1

        # Assign each traffic light an individual from their agent pool for this simulation run, and a starting rule
        for tl in trafficLights:
            tl.assignIndividual()
            tl.updateCurrentPhase(traci.trafficlight.getPhaseName(tl.getName()))

            rule = self.applicableUserDefinedRule(tl, userDefinedRules)  # Check user-defined rules

            # If no user-defined rules can be applied, get a rule from Agent Pool
            if rule == False or rule is None:
                # Determine if the rule should be chosen from RS or RSev
                isEVApproaching = self.getIsEVApproaching(tl)
                validRules = self.getValidRules(tl, tl.getAssignedIndividual())

                # Get a rule from assigned Individual
                rule = tl.getNextRule(validRules[0], validRules[1], validRules[2], isEVApproaching, traci.simulation.getTime())

                # if no valid rule applicable, apply the Do Nothing rule.
                if rule == -1:
                    tl.doNothing()  # Update traffic light's Do Nothing counter
                    tl.getAssignedIndividual().updateFitnessPenalty(False, 0)  # Update fitness penalty for individual

                else:
                    # If rule conditions are satisfied, apply its action. Otherwise, do nothing.
                    if not rule.hasDoNothingAction():
                        traci.trafficlight.setPhase(tl.getName(), rule.getAction())
                        tl.resetTimeInCurrentPhase()
            else:
                self.applyUserDefinedRuleAction(tl, traci.trafficlight.getPhaseName(tl.getName()), rule)
                tl.resetTimeInCurrentPhase()

            tl.setCurrentRule(rule)  # Set current rule in traffic light
            tl.updateTimePhaseSpentInRed(traci.trafficlight.getPhase(tl.getName()), 5)

        # Simulation loop
        step = 0

        # Variables for rule rewards
        carsWaitingBefore = {}
        carsWaitingAfter = {}

        while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < self.maxSimulationTime:

            tl.removeOldIntentions(traci.simulation.getTime())
            traci.simulationStep()  # Advance SUMO simulation one step (1 second)

            # Traffic Light agents reevaluate their state every 5 seconds
            step += 1
            if (step - 1) % 5 != 0:
                continue

            for tl in trafficLights:

                # USER DEFINED RULE CHECK
                # -------------------------------------------------------
                if self.assignGreenPhaseToSingleWaitingPhase_UDRule:
                    applied = self.checkAssignGreenPhaseToSingleWaitingPhaseRule(tl)
                    if applied is True:
                        continue

                if self.maxGreenAndYellow_UDRule:
                    applied = self.checkMaxGreenAndYellowPhaseRule(tl, nextRule)
                    if applied is True:
                        continue

                if self.maxRedPhaseTime_UDRule:
                    applied = self.checkMaxRedPhaseTimeRule(tl)
                    if applied is True:
                        continue

                # END USER DEFINED RULE CHECK
                # -------------------------------------------------------

                # Check if a user-defined rule can be applied
                nextRule = self.applicableUserDefinedRule(tl, userDefinedRules)

                # If no user-defined rules can be applied, get a rule from Agent Pool
                if nextRule:
                    self.applyUserDefinedRuleAction(tl, traci.trafficlight.getPhaseName(tl.getName()), nextRule)
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
                    # Update EV details within the TL itself
                    tl.setEVs(self.getEVs(tl))
                    tl.setLeadingEV(self.getLeadingEV(tl))
                    continue

                # No user-defined rule applied
                tl.updateTimeInCurrentPhase(5)

                carsWaitingBefore = tl.getCarsWaiting()
                carsWaitingAfter = self.carsWaiting(tl)

                isEVApproaching = self.getIsEVApproaching(tl)

                # Get EV reinforcement learning parameters
                if isEVApproaching:
                    leadingEVBefore = tl.getLeadingEV()

                    leadingEV = self.getLeadingEV(tl)
                    EVs = self.getEVs(tl)
                    EVIsStopped: bool = traci.vehicle.getWaitingTime(leadingEV.getID().split("_")[0]) > 0  # TODO: maybe do this with speed instead

                    # Only evaluate EV parameters for the reinforcement learning if there is an EV this step and an EV the previous step
                    if leadingEVBefore is None:
                        EVChangeInSpeed = None
                        EVChangeInTrafficDensity = None
                    elif leadingEVBefore.ID == leadingEV.getID():
                        EVChangeInSpeed = leadingEV.getSpeed() - leadingEVBefore.getSpeed()
                        EVChangeInTrafficDensity = leadingEV.getTrafficDensity() - leadingEVBefore.getTrafficDensity()
                    elif tl.existedBefore(leadingEV.getID()):
                        leadingEVBefore = tl.getEV(leadingEV.getID())
                        EVChangeInSpeed = leadingEV.getSpeed() - leadingEVBefore.getSpeed()
                        EVChangeInTrafficDensity = leadingEV.getTrafficDensity() - leadingEVBefore.getTrafficDensity()
                    else:
                        EVChangeInSpeed = None
                        EVChangeInTrafficDensity = None
                else:
                    leadingEV = None
                    EVs = None
                    EVChangeInSpeed = None
                    EVChangeInTrafficDensity = None
                    EVIsStopped = False

                # Determine if the rule should be chosen from RS or RSev
                validRules = self.getValidRules(tl, tl.getAssignedIndividual())

                if len(validRules[0]) == 0 and len(validRules[1]) == 0 and not isEVApproaching:
                    nextRule = -1  # -1 is used to represent "no valid next rule"
                elif len(validRules[2]) == 0 and len(validRules[1]) == 0 and isEVApproaching:
                    nextRule = -1  # -1 is used to represent "no valid next rule"
                else:
                    # Get a rule from assigned Individual
                    nextRule = tl.getNextRule(validRules[0], validRules[1], validRules[2], isEVApproaching, traci.simulation.getTime())

                if nextRule == -1:
                    tl.doNothing()  # Update traffic light's Do Nothing counter
                    tl.getAssignedIndividual().updateFitnessPenalty(False, False)  # Update fitness penalty for individual

                # If next rule is not a user-defined rule, update the weight of the last applied rule
                else:
                    oldRule = tl.getCurrentRule()
                    # If applied rule isn't user-defined, update its weight
                    if oldRule not in userDefinedRules:
                        if oldRule != -1:
                            # Used to calculate fitness penalty to individual
                            ruleWeightBefore = oldRule.getWeight()
                            # Update the weight with EV parameters is there is an EV present and there was an EV present the previous step
                            oldRule.updateWeight(
                                ReinforcementLearner.updatedWeight(
                                    oldRule,
                                    nextRule,
                                    self.getThroughputRatio(
                                        self.getThroughput(tl, carsWaitingBefore, carsWaitingAfter),
                                        len(carsWaitingBefore)
                                    ),
                                    self.getWaitTimeReducedRatio(
                                        self.getThroughputWaitingTime(tl, carsWaitingBefore, carsWaitingAfter),
                                        self.getTotalWaitingTime(carsWaitingBefore)
                                    ),
                                    len(carsWaitingAfter) - len(carsWaitingBefore),
                                    EVChangeInSpeed,
                                    EVChangeInTrafficDensity,
                                    EVIsStopped
                                )
                            )
                            tl.getAssignedIndividual().updateFitnessPenalty(True, oldRule.getWeight() > ruleWeightBefore)
                            tl.getAssignedIndividual().updateMeanEVSpeed(self.getEVSpeedsList(tl))
                            tl.getAssignedIndividual().updateEVStops(self.getNumEVStops(tl))

                        # Apply the next rule; if action is -1 then action is do nothing
                        if not nextRule.hasDoNothingAction():
                            traci.trafficlight.setPhase(tl.getName(), nextRule.getAction())

                            # change the phase if the action is different than the current action
                            if nextRule is not tl.getCurrentRule():
                                traci.trafficlight.setPhase(tl.getName(), nextRule.getAction())
                                tl.resetTimeInCurrentPhase()

                        if nextRule.getType() == 0:

                            numOfRSRulesApplied += 1
                        elif nextRule.getType() == 1:
                            numOfRSintRulesApplied += 1
                        elif nextRule.getType() == 2:
                            numOfRSevRulesApplied += 1

                # USER DEFINED RULE CHECK
                if self.maxGreenAndYellow_UDRule:
                    self.checkMaxGreenAndYellowPhaseRule(tl, nextRule)

                if self.assignGreenPhaseToSingleWaitingPhase_UDRule:
                    self.checkAssignGreenPhaseToSingleWaitingPhaseRule(tl)

                if self.maxRedPhaseTime_UDRule:
                    self.checkMaxRedPhaseTimeRule(tl)

                # Update attributes within the tl itself
                tl.setCurrentRule(nextRule)
                tl.updateCarsWaiting(carsWaitingAfter)
                tl.setEVs(EVs)
                tl.setLeadingEV(leadingEV)

        # Update the fitnesses of the individuals involved in the simulation based on their fitnesses
        simRunTime: float = traci.simulation.getTime()
        print(f"*** SIMULATION TIME: {simRunTime} ***\n")
        print("Total applied rules")
        print(f"  RS: {numOfRSRulesApplied}")
        print(f"  RSint: {numOfRSintRulesApplied}")
        print(f"  RSev: {numOfRSevRulesApplied}\n")
        for tl in trafficLights:
            tl.resetRecievedIntentions()
            individual = tl.getAssignedIndividual()
            individual.updateLastRunTime(simRunTime)
            individual.updateFitness(EvolutionaryLearner.rFit(individual, simRunTime), EvolutionaryLearner.EVrFit(individual))
        traci.close()  # End simulation

        # Returns all the agent pools to the main module
        return self.setUpTuple[2]

    def getState(self, trafficLight: TrafficLight) -> Dict[str, List[str]]:
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

#----------------------- EV PREDICATES AND REINFORCEMENT LEARNING ----------------------#

    # DETERMINE WHETHER OR NOT AN EMERGENCY VEHICLE IS APPROACHING
    def getIsEVApproaching(self, trafficLight: TrafficLight) -> bool:
        state = self.getState(trafficLight)
        for lane in state:
            for veh in state[lane]:
                if "_EV" in veh:
                    return True  # Return True if at least one vehicle was an EV

        return False  # Return False if no EVs were found

    # GET A LIST OF ALL EMERGENCY VEHICLES
    def getEVs(self, trafficLight: TrafficLight) -> List[EmergencyVehicle]:
        state = self.getState(trafficLight)
        EVs = []

        for lane in state:
            EVsInLane = []
            for veh in state[lane]:
                if "_EV" in veh:
                    vehID = veh.split("_")[0]
                    speed = traci.vehicle.getSpeed(vehID)
                    distance = traci.lane.getLength(lane) - traci.vehicle.getLanePosition(vehID)
                    EVsInLane.append(EmergencyVehicle(veh, speed, distance, lane))

            # Sort EVs based on their distance to the intersection
            EVsInLane.sort(key=lambda EV: EV.getDistance())

            # Obtain queue length ahead based on the vehicle's index in the list
            for i, EV in enumerate(EVsInLane):
                EV.setQueue(i)

            # Add EVs in lane to EV list
            EVs += EVsInLane

        EVs.sort(key=lambda EV: EV.getDistance())

        return EVs

    # GET LEADING EMERGENCY VEHICLE AMONG ALL LANES
    def getLeadingEV(self, trafficLight: TrafficLight) -> EmergencyVehicle:
        EVs = self.getEVs(trafficLight)

        if EVs == []:
            return None
        else:
            return EVs[0]
#---------------------------------- EV PREDICATES END ----------------------------------#


#------------------------------ EV EVOLUTIONARY LEARNING -------------------------------#

    def getEVSpeedsList(self, trafficLight: TrafficLight) -> List[int]:
        EVs = self.getEVs(trafficLight)
        EVSpeedsList = [EV.getSpeed() for EV in EVs]

        return EVSpeedsList

    def getNumEVStops(self, trafficLight: TrafficLight) -> int:
        EVs = self.getEVs(trafficLight)
        numEVStops = 0
        for EV in EVs:
            if traci.vehicle.getWaitingTime(EV.getID().split("_")[0]) > 0:
                numEVStops += 1

        return numEVStops
#---------------------------- EV EVOLUTIONARY LEARNING END -----------------------------#

    def getPredicateParameters(self, trafficLight: TrafficLight, predicate: str) -> Union[float, int, str, bool, List[str, float, int], List[str]]:
        if "longestTimeWaitedToProceedStraight" == predicate:
            # Find max wait time for relevant intersection
            maxWaitTime: float = 0
            # Retrieve state of specified intersection
            state = self.getState(trafficLight)
            for lane in state:
                if lane in trafficLight.getLanes():
                    for veh in state[lane]:
                        if "_Stopped_S" in veh:
                            vehIDSplit = veh.split("_")
                            vehID = vehIDSplit[0]
                            if traci.vehicle.getWaitingTime(vehID) > maxWaitTime:
                                maxWaitTime = traci.vehicle.getWaitingTime(vehID)
            return maxWaitTime

        elif "longestTimeWaitedToTurnLeft" == predicate:
            # Find max wait time for relevant intersection
            maxWaitTime: float = 0
            # Retrieve state of specified intersection
            state = self.getState(trafficLight)
            for lane in state:
                if lane in trafficLight.getLanes():
                    for veh in state[lane]:
                        if "_Stopped_L" in veh:
                            vehIDSplit = veh.split("_")
                            vehID = vehIDSplit[0]
                            if traci.vehicle.getWaitingTime(vehID) > maxWaitTime:
                                maxWaitTime = traci.vehicle.getWaitingTime(vehID)
            return maxWaitTime

        elif "numCarsWaitingToProceedStraight" == predicate:
            carsWaiting: int = 0
            # Retrieve state of specified intersection
            state = self.getState(trafficLight)
            for lane in state:
                if lane in trafficLight.getLanes():
                    for veh in state[lane]:
                        if "_Stopped_S" in veh:
                            vehIDSplit = veh.split("_")
                            vehID = vehIDSplit[0]
                            if traci.vehicle.getWaitingTime(vehID) > 0:
                                carsWaiting += 1
            return carsWaiting

        elif "numCarsWaitingToTurnLeft" == predicate:
            carsWaiting: int = 0
            # Retrieve state of specified intersection
            state = self.getState(trafficLight)
            for lane in state:
                if lane in trafficLight.getLanes():
                    for veh in state[lane]:
                        if "_Stopped_L" in veh:
                            vehIDSplit = veh.split("_")
                            vehID = vehIDSplit[0]
                            if traci.vehicle.getWaitingTime(vehID) > 0:
                                carsWaiting += 1

            return carsWaiting

        elif "timeSpentInCurrentPhase" == predicate:
            return traci.trafficlight.getPhaseDuration(trafficLight.getName())

        elif "verticalPhaseIs" in predicate or "horizontalPhaseIs" in predicate or "northSouthPhaseIs" in predicate or "southNorthPhaseIs" in predicate or "eastWestPhaseIs" in predicate or "westEastPhaseIs" in predicate:
            return traci.trafficlight.getPhaseName(trafficLight.getName()).split("_")

        elif "maxGreenPhaseTimeReached" == predicate:
            parameters: List[str, float, int] = []
            parameters.append(traci.trafficlight.getPhaseName(trafficLight.getName()))

            # Get phase (G or Y) from phase name
            getPhase = parameters[0].split("_")
            parameters[0] = getPhase[2]

            parameters.append(traci.trafficlight.getPhaseDuration(trafficLight.getName()) -
                              (traci.trafficlight.getNextSwitch(trafficLight.getName()) - traci.simulation.getTime()))
            parameters.append(self.maxGreenPhaseTime)

            return parameters

        elif "maxYellowPhaseTimeReached" == predicate:
            parameters = []
            parameters.append(traci.trafficlight.getPhaseName(trafficLight.getName()))  # Get traffic light phase name

            # Get phase (G or Y) from phase name
            getPhase = parameters[0].split("_")
            parameters[0] = getPhase[2]

            parameters.append(traci.trafficlight.getPhaseDuration(trafficLight.getName()) -
                              (traci.trafficlight.getNextSwitch(trafficLight.getName()) - traci.simulation.getTime()))
            parameters.append(self.maxYellowPhaseTime)

            return parameters

#------------------------------------ EV PREDICATES ------------------------------------#

        elif "isEVApproaching" == predicate:
            return self.getIsEVApproaching(trafficLight)

        elif "EVDistanceToIntersection" == predicate:
            leadingEV = self.getLeadingEV(trafficLight)
            return leadingEV.getDistance() if leadingEV is not None else -1

        elif "EVTrafficDensity" == predicate:
            leadingEV = self.getLeadingEV(trafficLight)
            return leadingEV.getTrafficDensity() if leadingEV is not None else -1

        elif "leadingEVLane" == predicate:
            leadingEV = self.getLeadingEV(trafficLight)
            return leadingEV.getLane() if leadingEV is not None else None

        else:
            raise Exception("Undefined predicate:", predicate)

#---------------------------------- EV PREDICATES END ----------------------------------#

    # RETURNS RULES THAT ARE APPLICABLE AT A GIVEN TIME AND STATE
    def getValidRules(self, trafficLight: TrafficLight, individual: Individual) -> Tuple[List[Rule], List[Rule], List[Rule]]:
        validRS = []
        validRSint = []
        validRSev = []

        # Find valid RS rules
        for rule in individual.getRS():
            if self.evaluateRule(trafficLight, rule):
                validRS.append(rule)

        # Find valid RSint rules
        for rule in individual.getRSint():
            if self.evaluateCoopRule(trafficLight, rule):
                validRSint.append(rule)

        # Find valid RSev rules
        for rule in individual.getRSev():
            if self.evaluateEVRule(trafficLight, rule):
                validRSev.append(rule)

        return (validRS, validRSint, validRSev)

    # EVALUATE RULE VALIDITY (fEval)
    def evaluateRule(self, trafficLight: TrafficLight, rule: Rule) -> bool:
        if rule.getType() == 1:
            return self.evaluateCoopRule(trafficLight, rule)
        if rule.getType() == 2:
            return self.evaluateEVRule(trafficLight, rule)

        # For each condition, its parameters are acquired and the condition predicate is evaluated
        for cond in rule.getConditions():
            predicate = cond.split("_")[0]

            # Construct predicate fuction call
            predCall = getattr(PredicateSet, cond)(self.getPredicateParameters(trafficLight, predicate))

            # Determine validity of predicate
            if predCall == False:
                return False

        return True  # if all predicates return true, evaluate rule as True

    def evaluateEVRule(self, trafficLight: TrafficLight, rule: Rule) -> bool:
        if rule.getType() == 0:
            return self.evaluateRule(trafficLight, rule)
        if rule.getType() == 1:
            return self.evaluateCoopRule(trafficLight, rule)

        for cond in rule.getConditions():
            predicate = cond.split("_")[0]

            if "leadingEVLane" == predicate:
                predCall = getattr(EVPredicateSet, "lanePredicate")(cond, self.getPredicateParameters(trafficLight, predicate))
            elif cond in PredicateSet.getPredicateList():
                predCall = getattr(PredicateSet, cond)(self.getPredicateParameters(trafficLight, predicate))
            elif cond in EVPredicateSet.getPredicateSet(trafficLight.getAgentPool()):
                predCall = getattr(EVPredicateSet, cond)(self.getPredicateParameters(trafficLight, predicate))
            else:
                raise Exception("Undefined condition:", cond)

            if predCall is False:
                return False

        return True
