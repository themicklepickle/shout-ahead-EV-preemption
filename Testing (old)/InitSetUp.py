# This script creates all the agents

import os
import sys
import optparse
import re

from TrafficLight import TrafficLight
from AgentPool import AgentPool
from Rule import Rule

def run(sumoNetworkName, minIndividualRunsPerGen):
    tlAgentPoolList = []
    trafficLightDict = {}
    userDefinedRules = []
    edgePartners = {}
    communicationPartners = {}
        
        # Parse user defined rules file and create rules for each
    f = open("UserDefinedRules.txt", "r")
        # Parse file to gather information about traffic lights, and instantiate their objects
    for x in f:
            # Ignore comment sections of input file
        if "//" in x:
            continue
            # For each user defined rule, create a rule with its conditions
        elif "udr" in x:
            ruleComponents = x.split(": ")
            ruleComponents = ruleComponents[1].split()
            #userDefinedRules.append(Rule(-1, [ruleComponents[0]], -1, None)) # User defined rules have only defined conditions; actions are predefined in Driver.py and they apply to all Agent Pools
            # print("The rule being added is:", ruleComponents[0], ".")
    f.close() # Close file before moving on

        
        # Get SUMO network file to parse
    # fileName = input("Please enter the name of the desired network file: ")

#ADD error checking for input (ensure it's a valid network file)

    
    f = open(sumoNetworkName, "r")                                     # Open desired file
    
    lanes = []
    trafficLights = []
    tlPhases = {}
    # Parse file to gather information about traffic lights, and instantiate their objects
    for x in f:
            # Create an action set dictionary for each traffic light
        if "<tlLogic" in x:
            getTLName = x.split("id=\"")
            tlNameArray = getTLName[1].split("\"")
            tlPhases[tlNameArray[0]] = []
                
                # Count number of phases/actions a TL has; loop max is arbitrarily high given phase number uncertainty 
            for i in range(0, 1000):
                x = f.readline()
                    # For each phase, record its phase name
                if "<phase" in x:
                    phaseNameSplit = x.split("name=")
                    phaseName = phaseNameSplit[1].split("\"")
                    tlPhases[tlNameArray[0]].append(phaseName[1])
                else:
                    break

            # Gather info about individual traffic lights
        elif "<junction" and "type=\"traffic_light\"" in x:
                # Isolate individual TLs
            temp = x.split("id=\"")
            trafficLightName = temp[1].split("\"")                      # Traffic Light name

                # Get all lanes controlled by TL
            splitForlanes = temp[1].split("incLanes=\"")
            lanesBulk = splitForlanes[1].split("\"")
            lanesSplit = lanesBulk[0].split()

                # Split lanes into individual elements in a list
            for l in lanesSplit:
                lanes.append(l)

            trafficLights.append(TrafficLight(trafficLightName[0], lanes))
            lanes = []

        elif "<edge id=" in x and "function" not in x:
            isolateFrom = x.split("from=\"")
            isolateTo = x.split("to=\"")

            isolateFrom = isolateFrom[1].split("\"")
            fromJunction = isolateFrom[0]

            isolateTo = isolateTo[1].split("\"")
            toJunction = isolateTo[0]

                # Create new dictionary entry for junctions if they doesn't already exist
            if toJunction not in edgePartners:
                edgePartners[toJunction] = []          
            if fromJunction not in edgePartners:
                edgePartners[fromJunction] = []

                # Add edges to each others dictionary entries if not already there
            if fromJunction not in edgePartners[toJunction]:
                edgePartners[toJunction].append(fromJunction)            
            if toJunction not in edgePartners[fromJunction]:
                edgePartners[fromJunction].append(toJunction)

        else:
            continue
    
    f.close()                                                           # Close file once finished


        # Set number of phases for each traffic light
    for x in tlPhases:
        for tl in trafficLights:
            if x == tl.getName():
                tl.setPhases(tlPhases[x])
            
        # Create entries for traffic lights in the communicationPartners dict based on edgePartners data
    # for junction in edgePartners:
    #     print("Junction is", junction, "and edgePartners are", edgePartners)
    #     for t in trafficLights:
    #         if junction == t.getName():
    #             communicationPartners[t] = []
    
        # Create and assign agent pools; populate communicationPartners dictionary 
    agentPools = []
    for tl in trafficLights:
        for edge in tl.getEdges():
            edgeSplit = edge.split("2")
            endPoint = edgeSplit[1].split("_")
            if endPoint[0] == tl.getName():
                for otherTL in trafficLights:
                    if edgeSplit[0] == otherTL.getName() and otherTL not in tl.getCommunicationPartners():
                        tl.addCommunicationPartner(otherTL)
        print("Current light:", tl.getName(),"\nEdge goes to:", endPoint[0], "\nEdge comes from:", edgeSplit[0],"\n\n")

        apAssigned = False
            # If agent pool(s) already exist, check to see its ability to host the traffic light
        if len(agentPools) > 0:    
            for ap in agentPools:
                    # An agent pool can realistically host more than one traffic light iff at minimum all TL's using the pool share the same number of phases
                if tl.getPhases() == ap.getActionSet(): 
                    ap.addNewTrafficLight(tl)
                    #tl.assignToAgentPool(ap)
                    apAssigned = True
                    break
        
        if apAssigned == False:
            apID = "AP" + str(len(agentPools) + 1)                      # Construct new agent ID
            agentPool = AgentPool(apID, tl.getPhases(), minIndividualRunsPerGen, [tl])                 # Create a new agent pool for traffic light
            #tl.assignToAgentPool(agentPool)
            apAssigned = True

            agentPools.append(agentPool)                                # Add new pool to agent pools list

        #     # Determine a traffic light's communication partners
        # for p in edgePartners[tl.getName()]:
        #     for t in trafficLights:
        #         if p == t.getName():
        #             communicationPartners[tl].append(t)                # If edge partner is a traffic light, add it to tl's entry in communicationPartner 
        
        #tl.setCommunicationPartners(communicationPartners[tl])         # Set each TL's communication partners list
        
        #Finish the initialization of the agent pools
    for ap in agentPools:
        ap.finishSetUp()

    for tl in trafficLights:
        print(tl.getName(), "communicates with:", tl.getCommunicationPartners())
    return (userDefinedRules, trafficLights, agentPools)
    
# main entry point
if __name__ == "__main__":
    run("simpleNetwork.net.xml")