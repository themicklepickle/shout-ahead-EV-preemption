from random import random, randint, choice, shuffle
from textwrap import dedent
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

    def getVehicleXML(self, id, depart, EVType, edges) -> str:
        return dedent(f"""\
        <vehicle id="{id}" depart="{depart}"{EVType}>
            <route edges="{edges}"/>
        </vehicle>
        """)

    def alterFlow(self, IDNumber, trafficFlowFolderName):
        with open(f"traffic_flows/{trafficFlowFolderName}/routes.rou.xml") as f:
            lines = f.readlines()
        IDs = [line.split('"')[1] for line in lines if "vehicle " in line]
        edges = [line.split('"')[1] for line in lines if "route " in line]
        types = [' type="' + line.split('"')[5] + '"' if "type" in line else "" for line in lines]

        shuffle(edges)
        shuffle(types)

        with open(f"traffic_flows/evaluation/routes{IDNumber}.rou.xml", "w") as f:
            f.write(self.getHeader())
            for id, startTime, type_, edge in zip(IDs, IDs, types, edges):
                f.write(self.getVehicleXML(id, startTime, type_, edge))
            f.write(self.getFooter())

    def setupAllTestingTrafficFlows(self, numberOfTrafficFlows, trafficFlowFolderName):
        for i in range(numberOfTrafficFlows):
            self.alterFlow(i, trafficFlowFolderName)


if __name__ == "__main__":
    setup = EvaluationSetup()
    setup.setupAllTestingTrafficFlows(1000, "EV Traffic Flow 225")
