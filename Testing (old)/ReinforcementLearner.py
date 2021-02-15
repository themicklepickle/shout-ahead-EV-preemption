import os
import sys
import math
from Rule import Rule

global learningFactor           # Influences rate with which the weight value converges against the correct weight value
global discountRate             # Determines the emphasis on the importance of future evaluations 
global throughputFactor         # Determines the emphasis throughput has on the size of the reward
global waitTimeReducedFactor    # Determines the emphasis reduced waiting time has on the size of the reward
global penaltyMultiplier        # The penalty multiplier attached to the number of excess cars at an intersection after a rule is applied compared to before; assigned to a rule for poor performance 
learningFactor = 0.5
discountRate = 0.5
throughputFactor = 1
waitTimeReducedFactor = 1
penaltyMultiplier = -0.05

def updatedWeight(rule, nextRule, throughputRatio, waitTimeReducedRatio, intersectionQueueDifference):
       # Returns the updated weight based on the Sarsa learning method
    updatedWeight = rule.getWeight() + (learningFactor*(determineReward(throughputRatio, waitTimeReducedRatio) + (discountRate*nextRule.getWeight() - rule.getWeight()))) + determinePenalty(intersectionQueueDifference)

    return updatedWeight * 0.0001 # Numbers are reduced by 99.99% to keep them managable

    # Function to determine the reward 
#*** Add in something for basing reward as performance relative to average rates in simulation maybe***
def determineReward(throughputRatio, waitTimeReducedRatio):
    return (throughputFactor*throughputRatio) + (waitTimeReducedFactor*waitTimeReducedRatio)

def determinePenalty(intersectionQueueDifference):
    if intersectionQueueDifference > 0:
        return intersectionQueueDifference*penaltyMultiplier
    else:
        return 0