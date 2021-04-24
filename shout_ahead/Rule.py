from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Literal
    from shout_ahead.AgentPool import AgentPool


class Rule:

    def __init__(self, ruleType: str, conditions: List[str], action: int, agentPool: AgentPool):
        self.type = ruleType                # Name of the rule set that the rule belongs to ["RS", "RSev", "RSint", "RSev_int", "RSlearned", "RSlearned_int", "user-defined"]
        self.conditions = conditions        # Set of predicates that determine if rule is true
        self.action = action                # Action to carry out if all conditions are true
        self.agentPool = agentPool          # Agent pool rule rule originated from (used for updating actions of rule)
        self.weight: float = 0              # Weight of rule (used during a TL agent's process of selecting a rule)
        self.timesSelected: int = 0         # Keep track of how many times a rule was selected
        self.normalizedWeight: float = 0
        self.doNothingAction: bool = False  # Flag to keep track of an action being "do nothing"
        self.setDoNothingFlag()             # Used by Driver to determine if action is "Do nothing", which cannot be applied in the simulator

    def __str__(self):
        conditions = ', '.join(self.getConditions())
        weight = f"weight: {self.getWeight()}"
        action = f"action: {self.getAction()}"
        type_ = f"type: {self.getType()}"
        return "\n" + "\n   ".join([conditions, weight, action, type_])

    def __repr__(self):
        return str(self)

    def getJSON(self):
        return {
            "type": self.type,
            "conditions": self.conditions,
            "action": self.action,
            "agentPool": self.agentPool.getID(),
            "weight": self.weight,
            "timesSelected": self.timesSelected,
            "normalizedWeight": self.normalizedWeight,
            "doNothingAction": self.doNothingAction
        }

    def getType(self):
        return self.type

    def setType(self, ruleType: str):
        self.type = ruleType

    def getConditions(self):
        return self.conditions

    def setConditions(self, conditions: List[str]):
        self.conditions = conditions

    def getAction(self):
        return self.action

    def setAction(self, action):
        if action == -1:
            self.action = 1
        else:
            self._action = action

    def getAgentPool(self):
        return self.agentPool

    def setAgentPool(self, agentPool):
        self.agentPool = agentPool

    def getWeight(self):
        return self.weight

    def setWeight(self, weight):
        self.weight = weight

    def updateWeight(self, weight):
        self.weight += weight

    def selected(self):
        self.timesSelected += 1

    def getTimesSelected(self):
        return self.timesSelected

    def getNormalizedWeight(self):
        return self.normalizedWeight

    def setNormalizedWeight(self, weight):
        self.normalizedWeight = weight

    def setDoNothingFlag(self):
        if self.type != "user-defined":
            if self.action == len(self.agentPool.getActionSet())-1:
                self.doNothingAction = True

    def hasDoNothingAction(self):
        if self.doNothingAction:
            return True
        else:
            return False
