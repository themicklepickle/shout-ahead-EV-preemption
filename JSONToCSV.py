import json
import csv

filename = "feb25"

with open(f"results/{filename}.json", "r") as f:
    apData = json.load(f)
fieldnames = [
    "generation",
    "simulationTime",
    "EVStops",
    "averageEVSpeed"
]
with open(f"results/{filename}.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in apData:
        writer.writerow(row)
