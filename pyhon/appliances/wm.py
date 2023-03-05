class Appliance:
    def __init__(self, data):
        self._data = data

    def get(self):
        self._data["connected"] = self._data["lastConnEvent.category"] == "CONNECTED"
        return self._data
