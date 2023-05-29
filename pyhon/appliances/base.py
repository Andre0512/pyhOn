class ApplianceBase:
    def __init__(self, appliance):
        self.parent = appliance

    def data(self, data):
        program_name = "No Program"
        if program := int(data["attributes"]["parameters"].get("prCode", "0")):
            if ids := self.parent.settings["startProgram.program"].ids:
                program_name = ids.get(program, program_name)
        data["programName"] = program_name

    def settings(self, settings):
        return settings
