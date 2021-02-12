from __future__ import annotations

from operator import attrgetter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from AgentPool import AgentPool
    from Database import Database


def run(agentPools: List[AgentPool], avgGenTime: float, totalGenTime: float, database: Database):
    avgGenRuntime = avgGenTime
    finalGenRuntime = totalGenTime

    # Create new output file and add generation runtime information
    outputData = {
        "finalGenRunTime": finalGenRuntime,
        "averageGenRunTime": avgGenRuntime
    }
    bestIndividuals = {}

    for ap in agentPools:
        individuals = ap.getIndividualsSet()
        individuals.sort
        topIndividual = min(individuals, key=attrgetter('fitness'))

        bestIndividuals[ap.getID()] = topIndividual.getJSON()

    outputData["bestIndividuals"] = bestIndividuals

    database.storeOutput(outputData)


if __name__ == "__main__":
    run()
