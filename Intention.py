import os
import sys

class Intention:

        # INITIALIZE INTENTION WITH THE TRAFFIC LIGHT IT COMES FROM, THE INTENDED ACTION AND TIME CREATED
    def __init__ (self, trafficLight, action, timeWhenCreated):
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