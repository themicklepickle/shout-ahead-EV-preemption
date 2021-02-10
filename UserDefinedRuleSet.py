import os
import sys

class UserDefinedRuleSet:

    def __init__(self, ruleSet):
        self.ruleSet = ruleSet    # Set user defined rules

        # Return object rule set 
    def getRuleSet(self):
        return self.ruleSet
        
