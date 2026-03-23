class Detector:
    def __init__(self):
        self.keys = []

    def analyse(self, keys):
        self.keys = keys
        print("Analysing", len(keys), "keys:", self.keys)