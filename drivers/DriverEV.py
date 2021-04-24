from __future__ import annotations

import traci

from drivers.Driver import Driver
import PredicateSet
import CoopPredicateSet
import EVPredicateSet
import EVCoopPredicateSet
from learning import EvolutionaryLearner
from learning import ReinforcementLearner
from network_components.EmergencyVehicle import EmergencyVehicle

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Dict, Union, Tuple, Literal
    from shout_ahead.Individual import Individual
    from network_components.TrafficLight import TrafficLight
    from shout_ahead.Rule import Rule
    from shout_ahead.Intention import Intention
    from shout_ahead.AgentPool import AgentPool

# NOTE: vehID in DriverEV.py refers to only the first element of the split, in Driver.py vehID was the split tuple


class DriverEV(Driver):

    def __init__(self,
                 sumoCmd: str,
                 setUpTuple: Tuple[List[Rule], List[TrafficLight], List[AgentPool]],
                 maxGreenPhaseTime: int, maxYellowPhaseTime: int, maxSimulationTime: int,
                 maxGreenAndYellow_UDRule: bool, maxRedPhaseTime_UDRule: bool, assignGreenPhaseToSingleWaitingPhase: bool,
                 useShoutahead: bool, ruleSetOptions: List[str]) -> None:
        self.sumoCmd = sumoCmd
        self.setUpTuple = setUpTuple
        self.maxGreenPhaseTime = maxGreenPhaseTime
        self.maxYellowPhaseTime = maxYellowPhaseTime
        self.maxSimulationTime = maxSimulationTime
        self.maxGreenAndYellow_UDRule = maxGreenAndYellow_UDRule
        self.maxRedPhaseTime_UDRule = maxRedPhaseTime_UDRule
        self.assignGreenPhaseToSingleWaitingPhase_UDRule = assignGreenPhaseToSingleWaitingPhase
        self.useShoutahead = useShoutahead
        self.ruleSetOptions = ruleSetOptions
        self.state = {}
        self.leadingEV = {}
        self.TLControllingLane = {}
        self.leftTurnLanes = []
        self.EVs = {}
        self.lastEVs = None
        self.vehicleWaitingTimes = {}
        self.vehicleSpeeds = {}
        self.timeSinceLastEVThrough = {}
        self.learnEVPreemption = ruleSetOptions[0] == "RSev" or ruleSetOptions[1] == "RSev_int"

    # CONTAINS MAIN TRACI SIMULATION LOOP
    def run(self) -> None:
        # results to be outputted
        self.EVStops = 0
        self.averageEVSpeedsList = []
        self.averageEVSpeed = 0
        self.simulationTime = 0
        self.totalFitness = 0

        ruleApplicationCounts = {
            self.ruleSetOptions[0]: 0,
            self.ruleSetOptions[1]: 0,
            "learned": 0,
        }

        # Start SUMO. Comment out if running Driver as standalone module.
        traci.start(self.sumoCmd)

        # Run set-up script and acquire list of user defined rules and traffic light agents in simulation
        userDefinedRules = self.setUpTuple[0]
        trafficLights = self.setUpTuple[1]
        rule: Union[Rule, Literal[-1]] = -1
        nextRule: Union[Rule, Literal[-1]] = -1

        # run functions to setup state
        self.constructTLControllingLaneDict(trafficLights)
        self.constructLeftTurnLanesList(trafficLights)
        self.constructTimeSinceLastEVThroughDict(trafficLights)

        # get state and EVs
        self.calculateState(trafficLights)
        self.calculateEVs(trafficLights)
        self.calculateLeadingEV(trafficLights)
        self.calculateTimeSinceLastEVThrough(trafficLights)

        # Assign each traffic light an individual from their agent pool for this simulation run, and a starting rule
        for tl in trafficLights:
            tl.assignIndividual()
            tl.updateCurrentPhase(traci.trafficlight.getPhaseName(tl.getName()))

            # Check user-defined rules
            rule = self.applicableUserDefinedRule(tl, userDefinedRules)
            if rule:
                self.applyUserDefinedRuleAction(tl, traci.trafficlight.getPhaseName(tl.getName()), rule)
                tl.resetTimeInCurrentPhase()
                tl.setCurrentRule(rule)
                tl.updateTimePhaseSpentInRed(traci.trafficlight.getPhase(tl.getName()), 5)
                continue

            # Check learning rules
            validRS, validRSint = self.getValidRules(tl, tl.getAssignedIndividual())
            rule = tl.getNextRule(validRS, validRSint, traci.simulation.getTime())
            if rule != -1 and not rule.hasDoNothingAction():
                traci.trafficlight.setPhase(tl.getName(), rule.getAction())
                tl.resetTimeInCurrentPhase()
                tl.setCurrentRule(rule)  # Set current rule in traffic light
                tl.updateTimePhaseSpentInRed(traci.trafficlight.getPhase(tl.getName()), 5)
                continue

            # Check learned rules
            validRS, validRSint = self.getValidLearnedRules(tl, tl.getAgentPool())
            rule = tl.getNextRule(validRS, validRSint, traci.simulation.getTime())
            if rule != -1 and not rule.hasDoNothingAction():
                traci.trafficlight.setPhase(tl.getName(), rule.getAction())
                tl.resetTimeInCurrentPhase()
                tl.setCurrentRule(rule)  # Set current rule in traffic light
                tl.updateTimePhaseSpentInRed(traci.trafficlight.getPhase(tl.getName()), 5)
                continue

            # Apply Do Nothing action if no rules were applicable
            tl.doNothing()  # Update traffic light's Do Nothing counter
            tl.getAssignedIndividual().updateFitnessPenalty(False, 0)  # Update fitness penalty for individual
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
            self.calculateTimeSinceLastEVThrough(trafficLights)

            for tl in trafficLights:
                self.EVStops += self.getNumEVStops(tl)
                self.averageEVSpeedsList.append(self.getAverageEVSpeed(tl))
                if len(self.averageEVSpeedsList) > 0:
                    self.averageEVSpeed = sum(self.averageEVSpeedsList) / len(self.averageEVSpeedsList)

                if self.checkUDRules(tl, nextRule):
                    continue

                tl.updateTimeInCurrentPhase(5)

                isEVApproaching = self.getIsEVApproaching(tl)

                # --- Check user-defined rules ---
                nextRule = self.applicableUserDefinedRule(tl, userDefinedRules)
                if nextRule:
                    self.applyUserDefinedRuleAction(tl, traci.trafficlight.getPhaseName(tl.getName()), nextRule)
                    tl.resetTimeInCurrentPhase()

                    self.checkUDRules(tl, nextRule)

                    self.updateValues(tl, isEVApproaching, nextRule, carsWaitingAfter)
                    continue

                # --- Check learning rules ---
                validRS, validRSint = self.getValidRules(tl, tl.getAssignedIndividual())
                nextRule = tl.getNextRule(validRS, validRSint, traci.simulation.getTime())
                if nextRule != -1:
                    # If applied rule isn't user-defined, update its weight
                    oldRule = tl.getCurrentRule()
                    if oldRule not in userDefinedRules and oldRule != -1:
                        carsWaitingBefore = tl.getCarsWaiting()
                        carsWaitingAfter = self.carsWaiting(tl)

                        # Get reinforcement learning parameters
                        EVChangeInSpeed, EVChangeInQueue, EVIsStopped = self.getEV_RLParameters(tl, isEVApproaching)

                        # Update the weight with EV parameters is there is an EV present and there was an EV present the previous step
                        oldRule.updateWeight(
                            ReinforcementLearner.updatedWeight(
                                oldRule,
                                nextRule,
                                self.getThroughputRatio(self.getThroughput(tl, carsWaitingBefore, carsWaitingAfter), len(carsWaitingBefore)),
                                self.getWaitTimeReducedRatio(self.getThroughputWaitingTime(tl, carsWaitingBefore, carsWaitingAfter), self.getTotalWaitingTime(carsWaitingBefore)),
                                len(carsWaitingAfter) - len(carsWaitingBefore),
                                EVChangeInSpeed,
                                EVChangeInQueue,
                                EVIsStopped
                            )
                        )

                        # Used to calculate fitness penalty to individual
                        ruleWeightBefore = oldRule.getWeight()
                        tl.getAssignedIndividual().updateFitnessPenalty(True, oldRule.getWeight() > ruleWeightBefore)

                    # Apply the next rule; if action is -1 then action is do nothing
                    if not nextRule.hasDoNothingAction() and nextRule is not tl.getCurrentRule():
                        traci.trafficlight.setPhase(tl.getName(), nextRule.getAction())
                        tl.resetTimeInCurrentPhase()

                        ruleApplicationCounts[nextRule.getType()] += 1

                        self.updateValues(tl, isEVApproaching, nextRule, carsWaitingAfter)
                        continue

                # --- Check learned rules ---
                validRS, validRSint = self.getValidLearnedRules(tl, tl.getAgentPool())
                nextRule = tl.getNextRule(validRS, validRSint, traci.simulation.getTime())
                if nextRule != -1 and not nextRule.hasDoNothingAction():  # TODO: check if this 'and' works, or if it needs to be two if statements
                    traci.trafficlight.setPhase(tl.getName(), nextRule.getAction())
                    tl.resetTimeInCurrentPhase()

                    ruleApplicationCounts[nextRule.getType()] += 1

                    self.updateValues(tl, isEVApproaching, nextRule, carsWaitingAfter)
                    continue

                # Apply Do Nothing action if no rules were applicable
                tl.doNothing()  # Update traffic light's Do Nothing counter
                tl.getAssignedIndividual().updateFitnessPenalty(False, False)  # Update fitness penalty for individual

                self.checkUDRules(tl, nextRule)

                self.updateValues(tl, isEVApproaching, nextRule, carsWaitingAfter)

        # Update the fitnesses of the individuals involved in the simulation based on their fitnesses
        simRunTime: float = traci.simulation.getTime()
        print(f"    *** SIMULATION TIME: {simRunTime} ***\n")
        print("    Total applied rules")
        for ruleType, count in ruleApplicationCounts.items():
            print(f"      {ruleType}: {count}")
        for tl in trafficLights:
            tl.resetRecievedIntentions()
            individual = tl.getAssignedIndividual()
            individual.updateLastRunTime(simRunTime)
            individual.updateFitness(
                EvolutionaryLearner.rFit(individual, simRunTime),
                EvolutionaryLearner.EVrFit(individual) if self.learnEVPreemption else 0
            )
            self.totalFitness += individual.getFitness()

        traci.close()  # End simulation

        self.simulationTime = simRunTime

        # Returns all the agent pools to the main module
        return self.setUpTuple[2], trafficLights

    def getEV_RLParameters(self, tl: TrafficLight, isEVApproaching: bool):
        leadingEV = None
        EVChangeInSpeed = None
        EVChangeInQueue = None
        EVIsStopped = False

        leadingEVBefore = tl.getLeadingEV()

        # Only evaluate EV parameters for the reinforcement learning if there is an EV this step and an EV the previous step
        if isEVApproaching and leadingEVBefore is not None and self.learnEVPreemption:
            leadingEV = self.getLeadingEV(tl)
            EVIsStopped: bool = leadingEV.getSpeed() == 0

            if leadingEVBefore.getID() == leadingEV.getID():
                EVChangeInSpeed = leadingEV.getSpeed() - leadingEVBefore.getSpeed()
                EVChangeInQueue = leadingEV.getQueue() - leadingEVBefore.getQueue()
            elif tl.existedBefore(leadingEV.getID()):
                leadingEVBefore = tl.getEV(leadingEV.getID())
                EVChangeInSpeed = leadingEV.getSpeed() - leadingEVBefore.getSpeed()
                EVChangeInQueue = leadingEV.getQueue() - leadingEVBefore.getQueue()

        return (EVChangeInSpeed, EVChangeInQueue, EVIsStopped)

    def updateValues(self, tl: TrafficLight, isEVApproaching: bool, nextRule: Rule | Literal[-1], carsWaitingAfter: Dict[str, float]):
        # Update evolutionary learning attributes if there is at least one EV approaching
        if isEVApproaching and self.learnEVPreemption:
            tl.getAssignedIndividual().updateAverageEVSpeed(self.getAverageEVSpeed(tl))
            tl.getAssignedIndividual().updateEVStops(self.getNumEVStops(tl))

        # Update traffic light
        tl.setCurrentRule(nextRule)
        tl.updateCarsWaiting(carsWaitingAfter)
        tl.setEVs(self.getEVs(tl))
        tl.setLeadingEV(self.getLeadingEV(tl))

    def checkUDRules(self, tl: TrafficLight, nextRule: Rule | Literal[-1]):
        if self.maxGreenAndYellow_UDRule:
            if self.checkMaxGreenAndYellowPhaseRule(tl, nextRule):
                return True
        if self.assignGreenPhaseToSingleWaitingPhase_UDRule:
            if self.checkAssignGreenPhaseToSingleWaitingPhaseRule(tl):
                return True
        if self.maxRedPhaseTime_UDRule:
            if self.checkMaxRedPhaseTimeRule(tl):
                return True
        return False

    def constructTLControllingLaneDict(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            for lane in tl.getLanes():
                self.TLControllingLane[lane] = tl

    def constructLeftTurnLanesList(self, trafficLights: List[TrafficLight]) -> None:
        maxLaneNum = 0
        for tl in trafficLights:
            for lane in tl.getLanes():
                if "_LTL" in lane:
                    if int(lane.split("_")[2]) > maxLaneNum:
                        self.leftTurnLanes.append(lane)

    def constructTimeSinceLastEVThroughDict(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            self.timeSinceLastEVThrough[tl.getName()] = -1

    def resetState(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            self.state[tl.getName()] = {}
            for lane in tl.getLanes():
                self.state[tl.getName()][lane] = []

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
            self.state[tl.getName()][laneID].append(vehID + identifer)

    def getState(self, trafficLight: TrafficLight) -> Dict[str, List[str]]:
        return self.state[trafficLight.getName()]

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
        if self.lastEVs is None:
            self.lastEVs = self.EVs
        else:
            self.lastEVs = {}
            for tlName, EVList in self.EVs.items():
                self.lastEVs[tlName] = list(EVList)

        for tl in trafficLights:
            state = self.getState(tl)
            self.EVs[tl.getName()] = []

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
                        self.EVs[tl.getName()].append(EmergencyVehicle(veh["name"], speed, distance, lane, i))

            self.EVs[tl.getName()].sort(key=lambda EV: EV.getDistance())

    # GET A LIST OF ALL EMERGENCY VEHICLES
    def getEVs(self, trafficLight: TrafficLight) -> List[EmergencyVehicle]:
        return self.EVs[trafficLight.getName()]

    def getLastEVs(self, trafficLight: TrafficLight) -> List[EmergencyVehicle]:
        return self.lastEVs[trafficLight.getName()]

    def calculateLeadingEV(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            EVs = self.getEVs(tl)

            if EVs == []:
                self.leadingEV[tl.getName()] = None
            else:
                self.leadingEV[tl.getName()] = EVs[0]

    # GET LEADING EMERGENCY VEHICLE AMONG ALL LANES
    def getLeadingEV(self, trafficLight: TrafficLight) -> EmergencyVehicle:
        return self.leadingEV[trafficLight.getName()]

    def getTimeSinceLastEVThrough(self, trafficLight: TrafficLight) -> int:
        return self.timeSinceLastEVThrough[trafficLight.getName()]

    def calculateTimeSinceLastEVThrough(self, trafficLights: List[TrafficLight]) -> None:
        for tl in trafficLights:
            EVs = self.getEVs(tl)
            lastEVs = self.getLastEVs(tl)

            diff = [EV for EV in lastEVs if not any(EV.getNumber() == i.getNumber() for i in EVs)]

            if len(diff) > 0:
                self.timeSinceLastEVThrough[tl.getName()] = 0
            elif self.timeSinceLastEVThrough[tl.getName()] != -1:
                self.timeSinceLastEVThrough[tl.getName()] += 5

#---------------------------------- EV PREDICATES END ----------------------------------#

#------------------------------ EV EVOLUTIONARY LEARNING -------------------------------#

    def getAverageEVSpeed(self, trafficLight: TrafficLight) -> List[int]:
        EVs = self.getEVs(trafficLight)
        EVSpeedsList = [EV.getSpeed() for EV in EVs]
        if EVSpeedsList == []:
            return 0
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

    def getValidLearnedRules(self, trafficLight: TrafficLight, agentPool: AgentPool) -> Tuple[List[Rule], List[Rule]]:
        validRS = []
        validRSint = []

        # Find valid RS rules
        for rule in agentPool.getRSlearned():
            if self.evaluateRule(trafficLight, rule):
                validRS.append(rule)

        # Find valid RSint rules
        if self.useShoutahead:
            for rule in agentPool.getRSlearned_int():
                if self.evaluateCoopRule(trafficLight, rule):
                    validRSint.append(rule)

        return (validRS, validRSint)

    def getValidRules(self, trafficLight: TrafficLight, individual: Individual) -> Tuple[List[Rule], List[Rule]]:
        validRS = []
        validRSint = []

        # Find valid RS rules
        for rule in individual.getRS():
            if self.evaluateRule(trafficLight, rule):
                validRS.append(rule)

        # Find valid RSint rules
        if self.useShoutahead:
            for rule in individual.getRSint():
                if self.evaluateCoopRule(trafficLight, rule):
                    validRSint.append(rule)

        return (validRS, validRSint)

    def evaluateRule(self, trafficLight: TrafficLight, rule: Rule) -> bool:
        # For each condition, its parameters are acquired and the condition predicate is evaluated
        for cond in rule.getConditions():
            predicate = cond.split("_")[0]

            # Construct predicate fuction call
            # predCall = getattr(PredicateSet, cond)(self.getPredicateParameters(trafficLight, predicate))
            if "leadingEVLane" == predicate:
                predCall = getattr(EVPredicateSet, "lanePredicate")(cond, self.getPredicateParameters(trafficLight, predicate))
            elif cond in rule.getAgentPool().getRSPredicates():
                predCall = getattr(PredicateSet, cond)(self.getPredicateParameters(trafficLight, predicate))
            elif cond in rule.getAgentPool().getRSevPredicates():
                predCall = getattr(EVPredicateSet, cond)(self.getPredicateParameters(trafficLight, predicate))
            else:
                raise Exception("Undefined condition:", cond)

            # Determine validity of predicate
            if predCall is False:
                return False

        return True  # if all predicates return true, evaluate rule as True

    def getCoopPredicateParameters(self, predicate: str, intention: Intention, condition: str) -> Union[int, Tuple[str, Intention]]:
        if "timeSinceCommunication" == predicate:
            timeSent = intention.getTime()
            return traci.simulation.getTime() - timeSent

        elif "intendedActionIs" == predicate:
            return (condition, intention.getAction())

        elif "timeSinceLastEVThrough" == predicate:
            partnerName = "_".join(condition.split("_")[1:-2])
            partnerTL = [tl for tl in self.setUpTuple[1] if tl.getName() == partnerName][0]
            return (condition, self.getTimeSinceLastEVThrough(partnerTL))

        elif "EVApproachingPartner" == predicate:
            partnerName = condition.split("_", 1)[1]
            partnerTL = [tl for tl in self.setUpTuple[1] if tl.getName() == partnerName][0]
            return partnerTL

        else:
            raise Exception("Undefined predicate:", predicate)

    def evaluateCoopRule(self, trafficLight: TrafficLight, rule: Rule) -> bool:
        intentions = trafficLight.getCommunicatedIntentions()

        for x in intentions:
            for i in intentions[x]:
                # For each condition, its parameters are acquired and the condition predicate is evaluated
                for cond in rule.getConditions():
                    predicate = cond.split("_")[0]

                    # Get parameters
                    if "partnerAction" == predicate:
                        parameters = [cond, i]
                    else:
                        parameters = self.getCoopPredicateParameters(predicate, i, cond)

                    # Construct predicate function call
                    if "EVApproachingPartner" == predicate:
                        predCall = self.getIsEVApproaching(parameters)
                    elif "timeSinceLastEVThrough" == predicate:
                        predCall = getattr(EVCoopPredicateSet, "timeSinceLastEVThrough")(*parameters)
                    elif "partnerAction" == predicate:
                        predCall = getattr(CoopPredicateSet, "partnerAction")(*parameters)
                    elif "intendedActionIs" == predicate:
                        predCall = getattr(CoopPredicateSet, "partnerAction")(*parameters)
                    else:
                        predCall = getattr(CoopPredicateSet, cond)(parameters)

                    # Determine validity of predicate
                    if predCall == False:
                        return False

        return True  # if all predicates return true, evaluate rule as True

    def getResults(self) -> Dict:
        return {
            "EVStops": self.EVStops,
            "averageEVSpeed": self.averageEVSpeed,
            "simulationTime": self.simulationTime,
            "totalFitness": self.totalFitness
        }
