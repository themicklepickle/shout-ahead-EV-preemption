class EmergencyVehicle:
    def __init__(self, ID=None, speed=None, distance=None, lane=None, queue=None, trafficDensity=None):
        self.ID = ID
        self.speed = speed
        self.distance = distance
        self.lane = lane
        self.queue = queue
        self.trafficDensity = trafficDensity

    def getID(self):
        return self.ID

    def setID(self, ID):
        self.ID = ID

    def getSpeed(self):
        return self.speed

    def setSpeed(self, speed):
        self.speed = speed

    def getDistance(self):
        return self.distance

    def setDistance(self, distance):
        self.distance = distance

    def getLane(self):
        return self.lane

    def setLane(self, lane):
        self.lane = lane

    def getQueue(self):
        return self.queue

    def setQueue(self, queue):
        self.queue = queue

    def getTrafficDensity(self):
        if self.queue is None or self.distance is None:
            return None

        if self.distance == 0:
            self.trafficDensity = self.queue / 2.2250738585072014e-308
        else:
            self.trafficDensity = self.queue / self.distance

        self.trafficDensity *= 1000  # multiply by 1000 to give a better range
