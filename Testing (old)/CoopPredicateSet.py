import os
import sys
import optparse
import inspect
from random import randrange

#------------------------ intendedAction predicates -------------------------#
# def intendedActionIs_H_S_G(action):
#     if action == "H_S_G":
#         return True
#     else:
#         return False

# def intendedActionIs_H_S_Y(action):
#     if action == "H_S_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_H_L_G(action):
#     if action == "H_L_G":
#         return True
#     else:
#         return False

# def intendedActionIs_H_L_Y(action):
#     if action == "H_L_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_V_S_G(action):
#     if action == "V_S_G":
#         return True
#     else:
#         return False

# def intendedActionIs_V_S_Y(action):
#     if action == "V_S_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_V_L_G(action):
#     if action == "V_L_G":
#         return True
#     else:
#         return False

# def intendedActionIs_V_L_Y(action):
#     if action == "V_L_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_NS_S_G(action):
#     if action == "NS_S_G":
#         return True
#     else:
#         return False

# def intendedActionIs_NS_S_Y(action):
#     if action == "NS_S_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_NS_SL_G(action):
#     if action == "NS_S_G":
#         return True
#     else:
#         return False

# def intendedActionIs_NS_SL_Y(action):
#     if action == "NS_S_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_NS_L_G(action):
#     if action == "NS_L_G":
#         return True
#     else:
#         return False

# def intendedActionIs_NS_L_Y(action):
#     if action == "NS_L_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_SN_S_G(action):
#     if action == "SN_S_G":
#         return True
#     else:
#         return False

# def intendedActionIs_SN_S_Y(action):
#     if action == "SN_S_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_SN_SL_G(action):
#     if action == "SN_SL_G":
#         return True
#     else:
#         return False

# def intendedActionIs_SN_S_Y(action):
#     if action == "SN_SL_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_SN_L_G(action):
#     if action == "SN_L_G":
#         return True
#     else:
#         return False

# def intendedActionIs_SN_L_Y(action):
#     if action == "SN_L_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_EW_S_G(action):
#     if action == "EW_S_G":
#         return True
#     else:
#         return False

# def intendedActionIs_EW_S_Y(action):
#     if action == "EW_S_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_EW_SL_G(action):
#     if action == "EW_S_G":
#         return True
#     else:
#         return False

# def intendedActionIs_EW_SL_Y(action):
#     if action == "EW_S_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_EW_L_G(action):
#     if action == "EW_L_G":
#         return True
#     else:
#         return False

# def intendedActionIs_EW_L_Y(action):
#     if action == "EW_L_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_WE_S_G(action):
#     if action == "WE_S_G":
#         return True
#     else:
#         return False

# def intendedActionIs_WE_S_Y(action):
#     if action == "WE_S_Y":
#         return True
#     else:
#         return False

# def intendedActionIs_WE_SL_G(action):
#     if action == "WE_SL_G":
#         return True
#     else:
#         return False

# def intendedActionIs_WE_SL_Y(action):
#     if action == "WE_SL_Y":
#         return True
#     else:
#         return False
        
# def intendedActionIs_WE_L_G(action):
#     if action == "WE_L_G":
#         return True
#     else:
#         return False

# def intendedActionIs_WE_L_Y(action):
#     if action == "WE_L_Y":
#         return True
#     else:
#         return False       
#---------------------------------- end ---------------------------------------#

#------------------- timeSinceLastCommunication predicates --------------------#
def timeSinceCommunication_0(timeSinceCommunication):
    if timeSinceCommunication == 0:
        return True
    else:
        return False

def timeSinceCommunication_0_5(timeSinceCommunication):
    if 0 < timeSinceCommunication < 5:
        return True
    else:
        return False

def timeSinceCommunication_5_10(timeSinceCommunication):
    if 5 < timeSinceCommunication < 10:
        return True
    else:
        return False

def timeSinceCommunication_10_15(timeSinceCommunication):
    if 10 < timeSinceCommunication < 15:
        return True
    else:
        return False

def timeSinceCommunication_15_20(timeSinceCommunication):
    if 15 < timeSinceCommunication < 20:
        return True
    else:
        return False

def timeSinceCommunication_20_25(timeSinceCommunication):
    if 20 < timeSinceCommunication < 25:
        return True
    else:
        return False
#---------------------------------- end ----------------------------------#

    # EVALUATES VALIDITY OF A CUSTOM PREDICATE RELATIVE TO A COMMUNICATED INTENTION
def customPredicate(predicate, intention):
    predicate = predicate.split("_", 1)

    if predicate[0] == intention.getTrafficLight().getName() and predicate[1] == intention.getAction():
        # print("predicate[0] is", predicate[0], "and the traffic light that sent the intention is", intention.getTrafficLight().getName())
        # print("predicate[1] is", predicate[1], "and the intended action is", intention.getAction())
        return True
    else:
        return False

    # RETURN LIST OF PREDICATE FUNCTIONS AS DEFINED ABOVE
def getPredicateSet(agentPool):
    thisModule = sys.modules[__name__] # Get reference to this module for next operation
    methodsDict = dict(inspect.getmembers(thisModule, predicate=inspect.isfunction)) # Get a dictionary with all methods (predicates) in this module
        # Remove all methods that are not predicates from dictionary 
    methodsDict.pop("getPredicateSet")
    methodsDict.pop("getRandomPredicate") 
    methodsDict.pop("getPredicateSetFromFile")
    methodsDict.pop("getAgentSpecificPredicates")
    #methodsDict.pop("run")

        # Seperate methods/predicates from rest of data in dictionary into a list
    predicateList = []
    for predicate in methodsDict:
        predicateList.append(predicate)
    
    predicateList = predicateList + getAgentSpecificPredicates(agentPool)
    
    #print("Getting predicate set for", agentPool.getID(), "\n\n\n")
    #print("Predicate set contains", predicateList)
    return predicateList
    
    # RETURN LIST OF PREDICATE FUNCTIONS FROM AN INPUT FILE
def getPredicateSetFromFile(file):
    predicateList = []
    f = open(file, "r")                                     # Open desired file
    for x in f:
        if "//" in x:
            continue
        elif x.strip() == "":
            continue
        else:
            pred = x.split("\n")
            predicateList.append(pred[0])
    
    return predicateList

    # RETURN RANDOM PREDICATE FROM LIST OF PREDICATE FUNCTIONS
def getRandomPredicate(agentPool):
    # Add some ap specific stuff here
    predicateList = getPredicateSet(agentPool)
    return predicateList[randrange(len(predicateList))]

def getAgentSpecificPredicates(agentPool):
    customPredicates = []
    #print(agentPool.getID(), "(", agentPool, ") has the following assigned traffic lights:", agentPool.getAssignedTrafficLights())
    for tl in agentPool.getAssignedTrafficLights():
        #print(tl.getName(), "has the following communication partners:", tl.getCommunicationPartners())
        for partner in tl.getCommunicationPartners():
            for action in partner.getAgentPool().getActionSet():
                pred = partner.getName() + "_" + action
                customPredicates.append(pred)
    #print("Custom predicates are", customPredicates)
    return customPredicates

# def run():
#      print("\nThe predicate list is:", getPredicateSetFromFile("predicatesForRSint.txt"))

# if __name__ == "__main__":
#     run()