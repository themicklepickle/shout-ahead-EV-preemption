from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from network_components.TrafficLight import TrafficLight


class Intention:

    # INITIALIZE INTENTION WITH THE TRAFFIC LIGHT IT COMES FROM, THE INTENDED ACTION AND TIME CREATED
    def __init__(self, trafficLight: TrafficLight, action: int, timeWhenCreated: float):
        self.trafficLight = trafficLight
        self.action = action
        self.time = timeWhenCreated
        self.turn = self.time/5

        # RETURN CORRESPONDING TRAFFIC LIGHT OBJECT
    def getTrafficLight(self):
        return self.trafficLight

        # RETURN INTENDED ACTION
    def getAction(self):
        return self.trafficLight.getAgentPool().getActionSet()[self.action]

        # RETURN TIME CREATED
    def getTime(self):
        return self.time

        # RETURN TURN CREATED
    def getTurn(self):
        return self.turn
