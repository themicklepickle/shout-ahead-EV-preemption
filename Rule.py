import os
import sys


class Rule:

    def __init__(self, ruleType, conditions, action, agentPool):
        self.type = ruleType            # Either -1, 0 or 1: -1 indicates a userDefinedRule, 0 indicates a rule for RS, and 1 indicates a rule for RSint
        self.conditions = conditions    # Set of predicates that determine if rule is true
        self.action = action            # Action to carry out if all conditions are true 
        self.agentPool = agentPool      # Agent pool rule rule originated from (used for updating actions of rule)
        self.weight = 0                 # Weight of rule (used during a TL agent's process of selecting a rule)
        self.timesSelected = 0          # Keep track of how many times a rule was selected
        self.normalizedWeight = 0
        self.doNothingAction = False    # Flag to keep track of an action being "do nothing"
        self.setDoNothingFlag()         # Used by Driver to determine if action is "Do nothing", which cannot be applied in the simulator
    
        # GET RULE TYPE
    def getType(self):
        return self.type

        # GET RULE CONDITIONS
    def getConditions(self):
        return self.conditions
        
        # UPDATE RULE CONDITIONS
    def setConditions(self, conditions):
        self._conditions = conditions

        # GET RULE ACTION
    def getAction(self):
        return self.action
        
        # UPDATE RULE ACTION
    def setAction(self, action):
        if action == -1:
            print("Setting action to -1")
            print(x)
            self.action = 1
        else:
            self._action = action
        
        # GET CORRESPONDING AGENT POOL
    def getAgentPool(self):
        return self.agentPool
        
        # UPDATE AGENT POOL RULE ORIGINATED FROM
    def setAgentPool(self, agentPool):
        self.agentPool = agentPool
    
        # GET RULE WEIGHT
    def getWeight(self):
        return self.weight

    def setWeight(self, weight):
        self.weight = weight
        
        # UPDATE WEIGHT OF RULE AFTER SIMULATION RUN
    def updateWeight(self, weight):
        self.weight += weight
        
        # UPDATE NUMBER OF TIMES A RULE HAS BEEN APPLIED 
    def selected(self):
        self.timesSelected += 1
        
        # GET NUMBER OF TIMES A RULE HAS BEEN SELECTED
    def getTimesSelected(self):
        return self.timesSelected
    
    def getNormalizedWeight(self):
        return self.normalizedWeight
    
    def setNormalizedWeight(self, weight):
        self.normalizedWeight = weight

    def setDoNothingFlag(self):
        if self.type != -1:
            if self.action == len(self.agentPool.getActionSet())-1:
                self.doNothingAction = True
    
    def hasDoNothingAction(self):
        if self.doNothingAction:
            return True
        else:
            return False