from __future__ import annotations

import sys
import inspect
from random import randrange

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List


#---------- longestTimeWaitedToProceedStaight predicate set ----------#
def longestTimeWaitedToProceedStraight_0(time: float):
    return time == 0


def longestTimeWaitedToProceedStraight_0_15(time: float):
    return 0 < time <= 15


def longestTimeWaitedToProceedStraight_15_30(time: float):
    return 15 < time <= 30


def longestTimeWaitedToProceedStraight_30_45(time: float):
    return 30 < time <= 45


def longestTimeWaitedToProceedStraight_45_60(time: float):
    return 45 < time <= 60


def longestTimeWaitedToProceedStraight_60_90(time: float):
    return 60 < time <= 90


def longestTimeWaitedToProceedStraight_90_120(time: float):
    return 90 < time <= 120


def longestTimeWaitedToProceedStraight_120_150(time: float):
    return 120 < time <= 150


def longestTimeWaitedToProceedStraight_150_180(time: float):
    return 150 < time <= 180


def longestTimeWaitedToProceedStraight_180_210(time: float):
    return 180 < time <= 210


def longestTimeWaitedToProceedStraight_210_240(time: float):
    return 210 < time <= 240


def longestTimeWaitedToProceedStraight_240_270(time: float):
    return 240 < time <= 270


def longestTimeWaitedToProceedStraight_270_300(time: float):
    return 270 < time <= 300


def longestTimeWaitedToProceedStraight_300(time: float):
    return time > 300
#----------------------------- end -----------------------------#


#---------- longestTimeWaitedToTurnLeft predicate set ----------#
def longestTimeWaitedToTurnLeft_0(time: float):
    return time == 0


def longestTimeWaitedToTurnLeft_0_15(time: float):
    return 0 < time <= 15


def longestTimeWaitedToTurnLeft_15_30(time: float):
    return 15 < time <= 30


def longestTimeWaitedToTurnLeft_30_45(time: float):
    return 30 < time <= 45


def longestTimeWaitedToTurnLeft_45_60(time: float):
    return 45 < time <= 60


def longestTimeWaitedToTurnLeft_60_90(time: float):
    return 60 < time <= 90


def longestTimeWaitedToTurnLeft_90_120(time: float):
    return 90 < time <= 120


def longestTimeWaitedToTurnLeft_120_150(time: float):
    return 120 < time <= 150


def longestTimeWaitedToTurnLeft_150_180(time: float):
    return 150 < time <= 180


def longestTimeWaitedToTurnLeft_180_210(time: float):
    return 180 < time <= 210


def longestTimeWaitedToTurnLeft_210_240(time: float):
    return 210 < time <= 240


def longestTimeWaitedToTurnLeft_240_270(time: float):
    return 240 < time <= 270


def longestTimeWaitedToTurnLeft_270_300(time: float):
    return 270 < time <= 300


def longestTimeWaitedToTurnLeft_300(time: float):
    return time > 300
#----------------------------- end -----------------------------#


#-------- NumCarsWaitingToProceedStraight predicate set --------#
def numCarsWaitingToProceedStraight_0(carCount: int):
    return carCount == 0


def numCarsWaitingToProceedStraight_0_5(carCount: int):
    return 0 < carCount <= 5


def numCarsWaitingToProceedStraight_5_10(carCount: int):
    return 5 < carCount <= 10


def numCarsWaitingToProceedStraight_10_15(carCount: int):
    return 10 < carCount <= 15


def numCarsWaitingToProceedStraight_15_25(carCount: int):
    return 15 < carCount <= 25


def numCarsWaitingToProceedStraight_25_35(carCount: int):
    return 25 < carCount <= 35


def numCarsWaitingToProceedStraight_35_45(carCount: int):
    return 35 < carCount <= 45


def numCarsWaitingToProceedStraight_45(carCount: int):
    return carCount > 45

#----------------------------- end -----------------------------#


#------------ NumCarsWaitingToTurnLeft predicate set ------------#
def numCarsWaitingToTurnLeft_0(carCount: int):
    return carCount == 0


def numCarsWaitingToTurnLeft_0_3(carCount: int):
    return 0 < carCount <= 3


def numCarsWaitingToTurnLeft_3_6(carCount: int):
    return 3 < carCount <= 6


def numCarsWaitingToTurnLeft_6_9(carCount: int):
    return 6 < carCount <= 9


def numCarsWaitingToTurnLeft_9_12(carCount: int):
    return 9 < carCount <= 12


def numCarsWaitingToTurnLeft_12_15(carCount: int):
    return 12 < carCount <= 15


def numCarsWaitingToTurnLeft_15(carCount: int):
    return carCount > 15
#----------------------------- end -----------------------------#


#-------- TimeSpentInCurrentPhase predicate set --------#
def timeSpentInCurrentPhase_0(time: float):
    return time == 0


def timeSpentInCurrentPhase_0_15(time: float):
    return 0 < time <= 15


def timeSpentInCurrentPhase_15_30(time: float):
    return 15 < time <= 30


def timeSpentInCurrentPhase_30_45(time: float):
    return 30 < time <= 45


def timeSpentInCurrentPhase_45_60(time: float):
    return 45 < time <= 60


