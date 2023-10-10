from typing import Dict, Any, List, Tuple, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from pyhon.rules import HonRule


class HonParameter:
    def __init__(self, key: str, attributes: Dict[str, Any], group: str) -> None:
        self._key = key
        self._attributes = attributes
        self._category: str = ""
        self._typology: str = ""
        self._mandatory: int = 0
        self._value: str | float = ""
        self._group: str = group
        self._triggers: Dict[
            str, List[Tuple[Callable[["HonRule"], None], "HonRule"]]
        ] = {}
        self._set_attributes()

    def _set_attributes(self) -> None:
        self._category = self._attributes.get("category", "")
        self._typology = self._attributes.get("typology", "")
        self._mandatory = self._attributes.get("mandatory", 0)

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> str | float:
        return self._value if self._value is not None else "0"

    @value.setter
    def value(self, value: str | float) -> None:
        self._value = value
        self.check_trigger(value)

    @property
    def intern_value(self) -> str:
        return str(self.value)

    @property
    def values(self) -> List[str]:
        return [str(self.value)]

    @property
    def category(self) -> str:
        return self._category

    @property
    def typology(self) -> str:
        return self._typology

    @property
    def mandatory(self) -> int:
        return self._mandatory

    @property
    def group(self) -> str:
        return self._group

    def add_trigger(
        self, value: str, func: Callable[["HonRule"], None], data: "HonRule"
    ) -> None:
        if self._value == value:
            func(data)
        self._triggers.setdefault(value, []).append((func, data))

    def check_trigger(self, value: str | float) -> None:
        triggers = {str(k).lower(): v for k, v in self._triggers.items()}
        if str(value).lower() in triggers:
            for trigger in triggers[str(value)]:
                func, args = trigger
                func(args)

    @property
    def triggers(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for value, rules in self._triggers.items():
            for _, rule in rules:
                if rule.extras:
                    param = result.setdefault(value, {})
                    for extra_key, extra_value in rule.extras.items():
                        param = param.setdefault(extra_key, {}).setdefault(
                            extra_value, {}
                        )
                else:
                    param = result.setdefault(value, {})
                if fixed_value := rule.param_data.get("fixedValue"):
                    param[rule.param_key] = fixed_value
                else:
                    param[rule.param_key] = rule.param_data.get("defaultValue", "")

        return result

    def reset(self) -> None:
        self._set_attributes()
