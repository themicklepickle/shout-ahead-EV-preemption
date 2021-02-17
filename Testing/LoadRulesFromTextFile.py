import json
with open("ThatOneActuallyGoodOutputForOnce.txt") as f:
    file = [line.strip() for line in f.readlines()]

ruleSetName = None
output = {}
ruleSetNames = ["RS", "RSint", "RSev"]
apNames = ["AP1", "AP2", "AP3"]
for ap in apNames:
    output[ap] = {}
    for ruleSetName in ruleSetNames:
        output[ap][ruleSetName] = []

for line in file:
    if line[:10] == "Agent Pool":
        apID = line[10:]
        continue
    if line.split(":")[0] in ruleSetNames:
        ruleSetName = line.split(":")[0]
        continue
    if line[:4] != "Rule":
        continue

    conditionSection = line.split("<")[1]
    conditionSection = conditionSection.split(">")[0]
    conditions = [cond.strip() for cond in conditionSection.split(",") if len(cond) > 1]

    action = int(line.split("<")[2][0])

    rule = {
        "type": ruleSetNames.index(ruleSetName),
        "conditions": conditions,
        "action": action
    }
    output[apID][ruleSetName].append(rule)


for ap in apNames:
    with open(f"rules/noEV/{ap}.json", "w") as f:
        json.dump(output[ap], f, indent=2)
