from typing import Dict, Any, List, Tuple, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from pyhon.rules import HonRule


class HonParameter:
    def __init__(self, key: str, attributes: Dict[str, Any], group: str) -> None:
        self._key = key
        self._category: str = attributes.get("category", "")
        self._typology: str = attributes.get("typology", "")
        self._mandatory: int = attributes.get("mandatory", 0)
        self._value: str | float = ""
        self._group: str = group
        self._triggers: Dict[str, List[Tuple[Callable, "HonRule"]]] = {}

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> str | float:
        return self._value if self._value is not None else "0"

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

    def add_trigger(self, value, func, data):
        if self._value == value:
            func(data)
        self._triggers.setdefault(value, []).append((func, data))

    def check_trigger(self, value) -> None:
        if str(value) in self._triggers:
            for trigger in self._triggers[str(value)]:
                func, args = trigger
                func(args)

    @property
    def triggers(self):
        result = {}
        for value, rules in self._triggers.items():
            result[value] = {rule.param_key: rule.param_value for _, rule in rules}
        return result
