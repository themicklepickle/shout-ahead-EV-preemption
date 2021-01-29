import os
import sys
import optparse
import inspect
from random import randrange
from pprint import pprint


#--------------------- EV Traffic Density ----------------------#
def EVTrafficDensity_0(trafficDensity):
    if trafficDensity == 0:
        return True
    else:
        return False


def EVTrafficDensity_0_2(trafficDensity):
    if 0 < trafficDensity <= 2:
        return True
    else:
        return False


def EVTrafficDensity_2_5(trafficDensity):
    if 2 < trafficDensity <= 5:
        return True
    else:
        return False


def EVTrafficDensity_5_10(trafficDensity):
    if 5 < trafficDensity <= 10:
        return True
    else:
        return False


def EVTrafficDensity_10_15(trafficDensity):
    if 10 < trafficDensity <= 15:
        return True
    else:
        return False


def EVTrafficDensity_15_25(trafficDensity):
    if 15 < trafficDensity <= 25:
        return True
    else:
        return False


def EVTrafficDensity_25_35(trafficDensity):
    if 25 < trafficDensity <= 35:
        return True
    else:
        return False


def EVTrafficDensity_35_45(trafficDensity):
    if 35 < trafficDensity <= 45:
        return True
    else:
        return False


def EVTrafficDensity_45_60(trafficDensity):
    if 45 < trafficDensity <= 60:
        return True
    else:
        return False


def EVTrafficDensity_60_90(trafficDensity):
    if 60 < trafficDensity <= 90:
        return True
    else:
        return False


def EVTrafficDensity_90_120(trafficDensity):
    if 90 < trafficDensity <= 120:
        return True
    else:
        return False


def EVTrafficDensity_120_150(trafficDensity):
    if 120 < trafficDensity <= 150:
        return True
    else:
        return False


def EVTrafficDensity_150(trafficDensity):
    if trafficDensity > 150:
        return True
    else:
        return False
#----------------------------- end -----------------------------#


#----------------- EV distance to intersection ------------------#
def EVDistanceToIntersection_0(distanceToIntersection):
    if distanceToIntersection == 0:
        return True
    else:
        return False


def EVDistanceToIntersection_0_50(distanceToIntersection):
    if 0 < distanceToIntersection <= 50:
        return True
    else:
        return False


def EVDistanceToIntersection_50_100(distanceToIntersection):
    if 50 < distanceToIntersection <= 100:
        return True
    else:
        return False


def EVDistanceToIntersection_100_200(distanceToIntersection):
    if 100 < distanceToIntersection <= 200:
        return True
    else:
        return False


def EVDistanceToIntersection_200_300(distanceToIntersection):
    if 200 < distanceToIntersection <= 300:
        return True
    else:
        return False


def EVDistanceToIntersection_400_500(distanceToIntersection):
    if 400 < distanceToIntersection <= 500:
        return True
    else:
        return False


def EVDistanceToIntersection_500_600(distanceToIntersection):
    if 500 < distanceToIntersection <= 600:
        return True
    else:
        return False


def EVDistanceToIntersection_600_800(distanceToIntersection):
    if 600 < distanceToIntersection <= 800:
        return True
    else:
        return False


def EVDistanceToIntersection_800(distanceToIntersection):
    if distanceToIntersection > 800:
        return True
    else:
        return False
#----------------------------- end -----------------------------#


# TODO: will need to make individual predicates for each AP for the approaching EV's lane
# #-------------------- EV Approach Direction --------------------#
# def EVApproachingHorizontal(laneInfo):
#     EVLane, horizontalLanes = laneInfo
#     if EVLane is None:
#         return False
#     elif EVLane in horizontalLanes:
#         return True
#     else:
#         return False


# def EVApproachingVertical(laneInfo):
#     EVLane, verticalLanes = laneInfo
#     if EVLane is None:
#         return False
#     elif EVLane in verticalLanes:
#         return True
#     else:
#         return False
# #----------------------------- end -----------------------------#


# RETURN LIST OF PREDICATE FUNCTIONS
def getPredicateList():
    # Get reference to this module for next operation
    thisModule = sys.modules[__name__]
    # Get a dictionary with all methods (predicates) in this module
    methodsDict = dict(inspect.getmembers(thisModule, predicate=inspect.isfunction))
    # Remove all methods that are not predicates from dictionary
    methodsDict.pop("getPredicateList")
    methodsDict.pop("getRandomPredicate")
    methodsDict.pop("run")
    methodsDict.pop("pprint")

    # Seperate methods/predicates from rest of data in dictionary into a list
    predicateList = []
    for predicate in methodsDict:
        predicateList.append(predicate)

    return predicateList


# RETURN RANDOM PREDICATE FROM LIST OF PREDICATE FUNCTIONS
def getRandomPredicate():
    predicateList = getPredicateList()
    return (predicateList[randrange(len(predicateList))])


def run():
    print("\nThe predicate list is:")
    pprint(getPredicateList())


if __name__ == "__main__":
    run()
