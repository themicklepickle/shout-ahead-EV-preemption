from __future__ import annotations

import sys
import inspect
from random import randrange

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from AgentPool import AgentPool


#--------------------- EV Traffic Density ----------------------#
def EVTrafficDensity_0(trafficDensity: float):
    return trafficDensity == 0


def EVTrafficDensity_0_2(trafficDensity: float):
    return 0 < trafficDensity <= 2


def EVTrafficDensity_2_5(trafficDensity: float):
    return 2 < trafficDensity <= 5


def EVTrafficDensity_5_10(trafficDensity: float):
    return 5 < trafficDensity <= 10


def EVTrafficDensity_10_15(trafficDensity: float):
    return 10 < trafficDensity <= 15


def EVTrafficDensity_15_25(trafficDensity: float):
    return 15 < trafficDensity <= 25


def EVTrafficDensity_25_35(trafficDensity: float):
    return 25 < trafficDensity <= 35


def EVTrafficDensity_35_45(trafficDensity: float):
    return 35 < trafficDensity <= 45


def EVTrafficDensity_45_60(trafficDensity: float):
    return 45 < trafficDensity <= 60


def EVTrafficDensity_60_90(trafficDensity: float):
    return 60 < trafficDensity <= 90


def EVTrafficDensity_90_120(trafficDensity: float):
    return 90 < trafficDensity <= 120


def EVTrafficDensity_120_150(trafficDensity: float):
    return 120 < trafficDensity <= 150


def EVTrafficDensity_150(trafficDensity: float):
    return trafficDensity > 150
#----------------------------- end -----------------------------#


#----------------- EV distance to intersection ------------------#
def EVDistanceToIntersection_0(distanceToIntersection: float):
    return distanceToIntersection == 0


def EVDistanceToIntersection_0_100(distanceToIntersection: float):
    return 0 < distanceToIntersection <= 100


def EVDistanceToIntersection_100_200(distanceToIntersection: float):
    return 100 < distanceToIntersection <= 200


def EVDistanceToIntersection_200_300(distanceToIntersection: float):
    return 200 < distanceToIntersection <= 300


def EVDistanceToIntersection_300(distanceToIntersection: float):
    return distanceToIntersection > 300
#----------------------------- end -----------------------------#


# EVALUATES VALIDITY OF LEADING EV LANE PREDICATE
def lanePredicate(predicate: str, leadingEVLane: str):
    return predicate.split("_", 1)[1] == leadingEVLane


# RETURN LIST OF PREDICATE FUNCTIONS
def getPredicateSet(agentPool: AgentPool, includeLanePredicates: bool = True):
    # Get reference to this module for next operation
    thisModule = sys.modules[__name__]
    # Get a dictionary with all methods (predicates) in this module
    methodsDict = dict(inspect.getmembers(thisModule, predicate=inspect.isfunction))
    # Remove all methods that are not predicates from dictionary
    methodsDict.pop("getPredicateSet")
    methodsDict.pop("getRandomPredicate")
    methodsDict.pop("getAgentSpecificPredicates")
    methodsDict.pop("lanePredicate")
    methodsDict.pop("getRandomLanePredicate")
    methodsDict.pop("getPredicateTypes")

    # Seperate methods/predicates from rest of data in dictionary into a list
    predicateList: List[str] = []
    for predicate in methodsDict:
        predicateList.append(predicate)

    if includeLanePredicates:
        predicateList += getAgentSpecificPredicates(agentPool)

    return predicateList


# GET THE TYPES OF PREDICATES
def getPredicateTypes(includeLanePredicates: bool = False) -> List[str]:
    predicateTypes = [
        "EVTrafficDensity",
        "EVDistanceToIntersection"
    ]
    if includeLanePredicates:
        predicateTypes.append("leadingEVLane")
    return predicateTypes


# RETURN RANDOM PREDICATE FROM LIST OF PREDICATE FUNCTIONS
def getRandomPredicate(agentPool: AgentPool):
    predicateList = getPredicateSet(agentPool, False)
    return (predicateList[randrange(len(predicateList))])


def getAgentSpecificPredicates(agentPool: AgentPool):
    customPredicates: List[str] = []
    for tl in agentPool.getAssignedTrafficLights():
        for lane in tl.getLanes():
            pred = f"leadingEVLane_{lane}"
            customPredicates.append(pred)
    return customPredicates


def getRandomLanePredicate(agentPool):
    lanePredicates = getAgentSpecificPredicates(agentPool)
    return lanePredicates[randrange(len(lanePredicates))]
