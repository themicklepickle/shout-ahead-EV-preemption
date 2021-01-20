import sys


class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("log/out.txt", "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()
