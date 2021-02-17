from __future__ import annotations

from TrafficLight import TrafficLight
from AgentPool import AgentPool

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Dict
    from Rule import Rule


def run(sumoNetworkName: str, minIndividualRunsPerGen: int, useShoutahead: bool, useEVCoopPredicates: bool):
    userDefinedRules: List[Rule] = []
    edgePartners: Dict[str, List[str]] = {}

    f = open(sumoNetworkName, "r")  # Open desired file

    lanes: List[str] = []
    trafficLights: List[TrafficLight] = []
    tlPhases: Dict[str, List[str]] = {}

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
            trafficLightName = temp[1].split("\"")  # Traffic Light name

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

    f.close()  # Close file once finished

    # Set number of phases for each traffic light
    for x in tlPhases:
        for tl in trafficLights:
            if x == tl.getName():
                tl.setPhases(tlPhases[x])

    # Create and assign agent pools; populate communicationPartners dictionary
    agentPools: List[AgentPool] = []
    for tl in trafficLights:
        for edge in tl.getEdges():
            edgeSplit = edge.split("2")
            endPoint = edgeSplit[1].split("_")
            if endPoint[0] == tl.getName():
                for otherTL in trafficLights:
                    if edgeSplit[0] == otherTL.getName() and otherTL not in tl.getCommunicationPartners():
                        tl.addCommunicationPartner(otherTL)

        apAssigned = False
        # If agent pool(s) already exist, check to see its ability to host the traffic light
        if len(agentPools) > 0:
            for ap in agentPools:
                # An agent pool can realistically host more than one traffic light iff at minimum all TL's using the pool share the same number of phases
                if tl.getPhases() == ap.getActionSet():
                    ap.addNewTrafficLight(tl)
                    apAssigned = True
                    break

        if apAssigned == False:
            apID = "AP" + str(len(agentPools) + 1)  # Construct new agent ID
            agentPool = AgentPool(apID, tl.getPhases(), minIndividualRunsPerGen, [tl])  # Create a new agent pool for traffic light
            # tl.assignToAgentPool(agentPool)
            apAssigned = True

            agentPools.append(agentPool)  # Add new pool to agent pools list

    return (userDefinedRules, trafficLights, agentPools)


# main entry point
if __name__ == "__main__":
    run("simpleNetwork.net.xml", 5, True)
