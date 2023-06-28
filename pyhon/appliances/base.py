from typing import Dict, Any, TYPE_CHECKING

from pyhon.parameter.program import HonParameterProgram

if TYPE_CHECKING:
    from pyhon.appliance import HonAppliance


class ApplianceBase:
    def __init__(self, appliance: "HonAppliance"):
        self.parent = appliance

    def attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        program_name = "No Program"
        if program := int(str(data.get("parameters", {}).get("prCode", "0"))):
            if start_cmd := self.parent.settings.get("startProgram.program"):
                if isinstance(start_cmd, HonParameterProgram) and (
                    ids := start_cmd.ids
                ):
                    program_name = ids.get(program, program_name)
        data["programName"] = program_name
        return data

    def settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        return settings
