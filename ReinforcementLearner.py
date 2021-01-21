import os
import sys
import math
from Rule import Rule

global learningFactor           # Influences rate with which the weight value converges against the correct weight value
global discountRate             # Determines the emphasis on the importance of future evaluations
global throughputFactor         # Determines the emphasis throughput has on the size of the reward
global waitTimeReducedFactor    # Determines the emphasis reduced waiting time has on the size of the reward
global EVSpeedFactor
global EVTrafficDensityFactor
global penaltyMultiplier        # The penalty multiplier attached to the number of excess cars at an intersection after a rule is applied compared to before; assigned to a rule for poor performance
global EVIsStoppedPenalty
learningFactor = 0.5
discountRate = 0.5
throughputFactor = 1
waitTimeReducedFactor = 1
EVSpeedFactor = 5
EVTrafficDensityFactor = 5
penaltyMultiplier = -0.05
EVIsStoppedPenalty = -100


def updatedWeight(rule, nextRule, throughputRatio, waitTimeReducedRatio, intersectionQueueDifference, EVChangeInSpeed, EVChangeInTrafficDensity, EVIsStopped):
    # Returns the updated weight based on the Sarsa learning method
    updatedWeight = rule.getWeight() + (learningFactor*(determineReward(throughputRatio, waitTimeReducedRatio, EVChangeInSpeed, EVChangeInTrafficDensity) +
                                                        (discountRate*nextRule.getWeight() - rule.getWeight()))) + determinePenalty(intersectionQueueDifference, EVIsStopped)

    return updatedWeight * 0.0001  # Numbers are reduced by 99.99% to keep them managable


# Function to determine the reward
def determineReward(throughputRatio, waitTimeReducedRatio, EVChangeInSpeed, EVChangeInTrafficDensity):
    reward = 0

    reward += throughputFactor * throughputRatio
    reward += waitTimeReducedFactor * waitTimeReducedRatio

    if EVChangeInSpeed is not None:
        reward += EVSpeedFactor * EVChangeInSpeed
    if EVChangeInTrafficDensity is not None:
        reward += EVTrafficDensityFactor * EVChangeInTrafficDensity

    return reward


def determinePenalty(intersectionQueueDifference, EVIsStopped):
    penalty = 0
    if intersectionQueueDifference > 0:
        penalty += intersectionQueueDifference * penaltyMultiplier
    if EVIsStopped is True:
        penalty += EVIsStoppedPenalty
    print(penalty)
    return penalty
