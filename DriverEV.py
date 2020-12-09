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
