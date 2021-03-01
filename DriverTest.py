from __future__ import annotations

import traci
import timeit

from DriverEV import DriverEV

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Dict


class DriverTest(DriverEV):
    def getResults(self) -> Dict:
        return {
            "EVStops": self.EVStops,
            "averageEVSpeed": self.averageEVSpeed,
            "simulationTime": self.simulationTime
        }

    def runTest(self) -> None:
        # results to be outputted
        self.EVStops = 0
        self.averageEVSpeedsList = []
        self.averageEVSpeed = 0
        self.simulationTime = 0

        # Start SUMO. Comment out if running Driver as standalone module.
        traci.start(self.sumoCmd)

        # Run set-up script and acquire list of user defined rules and traffic light agents in simulation
        userDefinedRules = self.setUpTuple[0]
        trafficLights = self.setUpTuple[1]
        rule = -1
        nextRule = -1

        # run functions to setup state
        self.constructTLControllingLaneDict(trafficLights)
        self.constructLeftTurnLanesList(trafficLights)
        self.constructTimeSinceLastEVThroughDict(trafficLights)

        # get state and EVs
        self.calculateState(trafficLights)
        self.calculateEVs(trafficLights)
        self.calculateLeadingEV(trafficLights)
        self.calculateTimeSinceLastEVThrough(trafficLights)

        # Simulation loop
        step = 0

        carsWaitingAfter = {}

        for tl in trafficLights:
            tl.assignIndividual(testing=True)
            tl.updateCurrentPhase(traci.trafficlight.getPhaseName(tl.getName()))

            rule = self.applicableUserDefinedRule(tl, userDefinedRules)  # Check user-defined rules

            # If no user-defined rules can be applied, get a rule from Agent Pool
            if rule == False or rule is None:
                # Determine if the rule should be chosen from RS or RSev
                isEVApproaching = self.getIsEVApproaching(tl)
                validRS, validRSint, validRSev, validRSev_int = self.getValidRules(tl, tl.getAssignedIndividual())

                # Get a rule from assigned Individual
                rule = tl.getNextRule(validRS, validRSint, validRSev, validRSev_int, isEVApproaching, self.useEVCoopPredicates, traci.simulation.getTime())

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
            # tl.updateTimePhaseSpentInRed(traci.trafficlight.getPhase(tl.getName()), 5)

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
                # update output values
                self.EVStops += self.getNumEVStops(tl)
                self.averageEVSpeedsList.append(self.getAverageEVSpeed(tl))
                if len(self.averageEVSpeedsList) > 0:
                    self.averageEVSpeed = sum(self.averageEVSpeedsList) / len(self.averageEVSpeedsList)

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
                carsWaitingAfter = self.carsWaiting(tl)

                # Get EV reinforcement learning parameters
                if isEVApproaching:
                    leadingEV = self.getLeadingEV(tl)
                    EVs = self.getEVs(tl)
                else:
                    leadingEV = None
                    EVs = []

                validRS, validRSint, validRSev, validRSev_int = self.getValidRules(tl, tl.getAssignedIndividual())

                if len(validRS) == 0 and len(validRSint) == 0 and not isEVApproaching and not self.useEVCoopPredicates:
                    nextRule = -1
                elif len(validRSev) == 0 and len(validRSint) == 0 and isEVApproaching and not self.useEVCoopPredicates:
                    nextRule = -1
                elif len(validRS) == 0 and len(validRSev_int) == 0 and not isEVApproaching and self.useEVCoopPredicates:
                    nextRule = -1
                elif len(validRSev) == 0 and len(validRSev_int) == 0 and isEVApproaching and self.useEVCoopPredicates:
                    nextRule = -1
                else:
                    nextRule = tl.getNextRule(validRS, validRSint, validRSev, validRSev_int, isEVApproaching, self.useEVCoopPredicates, traci.simulation.getTime())

                if nextRule == -1:
                    tl.doNothing()  # Update traffic light's Do Nothing counter
                    tl.getAssignedIndividual().updateFitnessPenalty(False, False)  # Update fitness penalty for individual
                else:
                    # Apply the next rule; if action is -1 then action is do nothing
                    if not nextRule.hasDoNothingAction():
                        traci.trafficlight.setPhase(tl.getName(), nextRule.getAction())

                        # change the phase if the action is different than the current action
                        if nextRule is not tl.getCurrentRule():
                            traci.trafficlight.setPhase(tl.getName(), nextRule.getAction())
                            tl.resetTimeInCurrentPhase()
                            # if tl.getName() == "incoming":
                            # print(step)
                            # print(tl.getName())
                            # print(nextRule)
                            # print("\n")

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

        traci.close()  # End simulation

        self.simulationTime = step

    def runATL(self):
        # results to be outputted
        self.EVStops = 0
        self.averageEVSpeedsList = []
        self.averageEVSpeed = 0
        self.simulationTime = 0

        # Start SUMO. Comment out if running Driver as standalone module.
        traci.start(self.sumoCmd)

        # run functions to setup state
        trafficLights = self.setUpTuple[1]
        self.constructTLControllingLaneDict(trafficLights)
        self.constructLeftTurnLanesList(trafficLights)
        self.constructTimeSinceLastEVThroughDict(trafficLights)

        # Simulation loop
        step = 0

        while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < self.maxSimulationTime:
            traci.simulationStep()  # Advance SUMO simulation one step (1 second)

            step += 1
            if step % 5 != 0:
                continue

            # get state and EVs
            self.calculateState(trafficLights)
            self.calculateEVs(trafficLights)
            self.calculateLeadingEV(trafficLights)
            self.calculateTimeSinceLastEVThrough(trafficLights)

            for tl in trafficLights:
                # update output values
                self.EVStops += self.getNumEVStops(tl)
                self.averageEVSpeedsList.append(self.getAverageEVSpeed(tl))
                if len(self.averageEVSpeedsList) > 0:
                    self.averageEVSpeed = sum(self.averageEVSpeedsList) / len(self.averageEVSpeedsList)

        traci.close()  # End simulation

        self.simulationTime = step
