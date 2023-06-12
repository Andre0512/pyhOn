from datetime import datetime
from typing import Optional

from pyhon.helper import str_to_float


class HonAttribute:
    def __init__(self, data):
        self._value: str = ""
        self._last_update: Optional[datetime] = None
        self.update(data)

    @property
    def value(self) -> float | str:
        try:
            return str_to_float(self._value)
        except ValueError:
            return self._value

    @value.setter
    def value(self, value) -> None:
        self._value = value

    @property
    def last_update(self) -> Optional[datetime]:
        return self._last_update

    def update(self, data):
        self._value = data.get("parNewVal", "")
        if last_update := data.get("lastUpdate"):
            try:
                self._last_update = datetime.fromisoformat(last_update)
            except ValueError:
                self._last_update = None

    def __str__(self) -> str:
        return self._value
