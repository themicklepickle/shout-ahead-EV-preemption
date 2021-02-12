from __future__ import annotations

import traci

import PredicateSet
import CoopPredicateSet

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Union, Dict, List, Tuple
    from AgentPool import AgentPool
    from TrafficLight import TrafficLight
    from Intention import Intention
    from Rule import Rule


class Driver:

    def __init__(self,
                 sumoCmd: str,
                 setUpTuple: Tuple[List[Rule], List[TrafficLight], List[AgentPool]],
                 maxGreenPhaseTime: int, maxYellowPhaseTime: int, maxSimulationTime: int,
                 maxGreenAndYellow_UDRule: bool, maxRedPhaseTime_UDRule: bool, assignGreenPhaseToSingleWaitingPhase: bool,
                 useShoutahead: bool) -> None:
        self.sumoCmd = sumoCmd
        self.setUpTuple = setUpTuple
        self.maxGreenPhaseTime = maxGreenPhaseTime
        self.maxYellowPhaseTime = maxYellowPhaseTime
        self.maxSimulationTime = maxSimulationTime
        self.maxGreenAndYellow_UDRule = maxGreenAndYellow_UDRule
        self.maxRedPhaseTime_UDRule = maxRedPhaseTime_UDRule
        self.assignGreenPhaseToSingleWaitingPhase_UDRule = assignGreenPhaseToSingleWaitingPhase
        self.useShoutahead = useShoutahead
        self.state = {}
        self.leadingEV = {}
        self.TLControllingLane = {}
        self.leftTurnLanes = []
        self.EVs = {}

    # RETURNS A DICTIONARY WITH KEYS OF VEHIDs WAITING AT AN INTERSECTION AND THEIR WAITING TIME AS VALUES
    def carsWaiting(self, trafficLight: TrafficLight) -> Dict[str, float]:
        state = self.getState(trafficLight)
        carsWaiting = {}
        # Count all vehicles in the state dictionary
        for lanes in state:
            for veh in state[lanes]:
                vehID = veh.split("_")
                carsWaiting[vehID[0]] = traci.vehicle.getAccumulatedWaitingTime(vehID[0])

        return carsWaiting

    # RETURNS NUMBER OF CARS WAITING AT AN INTERSECTION
    def carsWaitingCount(self, trafficLight: TrafficLight) -> int:
        state = self.getState(trafficLight)  # TODO: save state so this doesn't need to be repeatedly called
        carsWaiting = 0
        # Count all vehicles in the state dictionary
        for lanes in state:
            carsWaiting += len(state[lanes])

        return carsWaiting

    # RETURNS NORMALIZED THROUGHPUT BY DIVIDING THE THROUGHPUT BY THE TOTAL VEHICLES AT AN INTERSECTION
    def getThroughputRatio(self, throughput: int, totalCarsWaiting: int) -> float:
        if totalCarsWaiting == 0:
            return throughput
        else:
            return throughput / totalCarsWaiting

    # RETURNS THROUGHPUT OF AN INTERSECTION BASED ON VEHICLES WAITING BEFORE AND AFTER A GIVEN TIME
    def getThroughput(self, trafficLight: TrafficLight, carsWaitingBefore: Dict[str, float], carsWaitingAfter: Dict[str, float]) -> int:
        if not carsWaitingBefore:
            return 0
        elif not carsWaitingAfter:
            return len(carsWaitingBefore)
        else:
            carsThrough = {k: carsWaitingBefore[k] for k in set(carsWaitingBefore) - set(carsWaitingAfter)}
            return len(carsThrough)

    # RETURNS THE AGGREGATE WAITING TIME OF CARS THAT HAVE GONE THROUGH THE INTERSECTION AT A GIVEN TIME
    def getThroughputWaitingTime(self, trafficLight: TrafficLight, carsWaitingBefore: Dict[str, float], carsWaitingAfter: Dict[str, float]) -> float:
        carsThrough = {k: carsWaitingBefore[k] for k in set(carsWaitingBefore) - set(carsWaitingAfter)}

        # Update the relevant individual's aggregate vehicle wait time and return the throughput waiting time
        trafficLight.getAssignedIndividual().updateAggregateVehicleWaitTime(sum(carsThrough.values()))
        return sum(carsThrough.values())

    # RETURNS TOTAL WAIT TIME AT AN INTERSECTION AT A GIVEN TIME
    def getWaitingTime(self, trafficLight: TrafficLight) -> float:
        waitTime = 0
        # Sum waiting time of each edge controlled by the traffic light
        for edge in trafficLight.getEdges():
            waitTime += traci.edge.getWaitingTime(edge)

        return waitTime

    # RETURNS TOTAL WAITING TIME OF A DICTIONARY OF VEHICLES WAITING AT AN INTERSECTION
    def getTotalWaitingTime(self, listOfVehicles: List[Dict[str, float]]) -> float:
        return sum(listOfVehicles.values())

    # RETURNS NORMALIZED WAIT TIME REDUCED BY DIVIDING THE WAIT TIMES OF THROUGHPUT VEHICLES BY THE TOTAL WAIT TIME AT AN INTERSECTION
    def getWaitTimeReducedRatio(self, throughputWaitTime: float, totalWaitTime: float):
        if totalWaitTime == 0:
            return 1
        else:
            return throughputWaitTime / totalWaitTime

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
                        parameters = self.getCoopPredicateParameters(
                            trafficLight, predicate, i)

                    if isinstance(parameters, int) or isinstance(parameters, float) or isinstance(parameters, str):
                        predCall = getattr(CoopPredicateSet, cond)(parameters)  # Construct predicate fuction call
                    else:
                        # Construct predicate fuction call for custom predicates (they are of form TLname_action but are handled by the same predicate in CoopPredicateSet)
                        predCall = getattr(CoopPredicateSet, "customPredicate")(parameters[0], parameters[1])

                    # Determine validity of predicate
                    if predCall == False:
                        return False

        return True  # if all predicates return true, evaluate rule as True

    # DETERMINE IF ANY USER DEFINED RULES ARE APPLICABLE
    def applicableUserDefinedRule(self, trafficLight: TrafficLight, userDefinedRules: List[Rule]) -> Union[Rule, bool]:
        # Evaluate each user define rule
        for rule in userDefinedRules:
            # For each rule, its parameters are acquired and the condition predicate is evaluated
            for cond in rule.getConditions():
                parameters = self.getPredicateParameters(trafficLight, cond)
                predCall = getattr(PredicateSet, cond)(parameters[0], parameters[1], parameters[2])  # Construct predicate fuction call

                # Determine validity of predicate
                if predCall == True:
                    return rule

        return False  # if no user-defined predicates are applicable, return False

    # APPLIES USER DEFINED ACTIONS
    def applyUserDefinedRuleAction(self, trafficLight: TrafficLight, currPhaseName: str, rule: Rule) -> None:
        # If max green phase time reached, switch phase to yellow in same direction
        if rule.getConditions()[0] == "maxGreenPhaseTimeReached":
            currPhase = traci.trafficlight.getPhaseName(trafficLight.getName())
            currPhase[5] = "Y"
            traci.trafficlight.setPhase(trafficLight.getName(), currPhase)

        # If max yellow phase time reached, switch to next phase in the schedule
        elif rule.getConditions()[0] == "maxYellowPhaseTimeReached":
            if traci.trafficlight.getPhase(trafficLight.getName()) >= (len(trafficLight.getPhases()) - 2):
                traci.trafficlight.setPhase(trafficLight.getName(), 0)
            else:
                traci.trafficlight.setPhase(trafficLight.getName(), traci.trafficlight.getPhase(trafficLight.getName()) + 1)

    # PROVIDE SIMULATION RELEVANT PARAMETERS
    def getCoopPredicateParameters(self, trafficLight: TrafficLight, predicate: str, intention: Intention) -> Union[int, Tuple[str, Intention]]:
        if "timeSinceCommunication" == predicate:
            timeSent = intention.getTime()
            return traci.simulation.getTime() - timeSent

        elif "intendedActionIs" == predicate:
            return intention.getAction()

        else:       # equivalent to: elif "customPredicate" == predicate:
            return (str(intention.getTrafficLight().getName()) + "_" + intention.getAction(), intention)

