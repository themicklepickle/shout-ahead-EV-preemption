import os
import sys

def run(fileName):
    fileName = input("Enter file name: ")
    f = open(fileName, "r")
    numOfRoutes = 0
    for x in f:
            # Ignore comment sections of input file
        if "id" in x:
            numOfRoutes += 1
    
    print("Number of routes:", numOfRoutes)

# main entry point
if __name__ == "__main__":
    run("simpleNetwork.net.xml")