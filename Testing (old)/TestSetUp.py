import os, sys, optparse, re
import InitSetUp

global sumoNetworkName
sumoNetworkName = "simpleNetwork.net.xml"
agentPool1 = "AP1.txt"
agentPool2 = "AP2.txt"
agentPool3 = "AP3.txt"

def run():   
    setUpTuple = InitSetUp.run(sumoNetworkName, 1)
    


   