from __future__ import annotations

import traci

from Driver import Driver
import PredicateSet
import CoopPredicateSet
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
    from Intention import Intention

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

        # run functions to setup state
        self.constructTLControllingLaneDict(trafficLights)
        self.constructLeftTurnLanesDict(trafficLights)

        # get state and EVs
        self.calculateState(trafficLights)
        self.calculateEVs(trafficLights)
        self.calculateLeadingEV(trafficLights)

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
            if step % 5 != 0:
                continue

            # get state and EVs
            self.calculateState(trafficLights)
            self.calculateEVs(trafficLights)
            self.calculateLeadingEV(trafficLights)

            for tl in trafficLights:

                # --- USER DEFINED RULE CHECK ---
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
                # -------------------------------

                tl.updateTimeInCurrentPhase(5)

                isEVApproaching = self.getIsEVApproaching(tl)

                # Check if a user-defined rule can be applied
                nextRule = self.applicableUserDefinedRule(tl, userDefinedRules)
                if nextRule:
                    self.applyUserDefinedRuleAction(tl, traci.trafficlight.getPhaseName(tl.getName()), nextRule)
                    tl.resetTimeInCurrentPhase()

                    # --- USER DEFINED RULE CHECK ---
                    if self.maxGreenAndYellow_UDRule:
                        self.checkMaxGreenAndYellowPhaseRule(tl, nextRule)

                    if self.assignGreenPhaseToSingleWaitingPhase_UDRule:
                        self.checkAssignGreenPhaseToSingleWaitingPhaseRule(tl)

                    if self.maxRedPhaseTime_UDRule:
                        self.checkMaxRedPhaseTimeRule(tl)
                    # -------------------------------

                    # update evolutionary learning attributes if there is at least one EV approaching
                    if isEVApproaching:
                        tl.getAssignedIndividual().updateAverageEVSpeed(self.getEVSpeedsList(tl))
                        tl.getAssignedIndividual().updateEVStops(self.getNumEVStops(tl))

                    # Update traffic light
                    tl.setCurrentRule(nextRule)
                    tl.updateCarsWaiting(carsWaitingAfter)
                    tl.setEVs(self.getEVs(tl))
                    tl.setLeadingEV(self.getLeadingEV(tl))
                    continue

                # If no user-defined rules can be applied, get a rule from Agent Pool
                carsWaitingBefore = tl.getCarsWaiting()
                carsWaitingAfter = self.carsWaiting(tl)

                # Get EV reinforcement learning parameters
                if isEVApproaching:
                    leadingEVBefore = tl.getLeadingEV()

                    leadingEV = self.getLeadingEV(tl)
                    EVs = self.getEVs(tl)
                    EVIsStopped: bool = leadingEV.getSpeed() == 0

                    # Only evaluate EV parameters for the reinforcement learning if there is an EV this step and an EV the previous step
                    if leadingEVBefore is None:
                        EVChangeInSpeed = None
                        EVChangeInQueue = None
                    elif leadingEVBefore.getID() == leadingEV.getID():
                        EVChangeInSpeed = leadingEV.getSpeed() - leadingEVBefore.getSpeed()
                        EVChangeInQueue = leadingEV.getQueue() - leadingEVBefore.getQueue()
                    elif tl.existedBefore(leadingEV.getID()):
                        leadingEVBefore = tl.getEV(leadingEV.getID())
                        EVChangeInSpeed = leadingEV.getSpeed() - leadingEVBefore.getSpeed()
                        EVChangeInQueue = leadingEV.getQueue() - leadingEVBefore.getQueue()
                    else:
                        EVChangeInSpeed = None
                        EVChangeInQueue = None
                else:
                    leadingEV = None
                    EVs = None
                    EVChangeInSpeed = None
                    EVChangeInQueue = None
                    EVIsStopped = False

                # Determine if the rule should be chosen from RS or RSev
                validRules = self.getValidRules(tl, tl.getAssignedIndividual())

                if len(validRules[0]) == 0 and len(validRules[1]) == 0 and not isEVApproaching:
                    nextRule = -1  # -1 is used to represent "no valid next rule"
                elif len(validRules[2]) == 0 and len(validRules[1]) == 0 and isEVApproaching:
                    nextRule = -1  # -1 is used to represent "no valid next rule"
                else:
                    nextRule = tl.getNextRule(validRules[0], validRules[1], validRules[2], isEVApproaching, traci.simulation.getTime())  # Get a rule from assigned Individual

                if nextRule == -1:
                    tl.doNothing()  # Update traffic light's Do Nothing counter
                    tl.getAssignedIndividual().updateFitnessPenalty(False, False)  # Update fitness penalty for individual

                # If next rule is not a user-defined rule, update the weight of the last applied rule
                else:
                    oldRule = tl.getCurrentRule()
                    # If applied rule isn't user-defined, update its weight
                    if oldRule not in userDefinedRules:
                        if oldRule != -1:
                            ruleWeightBefore = oldRule.getWeight()  # Used to calculate fitness penalty to individual

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
                                    EVChangeInQueue,
                                    EVIsStopped
                                )
                            )
                            tl.getAssignedIndividual().updateFitnessPenalty(True, oldRule.getWeight() > ruleWeightBefore)

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
                            # print(nextRule)
                            # print(oldRule)
                            # print()
                            numOfRSevRulesApplied += 1

                # --- USER DEFINED RULE CHECK ---
                if self.maxGreenAndYellow_UDRule:
                    self.checkMaxGreenAndYellowPhaseRule(tl, nextRule)

                if self.assignGreenPhaseToSingleWaitingPhase_UDRule:
                    self.checkAssignGreenPhaseToSingleWaitingPhaseRule(tl)

                if self.maxRedPhaseTime_UDRule:
                    self.checkMaxRedPhaseTimeRule(tl)
                # -------------------------------

                # update evolutionary learning attributes if there is at least one EV approaching
                if isEVApproaching:
                    tl.getAssignedIndividual().updateAverageEVSpeed(self.getAverageEVSpeed(tl))
                    tl.getAssignedIndividual().updateEVStops(self.getNumEVStops(tl))

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
            # print(tl.getName())
            # print([r for r in tl.getAssignedIndividual().getRSev() if r.getWeight() != 0])
        traci.close()  # End simulation

        # Returns all the agent pools to the main module
        return self.setUpTuple[2]

    def constructTLControllingLaneDict(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            for lane in tl.getLanes():
                self.TLControllingLane[lane] = tl

    def constructLeftTurnLanesDict(self, trafficLights: List[TrafficLight]) -> None:
        maxLaneNum = 0
        for tl in trafficLights:
            for lane in tl.getLanes():
                if "_LTL" in lane:
                    if int(lane.split("_")[2]) > maxLaneNum:
                        self.leftTurnLanes.append(lane)

    def resetState(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            self.state[tl] = {}
            for lane in tl.getLanes():
                self.state[tl][lane] = []

    def calculateState(self, trafficLights: List[TrafficLight]) -> None:
        self.resetState(trafficLights)

        # loop through all vehicles in simulation
        for vehID in traci.vehicle.getIDList():
            laneID = traci.vehicle.getLaneID(vehID)

            # ignore vehicles in lanes that are not controlled by traffic lights
            if laneID not in self.TLControllingLane:
                continue

            # store vehicle attributes
            self.vehicleWaitingTimes[vehID] = traci.vehicle.getWaitingTime(vehID)
            self.vehicleSpeeds[vehID] = traci.vehicle.getSpeed(vehID)

            # add appropriate identifier to vehicles
            identifer = ""

            # If vehicle is stopped, append relevant identifier to it
            if self.vehicleSpeeds[vehID] == 0:
                if laneID in self.leftTurnLanes:
                    identifer += "_Stopped_L"
                else:
                    identifer += "_Stopped_S"

            # If the vehicle is an EV, append relevant identifers to it
            # NOTE: EVs are not included in predicates for stopped vehicles, so the identifers are overidden (NOT TRUE ANYMORE)
            if traci.vehicle.getVehicleClass(vehID.split("_")[0]) == "emergency":
                if laneID in self.leftTurnLanes:
                    identifer += "_EV_L"
                else:
                    identifer += "_EV_S"

            tl = self.TLControllingLane[laneID]
            self.state[tl][laneID].append(vehID + identifer)

    def getState(self, trafficLight: TrafficLight) -> Dict[str, List[str]]:
        return self.state[trafficLight]

#----------------------- EV PREDICATES AND REINFORCEMENT LEARNING ----------------------#
    # DETERMINE WHETHER OR NOT AN EMERGENCY VEHICLE IS APPROACHING
    def getIsEVApproaching(self, trafficLight: TrafficLight) -> bool:
        state = self.getState(trafficLight)
        for lane in state:
            for veh in state[lane]:
                if "_EV" in veh:
                    return True  # Return True if at least one vehicle was an EV

        return False  # Return False if no EVs were found

    def calculateEVs(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            state = self.getState(tl)
            self.EVs[tl] = []

            for lane in state:
                vehicles = []
                for veh in state[lane]:
                    vehID = veh.split("_")[0]
                    vehicles.append({
                        "name": veh,
                        "distance": traci.lane.getLength(lane) - traci.vehicle.getLanePosition(vehID)
                    })

                # Sort vehicles based on their distance to the intersection
                vehicles.sort(key=lambda veh: veh["distance"])

                # Obtain queue length ahead based on the vehicle's index in the list
                for i, veh in enumerate(vehicles):
                    if "_EV" in veh["name"]:
                        vehID = veh["name"].split("_")[0]
                        speed = self.vehicleSpeeds[vehID]
                        distance = veh["distance"]
                        self.EVs[tl].append(EmergencyVehicle(veh["name"], speed, distance, lane, i))

            self.EVs[tl].sort(key=lambda EV: EV.getDistance())

    # GET A LIST OF ALL EMERGENCY VEHICLES
    def getEVs(self, trafficLight: TrafficLight) -> List[EmergencyVehicle]:
        return self.EVs[trafficLight]

    def calculateLeadingEV(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            EVs = self.getEVs(tl)

            if EVs == []:
                self.leadingEV[tl] = None
            else:
                self.leadingEV[tl] = EVs[0]

    # GET LEADING EMERGENCY VEHICLE AMONG ALL LANES
    def getLeadingEV(self, trafficLight: TrafficLight) -> EmergencyVehicle:
        return self.leadingEV[trafficLight]
#---------------------------------- EV PREDICATES END ----------------------------------#

#------------------------------ EV EVOLUTIONARY LEARNING -------------------------------#
    def getAverageEVSpeed(self, trafficLight: TrafficLight) -> List[int]:
        EVs = self.getEVs(trafficLight)
        EVSpeedsList = [EV.getSpeed() for EV in EVs]
        averageEVSpeed = sum(EVSpeedsList) / len(EVSpeedsList)

        return averageEVSpeed

    def getNumEVStops(self, trafficLight: TrafficLight) -> int:
        EVs = self.getEVs(trafficLight)
        numEVStops = 0
        for EV in EVs:
            if EV.getSpeed() == 0:
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
                            if self.vehicleWaitingTimes[vehID] > maxWaitTime:
                                maxWaitTime = self.vehicleWaitingTimes[vehID]
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
                            if self.vehicleWaitingTimes[vehID] > maxWaitTime:
                                maxWaitTime = self.vehicleWaitingTimes[vehID]
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
                            if self.vehicleWaitingTimes[vehID] > 0:
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
                            if self.vehicleWaitingTimes[vehID] > 0:
                                carsWaiting += 1

            return carsWaiting

        elif "timeSpentInCurrentPhase" == predicate:
            return traci.trafficlight.getPhaseDuration(trafficLight.getName())

        elif ("verticalPhaseIs" in predicate or
              "horizontalPhaseIs" in predicate or
              "northSouthPhaseIs" in predicate or
              "southNorthPhaseIs" in predicate or
              "eastWestPhaseIs" in predicate or
              "westEastPhaseIs" in predicate):
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

        if self.useShoutahead:
            # Find valid RSint rules
            for rule in individual.getRSint():
                if self.evaluateCoopRule(trafficLight, rule):
                    validRSint.append(rule)

        # TODO: add toggle for learning RSev and toggle for learning RS
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
            elif cond in rule.getAgentPool().getRSPredicates():
                predCall = getattr(PredicateSet, cond)(self.getPredicateParameters(trafficLight, predicate))
            elif cond in rule.getAgentPool().getRSevPredicates():
                predCall = getattr(EVPredicateSet, cond)(self.getPredicateParameters(trafficLight, predicate))
            else:
                raise Exception("Undefined condition:", cond)

            if predCall is False:
                return False

        return True

    # EVALUATE RULE VALIDITY (fEval)
    def evaluateCoopRule(self, trafficLight: TrafficLight, rule: Rule) -> bool:
        if rule.getType() == 0:
            return self.evaluateRule(trafficLight, rule)
        if rule.getType() == 2:
            return self.evaluateEVRule(trafficLight, rule)

        intentions = trafficLight.getCommunicatedIntentions()

        for x in intentions:
            for i in intentions[x]:
                # For each condition, its parameters are acquired and the condition predicate is evaluated
                for cond in rule.getConditions():
                    predicate = cond.split("_")[0]

                    if any(x.getName() == predicate for x in self.setUpTuple[1]):
                        parameters = [cond, i]
                    else:
                        parameters = self.getCoopPredicateParameters(trafficLight, predicate, i)

                    if isinstance(parameters, int) or isinstance(parameters, float) or isinstance(parameters, str):
                        predCall = getattr(CoopPredicateSet, cond)(parameters)  # Construct predicate fuction call
                    else:
                        # Construct predicate fuction call for custom predicates (they are of form TLname_action but are handled by the same predicate in CoopPredicateSet)
                        predCall = getattr(CoopPredicateSet, "customPredicate")(parameters[0], parameters[1])

                    # Determine validity of predicate
                    if predCall == False:
                        return False

        return True  # if all predicates return true, evaluate rule as True

    # PROVIDE SIMULATION RELEVANT PARAMETERS
    def getCoopPredicateParameters(self, trafficLight: TrafficLight, predicate: str, intention: Intention) -> Union[int, Tuple[str, Intention]]:
        if "timeSinceCommunication" == predicate:
            timeSent = intention.getTime()
            return traci.simulation.getTime() - timeSent
        elif "intendedActionIs" == predicate:
            return intention.getAction()
        elif "EVApproachingPartner" == predicate:
            partnerName = predicate.split("_", 1)[1]
            partnerTL = [tl for tl in self.setUpTuple[1] if tl.getName() == partnerName][0]
            return self.getIsEVApproaching(partnerTL)
        else:
            raise Exception("Undefined predicate:", predicate)
