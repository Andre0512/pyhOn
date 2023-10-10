from dataclasses import dataclass
from typing import List, Dict, TYPE_CHECKING, Any, Optional

from pyhon.parameter.enum import HonParameterEnum
from pyhon.parameter.range import HonParameterRange
from pyhon.typedefs import Parameter

if TYPE_CHECKING:
    from pyhon.commands import HonCommand
    from pyhon.parameter.base import HonParameter


@dataclass
class HonRule:
    trigger_key: str
    trigger_value: str
    param_key: str
    param_data: Dict[str, Any]
    extras: Optional[Dict[str, str]] = None


class HonRuleSet:
    def __init__(self, command: "HonCommand", rule: Dict[str, Any]):
        self._command: "HonCommand" = command
        self._rules: Dict[str, List[HonRule]] = {}
        self._parse_rule(rule)

    @property
    def rules(self) -> Dict[str, List[HonRule]]:
        return self._rules

    def _parse_rule(self, rule: Dict[str, Any]) -> None:
        for param_key, params in rule.items():
            param_key = self._command.appliance.options.get(param_key, param_key)
            for trigger_key, trigger_data in params.items():
                self._parse_conditions(param_key, trigger_key, trigger_data)

    def _parse_conditions(
        self,
        param_key: str,
        trigger_key: str,
        trigger_data: Dict[str, Any],
        extra: Optional[Dict[str, str]] = None,
    ) -> None:
        trigger_key = trigger_key.replace("@", "")
        trigger_key = self._command.appliance.options.get(trigger_key, trigger_key)
        for multi_trigger_value, param_data in trigger_data.items():
            for trigger_value in multi_trigger_value.split("|"):
                if isinstance(param_data, dict) and "typology" in param_data:
                    self._create_rule(
                        param_key, trigger_key, trigger_value, param_data, extra
                    )
                elif isinstance(param_data, dict):
                    if extra is None:
                        extra = {}
                    extra[trigger_key] = trigger_value
                    for extra_key, extra_data in param_data.items():
                        self._parse_conditions(param_key, extra_key, extra_data, extra)
                else:
                    param_data = {"typology": "fixed", "fixedValue": param_data}
                    self._create_rule(
                        param_key, trigger_key, trigger_value, param_data, extra
                    )

    def _create_rule(
        self,
        param_key: str,
        trigger_key: str,
        trigger_value: str,
        param_data: Dict[str, Any],
        extras: Optional[Dict[str, str]] = None,
    ) -> None:
        if param_data.get("fixedValue") == f"@{param_key}":
            return
        self._rules.setdefault(trigger_key, []).append(
            HonRule(trigger_key, trigger_value, param_key, param_data, extras)
        )

    def _duplicate_for_extra_conditions(self) -> None:
        new: Dict[str, List[HonRule]] = {}
        for rules in self._rules.values():
            for rule in rules:
                if rule.extras is None:
                    continue
                for key, value in rule.extras.items():
                    extras = rule.extras.copy()
                    extras.pop(key)
                    extras[rule.trigger_key] = rule.trigger_value
                    new.setdefault(key, []).append(
                        HonRule(key, value, rule.param_key, rule.param_data, extras)
                    )
        for key, rules in new.items():
            for rule in rules:
                self._rules.setdefault(key, []).append(rule)

    def _extra_rules_matches(self, rule: HonRule) -> bool:
        if rule.extras:
            for key, value in rule.extras.items():
                if not self._command.parameters.get(key):
                    return False
                if str(self._command.parameters.get(key)) != str(value):
                    return False
        return True

    def _apply_fixed(self, param: Parameter, value: str | float) -> None:
        if isinstance(param, HonParameterEnum) and set(param.values) != {str(value)}:
            param.values = [str(value)]
            param.value = str(value)
        elif isinstance(param, HonParameterRange):
            if float(value) < param.min:
                param.min = float(value)
            elif float(value) > param.max:
                param.max = float(value)
            param.value = float(value)
            return
        param.value = str(value)

    def _apply_enum(self, param: Parameter, rule: HonRule) -> None:
        if not isinstance(param, HonParameterEnum):
            return
        if enum_values := rule.param_data.get("enumValues"):
            param.values = enum_values.split("|")
        if default_value := rule.param_data.get("defaultValue"):
            param.value = default_value

    def _add_trigger(self, parameter: "HonParameter", data: HonRule) -> None:
        def apply(rule: HonRule) -> None:
            if not self._extra_rules_matches(rule):
                return
            if not (param := self._command.parameters.get(rule.param_key)):
                return
            if fixed_value := rule.param_data.get("fixedValue", ""):
                self._apply_fixed(param, fixed_value)
            elif rule.param_data.get("typology") == "enum":
                self._apply_enum(param, rule)

        parameter.add_trigger(data.trigger_value, apply, data)

    def patch(self) -> None:
        self._duplicate_for_extra_conditions()
        for name, parameter in self._command.parameters.items():
            if name not in self._rules:
                continue
            for data in self._rules.get(name, []):
                self._add_trigger(parameter, data)
