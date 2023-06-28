from datetime import datetime, timedelta
from typing import Optional, Final, Dict

from pyhon.helper import str_to_float


class HonAttribute:
    _LOCK_TIMEOUT: Final = 10

    def __init__(self, data: Dict[str, str] | str):
        self._value: str = ""
        self._last_update: Optional[datetime] = None
        self._lock_timestamp: Optional[datetime] = None
        self.update(data)

    @property
    def value(self) -> float | str:
        """Attribute value"""
        try:
            return str_to_float(self._value)
        except ValueError:
            return self._value

    @value.setter
    def value(self, value: str) -> None:
        self._value = value

    @property
    def last_update(self) -> Optional[datetime]:
        """Timestamp of last api update"""
        return self._last_update

    @property
    def lock(self) -> bool:
        """Shows if value changes are forbidden"""
        if not self._lock_timestamp:
            return False
        lock_until = self._lock_timestamp + timedelta(seconds=self._LOCK_TIMEOUT)
        return lock_until >= datetime.utcnow()

    def update(self, data: Dict[str, str] | str, shield: bool = False) -> bool:
        if self.lock and not shield:
            return False
        if shield:
            self._lock_timestamp = datetime.utcnow()
        if isinstance(data, str):
            self.value = data
            return True
        self.value = data.get("parNewVal", "")
        if last_update := data.get("lastUpdate"):
            try:
                self._last_update = datetime.fromisoformat(last_update)
            except ValueError:
                self._last_update = None
        return True

    def __str__(self) -> str:
        return self._value
