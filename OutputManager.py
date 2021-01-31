from __future__ import annotations

from operator import attrgetter

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List
    from AgentPool import AgentPool


def run(agentPools: List[AgentPool], avgGenTime: float, totalGenTime: float, generations: int, totalGenerations: int, folderName: str):
    avgGenRuntime = avgGenTime
    finalGenRuntime = totalGenTime

    # Create new output file and add generation runtime information
    if generations + 1 < totalGenerations:
        f = open(f"log/{folderName}/gen_{generations}/simOutputData.txt", "w")
        f.write(f"Generation {generations} Stats\n\n")
    else:
        f = open(f"log/{folderName}/simOutputData.txt", "w")
        f.write("Final Generation Stats\n\n")

    f.write(f"Generation runtime: {finalGenRuntime}\n")
    f.write(f"Average Generation runtime: {avgGenRuntime}")
    f.write("\n---------------------------\n\n")
    f.write("Best Individuals per Agent Pool\n")

    for ap in agentPools:
        f.write(f"Agent Pool {ap.getID()}\n")
        f.write(f"This agent pool has an action set of: {', '.join(ap.getActionSet())}\n")

        individuals = ap.getIndividualsSet()
        individuals.sort
        topIndividual = min(individuals, key=attrgetter('fitness'))
        f.write(f"The top individual has a fitness of {topIndividual.getFitness()}\n")

        f.write("RS:\n")
        for rule in topIndividual.getRS():
            f.write(rule)

        f.write("RSint:\n")
        for rule in topIndividual.getRSint():
            f.write(rule)

        f.write("RSev:\n")
        for rule in topIndividual.getRSev():
            f.write(rule)

        f.write("*******\n")


if __name__ == "__main__":
    run()
