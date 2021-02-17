from __future__ import annotations

from operator import attrgetter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from AgentPool import AgentPool
    from Database import Database


def run(agentPools: List[AgentPool], generationRuntimes: List[float], episodeRuntimes: List[float], database: Database):
    genTime = generationRuntimes[-1]
    averageGenTime = sum(generationRuntimes) / len(generationRuntimes)
    generations = len(generationRuntimes)
    averageEpisodeTime = sum(episodeRuntimes) / len(episodeRuntimes)
    episodes = len(episodeRuntimes)

    # Create new output file and add generation runtime information
    outputData = {
        "stats": {
            "genTime": genTime,
            "averageGenTime": averageGenTime,
            "averageEpisodeTime": averageEpisodeTime,
            "generations": generations,
            "episodes": episodes,
        }
    }
    bestIndividuals = {}

    for ap in agentPools:
        individuals = ap.getIndividualsSet()
        topIndividual = min(individuals, key=attrgetter('fitness'))

        bestIndividuals[ap.getID()] = topIndividual.getJSON()

    outputData["bestIndividuals"] = bestIndividuals

    database.storeOutput(outputData)

    if database:
        agentPoolData = [i.getJSON() for i in ap.getIndividualsSet()]
        database.updateAgentPool(ap.getID(), agentPoolData, "new")


if __name__ == "__main__":
    run()
