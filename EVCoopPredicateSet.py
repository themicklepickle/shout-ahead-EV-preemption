from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from AgentPool import AgentPool


def timeSinceLastEVThrough(predicate: str, timeSinceLastEVThrough: float):
    bottom, top = [int(i) for i in predicate.split("_")[-2:]]

    # bottom of the range
    if top == -1:
        return timeSinceLastEVThrough == bottom

    # top of the range
    if bottom == -1:
        return timeSinceLastEVThrough > top

    # middle ranges
    return bottom < timeSinceLastEVThrough <= top


# RETURN LIST OF PREDICATE FUNCTIONS
def getPredicateSet(agentPool: AgentPool):
    predicateSet = getTimeSinceLastEVThroughPredicates(agentPool) + getEVApproachingPartnerPredicates(agentPool)

    return predicateSet


def getTimeSinceLastEVThroughPredicates(agentPool: AgentPool):
    ranges = [
        (0, -1),
        (0, 20),
        (20, 80),
        (80, 120),
        (120, 200),
        (200, 400),
        (-1, 400)
    ]
    customPredicates: List[str] = []
    for tl in agentPool.getAssignedTrafficLights():
        for partner in tl.getCommunicationPartners():
            for r in ranges:
                pred = f"timeSinceLastEVThrough_{partner.getName()}_{r[0]}_{r[1]}"
            customPredicates.append(pred)
    return customPredicates


def getEVApproachingPartnerPredicates(agentPool: AgentPool):
    customPredicates: List[str] = []
    for tl in agentPool.getAssignedTrafficLights():
        for partner in tl.getCommunicationPartners():
            pred = f"EVApproachingPartner_{partner.getName()}"
            customPredicates.append(pred)
    return customPredicates


def getPredicateTypes():
    return [
        "timeSinceLastEVThrough",
        "EVApproachingPartner"
    ]
