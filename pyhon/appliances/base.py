class ApplianceBase:
    def __init__(self, appliance):
        self.parent = appliance

    def attributes(self, data):
        program_name = "No Program"
        if program := int(str(data.get("parameters", {}).get("prCode", "0"))):
            if start_cmd := self.parent.settings.get("startProgram.program"):
                if ids := start_cmd.ids:
                    program_name = ids.get(program, program_name)
        data["programName"] = program_name
        return data

    def settings(self, settings):
        return settings
