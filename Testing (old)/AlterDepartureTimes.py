import os
import sys
from random import randrange
from random import randint

percentOfRouToChange = 0.5                              # Define in % the number of departure times you'd like altered (must be 0-1, 1 = 100%)
numberOfAlternateRoutes = 10                            # Define how many different altered routes you'd like

routesFilePath = "routes.rou.xml"                       # File name/path for routes.rou.xml; if blank, user will be prompted
tripsFilePath = ""                                      # File path for trips.trips.xml; if blank, user will be prompted
routesData = {}                                         # Dictionary to host deconstructed xml file

# Get input file path if none specified
#---------------------------
if routesFilePath == "":
    routesFilePath = input("Please enter the file path for the route file you'd like to alter: ")
#---------------------------

for newRouteCount in range(numberOfAlternateRoutes):
    # Deconstruct routes file into a Dictionary (key=departureTime/id, value=route)
    #---------------------------
    f = open(routesFilePath, "r")

    for row in f:
        if "<vehicle id=" in row:
            rowArray = row.split("depart=\"")
            idArray= rowArray[1].split(".00")
            rouID = idArray[0]
            
            row = f.readline()                                       # Read next line to get routes info
            
            rowArray = row.split("edges=\"")
            routeArray= rowArray[1].split("\"")
            routes = routeArray[0]
            routesData[int(rouID)] = (int(rouID), routes)

    f.close()
    #---------------------------


    # Alter departure times of a certain number of vehicles
    #---------------------------
    numOfVeh = len(routesData)
    numOfRouToAdjust = int(numOfVeh*percentOfRouToChange)
    indexesToAdjust = []                                                      # List of indexes adjusted so the same one isn't changed twice
    indexToAdjust = -1

    while indexToAdjust not in routesData.keys():
        indexToAdjust = randrange(0, list(routesData)[-1])                 # Get new random route to alter    

    indexesToAdjust.append(indexToAdjust)

    # Finish populating indexes to adjust 
    for i in range(numOfRouToAdjust-1):
        while indexToAdjust in indexesToAdjust or indexToAdjust not in routesData.keys():
            indexToAdjust = randrange(0, list(routesData)[-1])                 # Get new random route to alter    
        indexesToAdjust.append(indexToAdjust)

    for index in indexesToAdjust:
        changeValue = randint(-10, 10)                                          # How much will the departure time change by
        routes = routesData[index][1]                                   # Preserve routes
        
        if routesData[index][0] + changeValue < 0:
            newDepartureTime = 0
        elif routesData[index][0] + changeValue > 299:
            newDepartureTime = 299
        else:
            newDepartureTime = routesData[index][0] + changeValue           # Update departure value
        
        routesData[index] = (newDepartureTime, routes)                  # Update routes dictionary

    # values = list(routesData.values())
    # departureTimes = []
    # for valTuple in values:
    #     departureTimes.append(valTuple[0])
    # print(departureTimes)

    # Sort dictionary by value
    newRoutesData = {k: v for k, v in sorted(routesData.items(), key=lambda item: item[1])}

    # Reconstruct routes file with new data
    #---------------------------
    newFileName = "routes" + str(int(percentOfRouToChange*100)) + "_" + str(newRouteCount+1) + ".rou.xml"
    f = open(newFileName, "w")
    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\n\n")
    f.write("<routes  xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://sumo.dlr.de/xsd/routes_file.xsd\">\n")

        # For each entry in the routesData database, an XML representation is constructed with the data
    for rouID in newRoutesData:
        f.write("    <vehicle id=\"" + str(rouID) + "\" depart=\"" + str(routesData[rouID][0]) + ".00\">\n        <route edges=\"" + routesData[rouID][1] + "\"/>\n    </vehicle>\n")

    f.write("</routes>")
    f.close()

        # Make a config file for each new route
    newConfigFileName = "config_file_" + str(newRouteCount+1) + ".sumocfg"
    f = open(newConfigFileName, "w")
    f.write("<configuration>\n    <input>\n        <net-file value=\"simpleNetwork.net.xml\"/>\n        <route-files value=\"" + newFileName + "\"/>\n    </input>\n\n    <time>\n        <begin value=\"0\"/>\n    </time>\n\n</configuration>")
    f.close()
    #---------------------------

print("\nCreated", numberOfAlternateRoutes, "new route and config file(s) successfully!")

