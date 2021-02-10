from __future__ import annotations

from numpy.random import choice

from Intention import Intention

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Dict, Union, Literal
    from Intention import Intention
    from EmergencyVehicle import EmergencyVehicle
    from Rule import Rule
    from AgentPool import AgentPool


class TrafficLight:

    # Probability of choosing rule from RS vs RSint as defined in "Learning cooperative behaviour for the shout-ahead architecture" (2014)
    global pCoop
    global assignedIndividual
    global maxIntentionRecievedTime
    maxIntentionRecievedTime = 40
    pCoop = 0.5

    def __init__(self, name: str, lanes: List[str]):
        self.name = name
        self.lanes = lanes
        self.edges: List[str] = []
        self._setEdges(self.lanes)
        self.phases: List[str] = []
        self.currentRule: Union[Rule, Literal[-1]] = -1
        self.carsWaiting: Dict[str, List[str]] = {}
        self.waitTime: float = 0
        self.doNothingCount: int = 0
        self.communicationPartners: List[TrafficLight] = []
        self.communicatedIntentions: Dict[float, Intention] = {}
        self.recievedIntentions: Dict[float, List[Intention]] = {}
        self.numOfTimesNoCoopRuleWasValid: int = 0
        self.numOfRulesSelected: int = 0
        self.numOfTimesNoRSRuleWasValid: int = 0
        self.numOfTimesNoRSevRuleWasValid: int = 0
        self.timeInCurrentPhase: float = 0
        self.currentPhase: str = None
        self.maxRedPhaseTime: float = 0
        self.phaseTimeSpentInRed: List[float] = []
        self.EVs: List[EmergencyVehicle] = []
        self.leadingEV: EmergencyVehicle = None

    def __str__(self) -> str:
        return self.getName()

    def __repr__(self) -> str:
        return self.getName()

    # RETURNS THE TRAFFIC LIGHT'S NAME
    def getName(self):
        return self.name

    # RETURNS THE LANES CONTROLLED BY THE TRAFFIC LIGHT
    def getLanes(self):
        return self.lanes

    # RETURNS THE EDGES CONTROLLED BY THE TRAFFIC LIGHT
    def getEdges(self):
        return self.edges

    # SETS THE NUMBER OF EDGES CONTROLLED BY THE TRAFFIC LIGHT
    def _setEdges(self, lanes: List[str]):
        # Determine edges from lanes
        for l in lanes:
            # Isolate edge name from lane name
            edge = l.split("_")

            # Ensure edge being added to list isn't a duplicate or retains "LTL" designation
            if edge[1] == "LTL":
                edgeName = edge[0] + "_LTL"
                if edgeName not in self.edges:
                    self.edges.append(edgeName)

            elif edge[0] not in self.edges:
                self.edges.append(edge[0])

            else:
                pass

    # RETURNS THE PHASES AVAILBLE TO THE TRAFFIC LIGHT
    def getPhases(self):
        return self.phases

    # SETS THE PHASES AVAILBLE TO THE TRAFFIC LIGHT
    def setPhases(self, phases: List[str]):
        self.phases = phases

    # SETS THE PHASES AVAILBLE TO THE TRAFFIC LIGHT
    def addPhase(self, phase: str):
        self.phases.append(phase)

    def getCurrentPhase(self):
        return self.currentPhase

    def updateCurrentPhase(self, phase: str):
        self.currentPhase = phase

    def getTimeInCurrentPhase(self):
        return self.timeInCurrentPhase

    def updateTimeInCurrentPhase(self, time: float):
        self.timeInCurrentPhase += time

    def resetTimeInCurrentPhase(self):
        self.timeInCurrentPhase = 0

    # RETURN THE CURRENTLY SELECTED RULE
    def getCurrentRule(self):
        return self.currentRule

    # SET THE CURRENTLY SELECTED RULE
    def setCurrentRule(self, rule: Rule):
        self.currentRule = rule

    # RETURNS THE AGENT POOL OF THE TRAFFIC LIGHT
    def getAgentPool(self):
        return self.agentPool

    # ASSIGNS THE TRAFFIC LIGHT TO AN AGENT POOL
    def assignToAgentPool(self, agentPool: AgentPool):
        self.agentPool = agentPool

    # RETURNS THE RULE SET INDIVIDUAL CURRENTLY BEING USED BY THE TRAFFIC LIGHT FOR A SIM RUN
    def getAssignedIndividual(self):
        return self.assignedIndividual

    # ASSIGNS A RULE SET INDIVIDUAL CURRENTLY BEING USED BY THE TRAFFIC LIGHT FOR A SIM RUN
    def assignIndividual(self):
        self.assignedIndividual = self.agentPool.selectIndividual()
        self.assignedIndividual.selected()  # Let Individual know it's been selected

    # RETURNS THE TOTAL NUMBER OF CARS WAITING AT THE TRAFFIC LIGHT'S INTERSECTION
    def getCarsWaiting(self):
        return self.carsWaiting

    # SETS THE TOTAL NUMBER OF CARS WAITING AT THE TRAFFIC LIGHT'S INTERSECTION
    def updateCarsWaiting(self, carsWaiting: Dict[str, List[str]]):
        self.carsWaiting = carsWaiting

    # RETURNS THE TOTAL WAIT TIME OF CARS WAITING AT THE TRAFFIC LIGHT'S INTERSECTION
    def getWaitTime(self):
        return self.waitTime

    # SETS THE TOTAL WAIT TIME OF CARS WAITING AT THE TRAFFIC LIGHT'S INTERSECTION
    def setWaitTime(self, waitTime: float):
        self.waitTime = waitTime

    # INCREMENTS THE NUMBER OF TIMES THE TL HAS APPLIED THE Do Nothing ACTION
    def doNothing(self):
        self.doNothingCount += 1

    # RETURN THE doNothingCount
    def getDoNothingCount(self):
        return self.doNothingCount

    # RETURN LIST OF COMMUNICATION PARTNERS
    def getCommunicationPartners(self):
        return self.communicationPartners

    # SET LIST OF COMMUNICATION PARTNERS
    def setCommunicationPartners(self, commPartners: List[TrafficLight]):
        self.communicationPartners = commPartners

    # ADD A COMMUNICATION PARTNER
    def addCommunicationPartner(self, commPartner: TrafficLight):
        self.communicationPartners.append(commPartner)

    # SET TL'S NEXT INTENDED ACTION
    def setIntention(self, intention: Intention):
        self.communicateIntention(intention)
        self.communicatedIntentions[intention.getTurn()] = intention

    # COMMUNICATE INTENTION TO ALL COMMUNICATION PARTNERS
    def communicateIntention(self, intention: Intention):
        for tl in self.communicationPartners:
            tl.recieveIntention(intention)

    # RECIEVE AN INTENTION FROM A COMMUNICATION PARTNER
    def recieveIntention(self, intention: Intention):
        if intention.getTurn() not in self.recievedIntentions:
            self.recievedIntentions[intention.getTurn()] = []

        self.recievedIntentions[intention.getTurn()].append(intention)

    def getCommunicatedIntentions(self):
        return self.recievedIntentions

    # REMOVES ALL INTENTIONS SENT TOO LONG AGO
    def removeOldIntentions(self, currentTime: float):
        intentionsToRemove = []
        for intention in self.recievedIntentions:
            if (currentTime - intention) > maxIntentionRecievedTime:
                intentionsToRemove.append(intention)
        for intention in intentionsToRemove:
            self.recievedIntentions.pop(intention)

    def resetRecievedIntentions(self):
        self.recievedIntentions = {}

    # SETS MAXIMUM TIME A TL EDGE CAN SPEND IN A RED PHASE (MaxGreenPhaseTime*NumOfGreenPhases + MaxYellowPhaseTime*NumOfGreenPhases)
    def setMaxRedPhaseTime(self, maxGreenPhaseTime: float, maxYellowPhaseTime: float):
        numberOfPhases = len(self.phases)/2
        self.maxRedPhaseTime = (numberOfPhases/2)*maxGreenPhaseTime + (numberOfPhases/2)*maxYellowPhaseTime

    def getMaxRedPhaseTime(self):
        return self.maxRedPhaseTime

    def initPhaseTimeSpentInRedArray(self):
        for _ in range(len(self.agentPool.getActionSet())-1):
            self.phaseTimeSpentInRed.append(0)
        # print('Array initialized!', self.phaseTimeSpentInRed)

    def updateTimePhaseSpentInRed(self, currentPhase: int, time: float):
        for i in range(len(self.phaseTimeSpentInRed)):
            if i != currentPhase:
                self.phaseTimeSpentInRed[i] += time
        self.phaseTimeSpentInRed[currentPhase] = 0

    def maxRedPhaseTimeReached(self):
        for i, time in enumerate(self.phaseTimeSpentInRed):
            if time >= self.maxRedPhaseTime:
                return i
        return False

    # DECIDE WHICH RULE TO APPLY AT CURRENT ACTION STEP
    def getNextRule(self, validRulesRS: List[Rule], validRulesRSint: List[Rule], validRulesRSev: List[Rule], isEVApproaching: bool, time: float) -> Union[Rule, Literal[-1]]:
        self.numOfRulesSelected += 1
        # First, select a rule from RS (or RSev if applicable) and communicate it
        if isEVApproaching:
            intendedRule = self.getAssignedIndividual().selectRule(validRulesRSev)  # Get intended rule to apply
        else:
            intendedRule = self.getAssignedIndividual().selectRule(validRulesRS)  # Get intended rule to apply
        if intendedRule == -1:
            if isEVApproaching:
                self.numOfTimesNoRSevRuleWasValid += 1
            else:
                self.numOfTimesNoRSRuleWasValid += 1
            if self.currentRule is None or self.currentRule == -1:
                # Return the Do Nothing action
                self.setIntention(Intention(self, len(self.getAgentPool().getActionSet())-1, time))
            else:
                self.setIntention(Intention(self, self.currentRule.getAction(), time))
        else:
            if self.currentRule is None or self.currentRule == -1:
                self.setIntention(Intention(self, len(self.getAgentPool().getActionSet())-1, time))
            else:
                self.setIntention(Intention(self, intendedRule.getAction(), time))

        # If intended rule isn't user-defined, select a rule from RSint and then decide between the two
        coopRule = self.getAssignedIndividual().selectCoopRule(validRulesRSint)
        if coopRule == -1:
            self.numOfTimesNoCoopRuleWasValid += 1

        if intendedRule == -1 and coopRule == -1:
            if self.currentRule is None or self.currentRule == -1:
                self.setIntention(Intention(self, len(self.getAgentPool().getActionSet())-1, time))
                return -1
            else:
                self.setIntention(Intention(self, self.currentRule.getAction(), time))
                return self.currentRule
        # If no valid rules apply from RSint, return the intented rule from RS
        elif coopRule == -1 and intendedRule != -1:
            self.setIntention(Intention(self, intendedRule.getAction(), time))
            return intendedRule

        elif coopRule != -1 and intendedRule == -1:
            self.setIntention(Intention(self, coopRule.getAction(), time))
            return coopRule

        elif coopRule.getWeight() >= intendedRule.getWeight():
            self.setIntention(Intention(self, coopRule.getAction(), time))
            return coopRule
        else:
            # Select one of the two rules based on pCoop value
            rule: List[Rule] = choice([coopRule, intendedRule], 1, p=[pCoop, (1 - pCoop)])
            self.setIntention(Intention(self, rule[0].getAction(), time))
            # Choice returns an array, so we take the only element of it
            return rule[0]

    def getCoopRuleValidRate(self):
        return (self.numOfTimesNoCoopRuleWasValid/self.numOfRulesSelected)*100

    def getRSRuleValidRate(self):
        return (self.numOfTimesNoRSRuleWasValid/self.numOfRulesSelected)*100

    def getRSevRuleValidRate(self):
        return (self.numOfTimesNoRSevRuleWasValid/self.numOfRulesSelected)*100

    def getEVs(self):
        return self.EVs

    def setEVs(self, EVs: List[EmergencyVehicle]):
        self.EVs = EVs

    def getLeadingEV(self):
        return self.leadingEV

    def setLeadingEV(self, leadingEV: EmergencyVehicle):
        self.leadingEV = leadingEV

    def existedBefore(self, ID: str):
        for EV in self.EVs:
            if EV.getID() == ID:
                return True
        return False

    def getEV(self, ID: str) -> EmergencyVehicle:
        for EV in self.EVs:
            if EV.getID() == ID:
                return EV
