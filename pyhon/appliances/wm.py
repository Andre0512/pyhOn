class Appliance:
    def __init__(self, data):
        self._data = data

    def get(self):
        if self._data["lastConnEvent.category"] == "DISCONNECTED":
            self._data["machMode"] = "0"
        return self._data
