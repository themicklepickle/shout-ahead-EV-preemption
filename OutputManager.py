import os
import sys
import optparse
import traci


from operator import attrgetter


def run(agentPools, avgGenTime, totalGenTime, generations, totalGenerations, folderName):
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
        actionSet = ""
        for a in ap.getActionSet()[:-1]:
            actionSet += f"{a}, "
        actionSet += ap.getActionSet()[-1]

        f.write(f"Agent Pool {ap.getID()}\n")
        f.write(f"This agent pool has an action set of: {actionSet}\n")

        individuals = ap.getIndividualsSet()
        individuals.sort
        topIndividual = min(individuals, key=attrgetter('fitness'))
        f.write(f"The top individual has a fitness of {topIndividual.getFitness()} and its RS and RSint sets contain the following rules (formatted as \"<conditions>, <action>\"):\n\n")

        f.write("RS:\n")
        ruleCount = 1
        for rule in topIndividual.getRS():
            cond = ""
            for c in rule.getConditions()[:-1]:
                cond += f"{c}, "
            cond += rule.getConditions()[-1]

            f.write(f"RS Rule {ruleCount}: <{cond}> , <{rule.getAction()}> and rule has a weight of {rule.getWeight()}\n\n")
            ruleCount += 1

        f.write("RSint:\n")
        ruleCount = 1
        for rule in topIndividual.getRSint():
            cond = ""
            for c in rule.getConditions()[:-1]:
                cond += f"{c}, "
            cond += rule.getConditions()[-1]

            f.write(f"RSint Rule {ruleCount}: <{cond}> , <{rule.getAction()}> and rule has a weight of {rule.getWeight()}\n\n")
            ruleCount += 1

        f.write("*******\n")


if __name__ == "__main__":
    run()
