#!/usr/bin/env python

import os
import sys
import optparse
import traci

import PredicateSet
import CoopPredicateSet
import EvolutionaryLearner
import ReinforcementLearner
from Rule import Rule
from Intention import Intention
from Driver import Driver
import time
from pprint import pprint


# NOTE: vehID in DriverEV.py refers to only the first element of the split,
#       whereas in Driver.py vehID was the split tuple

class DriverEV(Driver):
    def getState(self, trafficLight):
        state = {}
        leftTurnLane = ""
        for lane in trafficLight.getLanes():
            state[lane] = []

        # Loop to determine which vehicles are waiting at an intersection
        for vehID in traci.vehicle.getIDList():
            laneID = traci.vehicle.getLaneID(vehID)
            tlLanes = trafficLight.getLanes()
            identifer = ""

            # Operate only on vehicles in a lane controlled by traffic light
            if laneID in tlLanes:
                # Determine left turn lane if it exists
                if "_LTL" in laneID:
                    maxLaneNum = 0
                    for lane in tlLanes:
                        if lane == laneID:
                            laneSplit = lane.split("_")
                            if int(laneSplit[2]) > maxLaneNum:
                                leftTurnLane = lane

                # If vehicle is stopped, append relevant identifier to it
                if traci.vehicle.getSpeed(vehID) == 0:
                    if leftTurnLane == laneID:
                        identifer += "_Stopped_L"
                    else:
                        identifer += "_Stopped_S"

#------------------------------------ EV IDENTIFIER ------------------------------------#
                # If the vehicle is an EV, append relevant identifers to it
                # NOTE: EVs are not included in predicates for stopped vehicles, so the identifers are overidden
                if traci.vehicle.getVehicleClass(vehID.split("_")[0]) == "emergency":
                    if leftTurnLane == laneID:
                        identifer += "_EV_L"
                    else:
                        identifer += "_EV_S"  # TODO: change to the same as other predicates?

#---------------------------------- EV IDENTIFIER END ----------------------------------#

                state[laneID].append(vehID + identifer)

        return state

                        if "_Stopped_L" in veh:
                            vehIDSplit = veh.split("_")
                        if "_Stopped_S" in veh:
                            vehIDSplit = veh.split("_")
