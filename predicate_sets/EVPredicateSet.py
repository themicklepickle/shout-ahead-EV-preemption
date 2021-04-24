from __future__ import annotations

import sys
import inspect
from random import randrange

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from shout_ahead.AgentPool import AgentPool


#--------------------- EV Traffic Density ----------------------#
def EVTrafficDensity_0(trafficDensity: float):
    return trafficDensity == 0


def EVTrafficDensity_0_15(trafficDensity: float):
    return 0 < trafficDensity <= 15


def EVTrafficDensity_15_45(trafficDensity: float):
    return 15 < trafficDensity <= 45


def EVTrafficDensity_45_90(trafficDensity: float):
    return 45 < trafficDensity <= 90


def EVTrafficDensity_90_120(trafficDensity: float):
    return 90 < trafficDensity <= 120


def EVTrafficDensity_120(trafficDensity: float):
    return trafficDensity > 120
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
def getPredicateSet():
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
    predicateSet: List[str] = []
    for predicate in methodsDict:
        predicateSet.append(predicate)

    return predicateSet


# GET THE TYPES OF PREDICATES
def getPredicateTypes() -> List[str]:
    predicateTypes = [
        "EVTrafficDensity",
        "EVDistanceToIntersection"
    ]
    return predicateTypes


# RETURN RANDOM PREDICATE FROM LIST OF PREDICATE FUNCTIONS
def getRandomPredicate(agentPool: AgentPool):
    predicateSet = getPredicateSet(agentPool, False)
    return (predicateSet[randrange(len(predicateSet))])


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
