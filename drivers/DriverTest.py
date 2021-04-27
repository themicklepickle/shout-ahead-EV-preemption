from __future__ import annotations

import traci

from drivers.DriverEV import DriverEV

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

    def updateOutputValues(self, tl) -> None:
        self.EVStops += self.getNumEVStops(tl)
        averageEVSpeed = self.getAverageEVSpeed(tl)
        if averageEVSpeed is not None:
            self.averageEVSpeedsList.append(averageEVSpeed)
        if len(self.averageEVSpeedsList) > 0:
            self.averageEVSpeed = sum(self.averageEVSpeedsList) / len(self.averageEVSpeedsList)

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

            # Apply Do Nothing action if no rules were applicable
            tl.doNothing()  # Update traffic light's Do Nothing counter
            tl.getAssignedIndividual().updateFitnessPenalty(False, 0)  # Update fitness penalty for individual
            tl.setCurrentRule(rule)  # Set current rule in traffic light
            tl.updateTimePhaseSpentInRed(traci.trafficlight.getPhase(tl.getName()), 5)

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
                self.updateOutputValues(tl)

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
                    carsWaitingAfter = self.carsWaiting(tl)

                    # Apply the next rule; if action is -1 then action is do nothing
                    if not nextRule.hasDoNothingAction() and nextRule is not tl.getCurrentRule():
                        traci.trafficlight.setPhase(tl.getName(), nextRule.getAction())
                        tl.resetTimeInCurrentPhase()

                        self.updateValues(tl, isEVApproaching, nextRule, carsWaitingAfter)
                        continue

                # Apply Do Nothing action if no rules were applicable
                tl.doNothing()  # Update traffic light's Do Nothing counter
                tl.getAssignedIndividual().updateFitnessPenalty(False, False)  # Update fitness penalty for individual
                self.checkUDRules(tl, nextRule)
                self.updateValues(tl, isEVApproaching, nextRule, carsWaitingAfter)

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
                self.updateOutputValues(tl)

        traci.close()  # End simulation

        self.simulationTime = step
