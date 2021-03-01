from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
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

# EV reinforcement learning factors
global EVSpeedFactor
global EVQueueFactor
global EVIsStoppedPenalty
EVSpeedFactor = 0.1
EVQueueFactor = 1
EVIsStoppedPenalty = -1


def updatedWeight(rule: Rule, nextRule: Rule, throughputRatio: float, waitTimeReducedRatio: float, intersectionQueueDifference: int, EVChangeInSpeed: float, EVChangeInQueue: int, EVIsStopped: bool) -> float:
    # Returns the updated weight based on the Sarsa learning method
    reward = determineReward(throughputRatio, waitTimeReducedRatio, EVChangeInSpeed, EVChangeInQueue)
    penalty = determinePenalty(intersectionQueueDifference, EVIsStopped)
    
    updatedWeight = rule.getWeight() + (learningFactor * (reward + (discountRate * nextRule.getWeight() - rule.getWeight()))) + (penaltyMultiplier * penalty)

    return updatedWeight * 0.0001  # Numbers are reduced by 99.99% to keep them managable


# Function to determine the reward
def determineReward(throughputRatio: float, waitTimeReducedRatio: float, EVChangeInSpeed: float, EVChangeInQueue: int):
    reward = 0

    reward += throughputFactor * throughputRatio
    reward += waitTimeReducedFactor * waitTimeReducedRatio

    if EVChangeInSpeed is not None:
        reward += EVSpeedFactor * EVChangeInSpeed
    if EVChangeInQueue is not None:
        reward -= EVQueueFactor * EVChangeInQueue

    return reward


def determinePenalty(intersectionQueueDifference, EVIsStopped):
    penalty = 0

    if intersectionQueueDifference > 0:
        penalty += intersectionQueueDifference
    if EVIsStopped is True:
        penalty += EVIsStoppedPenalty

    return penalty
