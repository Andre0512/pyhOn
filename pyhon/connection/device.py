from typing import Dict

from pyhon import const


class HonDevice:
    def __init__(self, mobile_id: str = "") -> None:
        self._app_version: str = const.APP_VERSION
        self._os_version: int = const.OS_VERSION
        self._os: str = const.OS
        self._device_model: str = const.DEVICE_MODEL
        self._mobile_id: str = mobile_id or const.MOBILE_ID

    @property
    def app_version(self) -> str:
        return self._app_version

    @property
    def os_version(self) -> int:
        return self._os_version

    @property
    def os_type(self) -> str:
        return self._os

    @property
    def device_model(self) -> str:
        return self._device_model

    @property
    def mobile_id(self) -> str:
        return self._mobile_id

    def get(self, mobile: bool = False) -> Dict[str, str | int]:
        result: Dict[str, str | int] = {
            "appVersion": self.app_version,
            "mobileId": self.mobile_id,
            "os": self.os_type,
            "osVersion": self.os_version,
            "deviceModel": self.device_model,
        }
        if mobile:
            result |= {"mobileOs": result.pop("os", "")}
        return result