def timeSpentInCurrentPhase_60_90(time: float):
    return 60 < time <= 90


def timeSpentInCurrentPhase_90_120(time: float):
    return 90 < time <= 120


def timeSpentInCurrentPhase_120_150(time: float):
    return 120 < time <= 150


def timeSpentInCurrentPhase_150_180(time: float):
    return 150 < time <= 180


def timeSpentInCurrentPhase_180_210(time: float):
    return 180 < time <= 210


def timeSpentInCurrentPhase_210_240(time: float):
    return 210 < time <= 250


def timeSpentInCurrentPhase_240_270(time: float):
    return 240 < time <= 270


def timeSpentInCurrentPhase_270_300(time: float):
    return 270 < time <= 300


def timeSpentInCurrentPhase_300(time: float):
    return time > 300
#----------------------------- end -----------------------------#


#------------------- Phase check predicates --------------------#
def verticalPhaseIs_Green(tlPhaseArray: List[str]):
    return "V" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def verticalPhaseIs_Yellow(tlPhaseArray: List[str]):
    return "V" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def northSouthPhaseIs_Green(tlPhaseArray: List[str]):
    return "NS" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def northSouthPhaseIs_Yellow(tlPhaseArray: List[str]):
    return "NS" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def southNorthPhaseIs_Green(tlPhaseArray: List[str]):
    return "SN" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def southNorthPhaseIs_Yellow(tlPhaseArray: List[str]):
    return "SN" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def verticalPhaseIsLeftTurn_Green(tlPhaseArray: List[str]):
    return "V" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def verticalPhaseIsLeftTurn_Yellow(tlPhaseArray: List[str]):
    return "V" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def northSouthPhaseIsLeftTurn_Green(tlPhaseArray: List[str]):
    return "NS" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def northSouthPhaseIsLeftTurn_Yellow(tlPhaseArray: List[str]):
    return "NS" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def southNorthPhaseIsLeftTurn_Green(tlPhaseArray: List[str]):
    return "SN" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def southNorthPhaseIsLeftTurn_Yellow(tlPhaseArray: List[str]):
    return "SN" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def horizontalPhaseIs_Green(tlPhaseArray: List[str]):
    return "H" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def horizontalPhaseIs_Yellow(tlPhaseArray: List[str]):
    return "H" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def eastWestPhaseIs_Green(tlPhaseArray: List[str]):
    return "EW" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def eastWestPhaseIs_Yellow(tlPhaseArray: List[str]):
    return "EW" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def westEastPhaseIs_Green(tlPhaseArray: List[str]):
    return "WE" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def westEastPhaseIs_Yellow(tlPhaseArray: List[str]):
    return "WE" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("S" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def horizontalPhaseIsLeftTurn_Green(tlPhaseArray: List[str]):
    return "H" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def horizontalPhaseIsLeftTurn_Yellow(tlPhaseArray: List[str]):
    return "H" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def eastWestPhaseIsLeftTurn_Green(tlPhaseArray: List[str]):
    return "EW" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def eastWestPhaseIsLeftTurn_Yellow(tlPhaseArray: List[str]):
    return "EW" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def westEastPhaseIsLeftTurn_Green(tlPhaseArray: List[str]):
    return "WE" == tlPhaseArray[0] and "G" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])


def westEastPhaseIsLeftTurn_Yellow(tlPhaseArray: List[str]):
    return "WE" == tlPhaseArray[0] and "Y" == tlPhaseArray[2] and ("L" == tlPhaseArray[1] or "SL" == tlPhaseArray[1])
#----------------------------- end -----------------------------#


#------------------- User-defined predicates --------------------#
def maxGreenPhaseTimeReached(phase: str, timeInPhase: float, maxTime: int):
    if phase == "G":
        return timeInPhase >= maxTime


def maxYellowPhaseTimeReached(phase: str, timeInPhase: float, maxTime: int):
    if phase == "Y":
        return timeInPhase >= maxTime
#----------------------------- end -----------------------------#


# RETURN LIST OF PREDICATE FUNCTIONS
def getPredicateList() -> List[str]:
    thisModule = sys.modules[__name__]  # Get reference to this module for next operation
    methodsDict = dict(inspect.getmembers(thisModule, predicate=inspect.isfunction))  # Get a dictionary with all methods (predicates) in this module

    # Remove all methods that are not predicates from dictionary
    methodsDict.pop("getPredicateList")
    methodsDict.pop("getRandomPredicate")
    methodsDict.pop("run")

    # Remove all user-defined predicates
    methodsDict.pop("maxGreenPhaseTimeReached")
    methodsDict.pop("maxYellowPhaseTimeReached")

    # Seperate methods/predicates from rest of data in dictionary into a list
    predicateList = []
    for predicate in methodsDict:
        predicateList.append(predicate)

    return predicateList


# RETURN RANDOM PREDICATE FROM LIST OF PREDICATE FUNCTIONS
def getRandomPredicate() -> str:
    predicateList = getPredicateList()
    return (predicateList[randrange(len(predicateList))])


def run() -> None:
    print("\nThe predicate list is:", getPredicateList())


if __name__ == "__main__":
    run()
