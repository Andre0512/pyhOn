from pyhon.appliances.base import ApplianceBase


class Appliance(ApplianceBase):
    def attributes(self, data):
        data = super().attributes(data)
        if data["lastConnEvent"]["category"] == "DISCONNECTED":
            data["parameters"]["temp"] = "0"
            data["parameters"]["onOffStatus"] = "0"
            data["parameters"]["remoteCtrValid"] = "0"
            data["parameters"]["remainingTimeMM"] = "0"

        data["active"] = data["parameters"]["onOffStatus"] == "1"

        if program := int(data["parameters"]["prCode"]):
            ids = self.parent.settings["startProgram.program"].ids
            data["programName"] = ids.get(program, "")

        return data
