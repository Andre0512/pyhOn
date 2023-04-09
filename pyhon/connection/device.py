import secrets

from pyhon import const


class HonDevice:
    def __init__(self):
        self._app_version = const.APP_VERSION
        self._os_version = const.OS_VERSION
        self._os = const.OS
        self._device_model = const.DEVICE_MODEL
        self._mobile_id = secrets.token_hex(8)

    @property
    def app_version(self):
        return self._app_version

    @property
    def os_version(self):
        return self._os_version

    @property
    def os(self):
        return self._os

    @property
    def device_model(self):
        return self._device_model

    @property
    def mobile_id(self):
        return self._mobile_id

    def get(self):
        return {
            "appVersion": self.app_version,
            "mobileId": self.mobile_id,
            "osVersion": self.os_version,
            "os": self.os,
            "deviceModel": self.device_model,
        }
