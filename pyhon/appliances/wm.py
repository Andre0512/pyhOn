class Appliance:
    def data(self, data):
        if data["attributes"]["lastConnEvent"]["category"] == "DISCONNECTED":
            data["attributes"]["parameters"]["machMode"] = "0"
        data["active"] = bool(data.get("attributes", {}).get("activity"))
        data["pause"] = data["attributes"]["parameters"]["machMode"] == "3"
        return data

    def settings(self, settings):
        return settings
