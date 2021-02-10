from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
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
EVSpeedFactor = 1
EVTrafficDensityFactor = 1
penaltyMultiplier = -0.05
EVIsStoppedPenalty = -3


def updatedWeight(rule: Rule, nextRule: Rule, throughputRatio: float, waitTimeReducedRatio: float, intersectionQueueDifference: int, EVChangeInSpeed: float, EVChangeInTrafficDensity: float, EVIsStopped: bool) -> float:
    # Returns the updated weight based on the Sarsa learning method
    updatedWeight = rule.getWeight() + (learningFactor*(determineReward(throughputRatio, waitTimeReducedRatio, EVChangeInSpeed, EVChangeInTrafficDensity) +
                                                        (discountRate*nextRule.getWeight() - rule.getWeight()))) + determinePenalty(intersectionQueueDifference, EVIsStopped)

    return updatedWeight * 0.0001  # Numbers are reduced by 99.99% to keep them managable


# Function to determine the reward
def determineReward(throughputRatio: float, waitTimeReducedRatio: float, EVChangeInSpeed: float, EVChangeInTrafficDensity: float):
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
    return penalty
