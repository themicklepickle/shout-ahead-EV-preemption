from random import random, randint, choice, randrange
from textwrap import dedent, indent
from pathlib import Path
from shutil import rmtree
from distutils.dir_util import copy_tree


class EvaluationSetup:
    def __init__(self) -> None:
        pass

    def setupEvaluationFolder(self) -> None:
        folderPath = "traffic_flows/evaluation"

        rmtree(folderPath, ignore_errors=True)  # clear folder
        Path(folderPath).mkdir(parents=True, exist_ok=True)  # create folder
        copy_tree("traffic_flows/Template/", folderPath)  # add config files

    def getValidEdges(self) -> None:
        with open("traffic_flows/Template/routes.rou.xml") as f:
            validEdges = [line.split('"')[1] for line in f.readlines() if "route " in line]
        with open("evaluation/validEdges.txt", "w") as f:
            f.write(indent("\n".join(validEdges), "+ ", lambda line: True))

    def getHeader(self) -> str:
        with open("evaluation/header.txt") as f:
            return f.read()

    def getFooter(self) -> str:
        with open("evaluation/footer.txt") as f:
            return f.read()

    def pickEdges(self) -> str:
        with open("evaluation/validEdges.txt") as f:
            validEdges = [line.strip() for line in f.readlines()]
        return choice(validEdges)

    def getVehicleXML(self, vehicle) -> str:
        id = depart = vehicle["startTime"]

        EVType = ""
        if vehicle["isEV"]:
            EVType = f' type="{choice(["FireTruck", "Ambulance", "PoliceCar"])}"'

        edges = self.pickEdges()

        return dedent(f"""\
        <vehicle id="{id}" depart="{depart}"{EVType}>
            <route edges="{edges}"/>
        </vehicle>
        """)

    def createTestingTrafficFlow(self, IDNumber, minVehicles,  maxVehicles, minStartTime, maxStartTime, percentEVs):
        numVehicles = randint(minVehicles, maxVehicles)

        # create a list of vehicle start times and whether or not they are EVs
        vehicles = []
        for _ in range(numVehicles):
            vehicles.append({
                "startTime": randint(minStartTime, maxStartTime),
                "isEV": random() <= percentEVs
            })

        # create file
        with open(f"traffic_flows/evaluation/routes{IDNumber}.rou.xml", "w") as f:
            f.write(self.getHeader())
            for vehicle in vehicles:
                f.write(self.getVehicleXML(vehicle))
            f.write(self.getFooter())

    def setupAllTestingTrafficFlows(self, numberOfTrafficFlows, *params):
        for i in range(numberOfTrafficFlows):
            self.createTestingTrafficFlow(i, *params)


if __name__ == "__main__":
    setup = EvaluationSetup()
    setup.setupAllTestingTrafficFlows(1000, 100, 225, 0, 300, 0.5)
