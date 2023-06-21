from pyhon.appliances.base import ApplianceBase


class Appliance(ApplianceBase):
    def attributes(self, data):
        data = super().attributes(data)
        if data.get("lastConnEvent", {}).get("category", "") == "DISCONNECTED":
            data["parameters"]["temp"].value = "0"
            data["parameters"]["onOffStatus"].value = "0"
            data["parameters"]["remoteCtrValid"].value = "0"
            data["parameters"]["remainingTimeMM"].value = "0"

        data["active"] = data["parameters"]["onOffStatus"] == "1"

        if program := int(data["parameters"]["prCode"]):
            ids = self.parent.settings["startProgram.program"].ids
            data["programName"] = ids.get(program, "")

        return data
