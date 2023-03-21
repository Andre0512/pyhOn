class Appliance:
    def __init__(self, data):
        self._data = data

    def get(self):
        if self._data["attributes"]["lastConnEvent"]["category"] == "DISCONNECTED":
            self._data["attributes"]["parameters"]["machMode"] = "0"
        self._data["active"] = bool(self._data.get("activity"))
        self._data["pause"] = self._data["attributes"]["parameters"]["machMode"] == "3"
        return self._data
