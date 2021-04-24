import requests


class Status:
    def __init__(self, id: str):
        self.id = id
        self.url = "https://mlstatus.herokuapp.com/"

    def __del__(self):
        self.terminate()

    def initialize(self):
        requests.post(self.url + "initialize", {
            "_id": self.id
        })

    def update(self, key: str, val):
        requests.post(self.url + "update", {
            "_id": self.id,
            key: val
        })

    def terminate(self):
        requests.post(self.url + "terminate", {
            "_id": self.id
        })
