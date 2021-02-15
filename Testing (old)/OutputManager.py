import os
import sys
import optparse
import traci


from operator import attrgetter

def run(agentPools, avgGenTime, totalGenTime):
    avgGenRuntime = avgGenTime
    finalGenRuntime = totalGenTime

    # Create new output file and add generation runtime information 
    f = open("simOutputData", "w")
    f.write("Final Generation Stats\n\nGeneration runtime:" + str(finalGenRuntime) + "\nAverage Generation runtime:" + str(avgGenRuntime) + "\n---------------------------\n\n Best Individuals per Agent Pool\n")

    for ap in agentPools:
        actionSet = "" 
        for a in ap.getActionSet():
            actionSet += "," + a + " "        
        
        f.write("Agent Pool" + ap.getID() + "\n" + "This agent pool has an action set of:" + str(actionSet))
    
        individuals = ap.getIndividualsSet()
        individuals.sort
        topIndividual = min(individuals, key=attrgetter('fitness'))
        f.write("The top individual has a fitness of" + str(topIndividual.getFitness()) + "and its RS and RSint sets contain the following rules (formatted as \"<conditions>, <action>\"):\n\n RS:\n")
        
        ruleCount = 1
        for rule in topIndividual.getRS():
            cond = ""
            for c in rule.getConditions():
                cond += "," + c + " "
            
            f.write("Rule" + str(ruleCount) + ": <" + cond + ">, <" + str(rule.getAction()) + "> and rule has a weight of" + str(rule.getWeight()) + "\n\n")
            ruleCount += 1

        f.write("RSint:\n")
        ruleCount = 1
        for rule in topIndividual.getRSint():
            cond = ""
            for c in rule.getConditions():
                cond += "," + c + " "

            f.write("Rule" + str(ruleCount) + ": <" + cond + ">, <" + str(rule.getAction()) + "> and rule has a weight of" + str(rule.getWeight()) + "\n\n")
            ruleCount += 1

        f.write("*******\n")

if __name__ == "__main__":
    run()
