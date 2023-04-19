class Appliance:
    def data(self, data):
        if data["attributes"]["lastConnEvent"]["category"] == "DISCONNECTED":
            data["attributes"]["parameters"]["temp"] = "0"
            data["attributes"]["parameters"]["onOffStatus"] = "0"
            data["attributes"]["parameters"]["remoteCtrValid"] = "0"
            data["attributes"]["parameters"]["remainingTimeMM"] = "0"

        data["active"] = data["attributes"]["parameters"]["onOffStatus"] == "1"

        return data

    def settings(self, settings):
        return settings
