class EmergencyVehicle:
    def __init__(self, ID: str = None, speed: float = None, distance: float = None, lane: str = None, queue: int = None, trafficDensity: float = None):
        self.ID: str = ID
        self.speed: float = speed
        self.distance: float = distance
        self.lane: str = lane
        self.queue: int = queue
        self.trafficDensity: float = trafficDensity

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

        return self.trafficDensity
