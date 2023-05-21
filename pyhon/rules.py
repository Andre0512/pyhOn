from dataclasses import dataclass
from typing import List, Dict, TYPE_CHECKING

from pyhon.parameter.enum import HonParameterEnum
from pyhon.parameter.range import HonParameterRange

if TYPE_CHECKING:
    from pyhon.commands import HonCommand


@dataclass
class HonRule:
    trigger_key: str
    trigger_value: str
    param_key: str
    param_value: str


class HonRuleSet:
    def __init__(self, command: "HonCommand", rule):
        self._command: "HonCommand" = command
        self._rules: Dict[str, List[HonRule]] = {}
        self._parse_rule(rule)

    def _parse_rule(self, rule):
        for entity_key, params in rule.items():
            entity_key = self._command.appliance.options.get(entity_key, entity_key)
            for trigger_key, values in params.items():
                trigger_key = trigger_key.replace("@", "")
                trigger_key = self._command.appliance.options.get(
                    trigger_key, trigger_key
                )
                for trigger_value, entity_value in values.items():
                    if entity_value.get("fixedValue") == f"@{entity_key}":
                        continue
                    self._rules.setdefault(trigger_key, []).append(
                        HonRule(
                            trigger_key,
                            trigger_value,
                            entity_key,
                            entity_value.get("fixedValue"),
                        )
                    )

    def patch(self):
        for name, parameter in self._command.parameters.items():
            if name not in self._rules:
                continue
            for data in self._rules.get(name):

                def apply(rule):
                    if param := self._command.parameters.get(rule.param_key):
                        if isinstance(param, HonParameterEnum) and set(
                            param.values
                        ) != {str(rule.param_value)}:
                            param.values = [str(rule.param_value)]
                        elif isinstance(param, HonParameterRange):
                            param.value = float(rule.param_value)
                            return
                        param.value = str(rule.param_value)

                parameter.add_trigger(data.trigger_value, apply, data)