# ------------------USER DEFINED RULE FUNCTIONS -------------------

    # MAX GREEN OR YELLOW PHASE REACHED UD RULE
    def checkMaxGreenAndYellowPhaseRule(self, tl: TrafficLight, nextRule: Rule) -> bool:
        if "G" in traci.trafficlight.getPhaseName(tl.getName()):
            if tl.getTimeInCurrentPhase() >= self.maxGreenPhaseTime:
                if traci.trafficlight.getPhase(tl.getName()) >= (len(tl.getPhases()) - 2):
                    traci.trafficlight.setPhase(tl.getName(), 0)
                    return True
                else:
                    traci.trafficlight.setPhase(
                        tl.getName(), traci.trafficlight.getPhase(tl.getName()) + 1)
                    return True
            else:
                #traci.trafficlight.setPhase(tl.getName(), nextRule.getAction())
                tl.updateTimeInCurrentPhase(5)

        elif "Y" in traci.trafficlight.getPhaseName(tl.getName()):
            if tl.getTimeInCurrentPhase() >= self.maxYellowPhaseTime:
                if traci.trafficlight.getPhase(tl.getName()) >= (len(tl.getPhases()) - 2):
                    traci.trafficlight.setPhase(tl.getName(), 0)
                    return True

                else:
                    traci.trafficlight.setPhase(
                        tl.getName(), traci.trafficlight.getPhase(tl.getName()) + 1)
                    return True
            else:
                tl.updateTimeInCurrentPhase(5)
        else:
            return False

    # ONE LANE WAITING USER-DEFINED RULE
    def checkAssignGreenPhaseToSingleWaitingPhaseRule(self, tl: TrafficLight) -> bool:
        lanesWithWaitingVehicles = []
        if tl.getName() == "four-arm":
            state = self.getState(tl)
            # print(state)
            for x in state:
                if state[x] != [] and "2four-arm" in x:
                    lanesWithWaitingVehicles.append(x)

            possibleLanes0 = ["WB2four-arm_LTL_0", "incoming2four-arm_LTL_0"]
            possibleLanes2 = ["WB2four-arm_LTL_1", "incoming2four-arm_LTL_1"]
            possibleLanes4 = ["NWB2four-arm_LTL_0", "bend2four-arm_LTL_0"]
            possibleLanes6 = ["NWB2four-arm_LTL_1", "bend2four-arm_LTL_1"]
            posLanesWaiting = []
            if set(lanesWithWaitingVehicles).issubset(set(possibleLanes0)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes0:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                # print("posLanesWaiting is", posLanesWaiting,
                #       "and lanesWithWaitingVeh is", lanesWithWaitingVehicles)
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 0)
                    return True

            elif set(lanesWithWaitingVehicles).issubset(set(possibleLanes2)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes2:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 2)
                    return True

            elif set(lanesWithWaitingVehicles).issubset(set(possibleLanes4)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes4:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 4)
                    return True

            elif set(lanesWithWaitingVehicles).issubset(set(possibleLanes6)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes6:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 6)
                    return True

        elif tl.getName() == "incoming":
            state = self.getState(tl)
            for x in state:
                if state[x] != [] and "2incoming" in x:
                    lanesWithWaitingVehicles.append(x)

            possibleLanes0 = [
                "four-arm2incoming_0", "four-arm2incoming_1", "EB2incoming_0", "EB2incoming_1"]
            possibleLanes2 = ["T-intersection2incoming_LTL_0",
                              "T-intersection2incoming_LTL_1"]
            possibleLanes4 = ["NEB2incoming_LTL_0", "NEB2incoming_LTL_1"]
            posLanesWaiting = []

            if set(lanesWithWaitingVehicles).issubset(set(possibleLanes0)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes0:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 0)
                    return True

            elif set(lanesWithWaitingVehicles).issubset(set(possibleLanes2)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes2:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 2)
                    return True

            elif set(lanesWithWaitingVehicles).issubset(set(possibleLanes4)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes4:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 4)
                    return True

        else:
            state = self.getState(tl)
            for x in state:
                if state[x] != [] and "2T" in x:
                    lanesWithWaitingVehicles.append(x)

            possibleLanes0 = ["SEB2T-intersection_0",
                              "SEB2T-intersection_1", "bend2T-intersection_LTL_0"]
            possibleLanes2 = ["bend2T-intersection_LTL_1"]
            posLanesWaiting = []

            if set(lanesWithWaitingVehicles).issubset(set(possibleLanes0)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes0:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 0)
                    return True

            elif set(lanesWithWaitingVehicles).issubset(set(possibleLanes2)):
                for i in range(len(lanesWithWaitingVehicles)+1):
                    if i == len(lanesWithWaitingVehicles):
                        for i in range(len(lanesWithWaitingVehicles)):
                            if lanesWithWaitingVehicles[i] in possibleLanes2:
                                posLanesWaiting.append(
                                    lanesWithWaitingVehicles[i])
                if len(posLanesWaiting) > 0 and posLanesWaiting == lanesWithWaitingVehicles:
                    traci.trafficlight.setPhase(tl.getName(), 2)
                    return True

        return False  # If not returned true by now, return false

    def checkMaxRedPhaseTimeRule(self, tl: TrafficLight) -> bool:
        if tl.maxRedPhaseTimeReached() is not False:
            traci.trafficlight.setPhase(tl.getName(), tl.maxRedPhaseTimeReached())
            return True
        else:
            return False

# Uncomment below if you wish to use the Driver without main.py


# main entry point
if __name__ == "__main__":

    # traci starts sumo as a subprocess and then this script connects and runs
    traci.start([sumoBinary, "-c", "config_file.sumocfg",
                 "--tripinfo-output", "tripinfo.xml"])
    run()
