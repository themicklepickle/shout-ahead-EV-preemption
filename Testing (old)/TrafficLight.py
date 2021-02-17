import os
import sys
from numpy.random import choice

from Intention import Intention
class TrafficLight:

    global pCoop                    # Probability of choosing rule from RS vs RSint as defined in "Learning cooperative behaviour for the shout-ahead architecture" (2014) 
    global assignedIndividual
    global maxIntentionRecievedTime
    maxIntentionRecievedTime = 40
    pCoop = 0.5

    def __init__ (self, name, lanes):
        self.name = name
        self.lanes = lanes
        self.edges = []
        self._setEdges(self.lanes)
        self.phases = []
        self.currentRule = -1 
        self.carsWaiting = {}
        self.waitTime = 0
        self.doNothingCount = 0
        self.communicationPartners = []
        self.communicatedIntentions = {}
        self.recievedIntentions = {}
        self.numOfTimesNoCoopRuleWasValid = 0
        self.numOfRulesSelected = 0
        self.numOfTimesNoRSRuleWasValid = 0
        self.timeInCurrentPhase = 0
        self.currentPhase = None
        self.maxRedPhaseTime = 0
        self.phaseTimeSpentInRed = []
        
        # RETURNS THE TRAFFIC LIGHT'S NAME
    def getName(self):
        return self.name

        # RETURNS THE NUMBER OF LANES CONTROLLED BY THE TRAFFIC LIGHT
    def getLanes(self):
        return self.lanes

        # RETURNS THE NUMBER OF EDGES CONTROLLED BY THE TRAFFIC LIGHT
    def getEdges(self):
        return self.edges
        
        # SETS THE NUMBER OF EDGES CONTROLLED BY THE TRAFFIC LIGHT
    def _setEdges(self, lanes):
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
                print("Edge already exists or is unprocessable:", edge)

       
        # RETURNS THE PHASES AVAILBLE TO THE TRAFFIC LIGHT
    def getPhases(self):
        return self.phases
        
        # SETS THE PHASES AVAILBLE TO THE TRAFFIC LIGHT
    def setPhases(self, phases):
        self.phases = phases

        # SETS THE PHASES AVAILBLE TO THE TRAFFIC LIGHT
    def addPhase(self, phase):
        self.phases.append(phase)
        # print("Adding a new phase to TL. Phases now include:", self.phases)
    
    def getCurrentPhase(self):
        return self.currentPhase
    
    def updateCurrentPhase(self, phase):
        self.currentPhase = phase
    
    def getTimeInCurrentPhase(self):
        return self.timeInCurrentPhase
    
    def updateTimeInCurrentPhase(self, time):
        self.timeInCurrentPhase += time
    
    def resetTimeInCurrentPhase(self):
        self.timeInCurrentPhase = 0
    
        # RETURN THE CURRENTLY SELECTED RULE
    def getCurrentRule(self):
        return self.currentRule

        # SET THE CURRENTLY SELECTED RULE
    def setCurrentRule(self, rule):
        self.currentRule = rule

        # RETURNS THE AGENT POOL OF THE TRAFFIC LIGHT
    def getAgentPool(self):
        return self.agentPool
        
        # ASSIGNS THE TRAFFIC LIGHT TO AN AGENT POOL
    def assignToAgentPool(self, agentPool):
        self.agentPool = agentPool

        # RETURNS THE RULE SET INDIVIDUAL CURRENTLY BEING USED BY THE TRAFFIC LIGHT FOR A SIM RUN
    def getAssignedIndividual(self):
        return self.assignedIndividual

        # ASSIGNS A RULE SET INDIVIDUAL CURRENTLY BEING USED BY THE TRAFFIC LIGHT FOR A SIM RUN
    def assignIndividual(self):
        self.assignedIndividual = self.agentPool.selectIndividual()
        #print("Individual selected is", self.assignedIndividual)
        self.assignedIndividual.selected() # Let Individual know it's been selected

        # RETURNS THE TOTAL NUMBER OF CARS WAITING AT THE TRAFFIC LIGHT'S INTERSECTION
    def getCarsWaiting(self):
        return self.carsWaiting
    
        # SETS THE TOTAL NUMBER OF CARS WAITING AT THE TRAFFIC LIGHT'S INTERSECTION
    def updateCarsWaiting(self, carsWaiting):
        self.carsWaiting = carsWaiting

        # RETURNS THE TOTAL WAIT TIME OF CARS WAITING AT THE TRAFFIC LIGHT'S INTERSECTION
    def getWaitTime(self):
        return self.waitTime
    
        # SETS THE TOTAL WAIT TIME OF CARS WAITING AT THE TRAFFIC LIGHT'S INTERSECTION
    def setWaitTime(self, waitTime):
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
    def setCommunicationPartners(self, commPartners):
        self.communicationPartners = commPartners

        # ADD A COMMUNICATION PARTNER
    def addCommunicationPartner(self, commPartner):
        self.communicationPartners.append(commPartner)

        # SET TL'S NEXT INTENDED ACTION
    def setIntention(self, intention):
        self.communicateIntention(intention)
        self.communicatedIntentions[intention.getTurn()] = intention

        # COMMUNICATE INTENTION TO ALL COMMUNICATION PARTNERS
    def communicateIntention(self, intention):
        for tl in self.communicationPartners:
            tl.recieveIntention(intention)

        # RECIEVE AN INTENTION FROM A COMMUNICATION PARTNER
    def recieveIntention(self, intention):
        if intention.getTurn() not in self.recievedIntentions:
            self.recievedIntentions[intention.getTurn()] = []
        
        self.recievedIntentions[intention.getTurn()].append(intention)
        # print(self.getName(), "recieved an intention from", intention.getTrafficLight().getName(), "\n")

    def getCommunicatedIntentions(self):
        return self.recievedIntentions


        # REMOVES ALL INTENTIONS SENT TOO LONG AGO
    def removeOldIntentions(self, currentTime):
        intentionsToRemove = []
        for intention in self.recievedIntentions:
            if (currentTime - intention) > maxIntentionRecievedTime:
                intentionsToRemove.append(intention)
        for intention in intentionsToRemove:
            self.recievedIntentions.pop(intention)

    def resetRecievedIntentions(self):
        self.recievedIntentions = {}

        # SETS MAXIMUM TIME A TL EDGE CAN SPEND IN A RED PHASE (MaxGreenPhaseTime*NumOfGreenPhases + MaxYellowPhaseTime*NumOfGreenPhases)
    def setMaxRedPhaseTime(self, maxGreenPhaseTime, maxYellowPhaseTime):
        numberOfPhases = len(self.phases)/2
        self.maxRedPhaseTime = (numberOfPhases/2)*maxGreenPhaseTime + (numberOfPhases/2)*maxYellowPhaseTime

    def getMaxRedPhaseTime(self):
        return self.maxRedPhaseTime
    
    def initPhaseTimeSpentInRedArray(self):
        for i in range(len(self.agentPool.getActionSet())-1):
            self.phaseTimeSpentInRed.append(0)
        #print('Array initialized!', self.phaseTimeSpentInRed)
    
    def updateTimePhaseSpentInRed(self, currentPhase, time):
        #print("The phaseTimeSpentInRed array is", self.phaseTimeSpentInRed, "and the max red phase time is", self.maxRedPhaseTime)
        #print("The current phase is", currentPhase)
        for x in range(len(self.phaseTimeSpentInRed)):
            #print('x is', x)
            if x != currentPhase:
                self.phaseTimeSpentInRed[x] += time
        self.phaseTimeSpentInRed[currentPhase] = 0

    def maxRedPhaseTimeReached(self):
        index = 0
        for x in self.phaseTimeSpentInRed:
            if x >= self.maxRedPhaseTime:
                #print("Max time reached. Returning index:", index)
                return index
            index += 1
        return False

        # DECIDE WHICH RULE TO APPLY AT CURRENT ACTION STEP
    def getNextRule(self, validRulesRS, validRulesRSint, time): 
        #for x in self.communicatedIntentions:
            #print("TL is", self.getName(),". The intention is", self.communicatedIntentions[x].getAction())      
        self.numOfRulesSelected += 1
            # First, select a rule from RS and communicate it
        intendedRule = self.getAssignedIndividual().selectRule(validRulesRS)    # Get intended rule to apply
        #print("Intended rule is", intendedRule, "!\n\n\n")    
        if intendedRule == -1:
            self.numOfTimesNoRSRuleWasValid += 1
            if self.currentRule is None or self.currentRule == -1:
                self.setIntention(Intention(self, len(self.getAgentPool().getActionSet())-1, time)) # Return the Do Nothing action
            else:
                #print("Using current rule instead. It is", self.currentRule)
                self.setIntention(Intention(self, self.currentRule.getAction(), time))
        else:
            if self.currentRule is None or self.currentRule == -1:
                #print('In else. Intended rule is', intendedRule)
                self.setIntention(Intention(self, len(self.getAgentPool().getActionSet())-1, time))
            else:
                self.setIntention(Intention(self, intendedRule.getAction(), time))
            
            # If intended rule isn't user-defined, select a rule from RSint and then decide between the two
        coopRule = self.getAssignedIndividual().selectCoopRule(validRulesRSint)
        if coopRule == -1:
            self.numOfTimesNoCoopRuleWasValid += 1
            #print("No valid rule from RSint.")
       
        if intendedRule == -1 and coopRule == -1:
            #print("Neither intended nor coopRule valid.")
            if self.currentRule is None or self.currentRule == -1:
                #print('In if statement. Current rule is', self.currentRule)
                self.setIntention(Intention(self, len(self.getAgentPool().getActionSet())-1, time))
                return -1            
            else:
                #print("Returning currentRule with action", self.currentRule.getAction())
                self.setIntention(Intention(self, self.currentRule.getAction(), time))
                return self.currentRule
            # If no valid rules apply from RSint, return the intented rule from RS
        elif coopRule == -1 and intendedRule != -1:
            #print("CoopRule invalid. Applying intended rule:", intendedRule)
            self.setIntention(Intention(self, intendedRule.getAction(), time))
            return intendedRule
        
        elif coopRule != -1 and intendedRule == -1:
            #print("Intended rule invalid. Applying coop rule:", coopRule)
            self.setIntention(Intention(self, coopRule.getAction(), time))
            return coopRule

        elif coopRule.getWeight() >= intendedRule.getWeight():
            #print("CoopRule has higher weight than intended rule. Applying it:", coopRule)
            self.setIntention(Intention(self, coopRule.getAction(), time))
            return coopRule
        else:
            rule = choice([coopRule, intendedRule], 1, p = [pCoop, (1-pCoop)])  # Select one of the two rules based on pCoop value
            #print("The rule options are", rule, "and we chose", rule[0])
            self.setIntention(Intention(self, rule[0].getAction(), time))
            return rule[0]                                                      # Choice returns an array, so we take the only element of it

    def getCoopRuleValidRate(self):
        return (self.numOfTimesNoCoopRuleWasValid/self.numOfRulesSelected)*100
    
    def getRSRuleValidRate(self):
        return (self.numOfTimesNoRSRuleWasValid/self.numOfRulesSelected)*100
