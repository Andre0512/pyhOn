import json
import logging
import re
import secrets
import urllib
from urllib import parse

import aiohttp as aiohttp

from pyhon import const

_LOGGER = logging.getLogger()


class HonAuth:
    def __init__(self) -> None:
        self._framework = ""
        self._cognito_token = ""
        self._id_token = ""

    @property
    def cognito_token(self):
        return self._cognito_token

    @property
    def id_token(self):
        return self._id_token

    async def _get_frontdoor_url(self, session, email, password):
        data = {
            "message": {
                "actions": [
                    {
                        "id": "79;a",
                        "descriptor": "apex://LightningLoginCustomController/ACTION$login",
                        "callingDescriptor": "markup://c:loginForm",
                        "params": {
                            "username": email,
                            "password": password,
                            "startUrl": ""
                        }
                    }
                ]
            },
            "aura.context": {
                "mode": "PROD",
                "fwuid": self._framework,
                "app": "siteforce:loginApp2",
                "loaded": {"APPLICATION@markup://siteforce:loginApp2": "YtNc5oyHTOvavSB9Q4rtag"},
                "dn": [],
                "globals": {},
                "uad": False},
            "aura.pageURI": f"SmartHome/s/login/?language={const.LANGUAGE}",
            "aura.token": None}

        params = {"r": 3, "other.LightningLoginCustom.login": 1}
        async with session.post(
                const.AUTH_API + "/s/sfsites/aura",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data="&".join(f"{k}={json.dumps(v)}" for k, v in data.items()),
                params=params
        ) as response:
            if response.status != 200:
                _LOGGER.error("Unable to connect to the login service: %s\n%s", response.status, await response.text())
                return ""
            try:
                text = await response.text()
                return (await response.json())["events"][0]["attributes"]["values"]["url"]
            except json.JSONDecodeError:
                if framework := re.findall('clientOutOfSync.*?Expected: ([\\w-]+?) Actual: (.*?)"', text):
                    self._framework, actual = framework[0]
                    _LOGGER.debug('Framework update from "%s" to "%s"', self._framework, actual)
                    return await self._get_frontdoor_url(session, email, password)
                _LOGGER.error("Unable to retrieve the frontdoor URL. Message: " + text)
                return ""

    async def _prepare_login(self, session, email, password):
        if not (frontdoor_url := await self._get_frontdoor_url(session, email, password)):
            return False

        async with session.get(frontdoor_url) as resp:
            if resp.status != 200:
                _LOGGER.error("Unable to connect to the login service: %s", resp.status)
                return False

        params = {"retURL": "/SmartHome/apex/CustomCommunitiesLanding"}
        async with session.get(f"{const.AUTH_API}/apex/ProgressiveLogin", params=params) as resp:
            if resp.status != 200:
                _LOGGER.error("Unable to connect to the login service: %s", resp.status)
                return False
        return True

    async def _login(self, session):
        nonce = secrets.token_hex(16)
        nonce = f"{nonce[:8]}-{nonce[8:12]}-{nonce[12:16]}-{nonce[16:20]}-{nonce[20:]}"
        params = {
            "response_type": "token+id_token",
            "client_id": const.CLIENT_ID,
            "redirect_uri": urllib.parse.quote(f"{const.APP}://mobilesdk/detect/oauth/done"),
            "display": "touch",
            "scope": "api openid refresh_token web",
            "nonce": nonce
        }
        params = "&".join([f"{k}={v}" for k, v in params.items()])
        async with session.get(f"{const.AUTH_API}/services/oauth2/authorize?{params}") as resp:
            if id_token := re.findall("id_token=(.*?)&", await resp.text()):
                self._id_token = id_token[0]
                return True
        return False

    async def authorize(self, email, password, mobile_id):
        async with aiohttp.ClientSession() as session:
            if not await self._prepare_login(session, email, password):
                return False
            if not await self._login(session):
                return False

            post_headers = {"Content-Type": "application/json", "id-token": self._id_token}
            data = {"appVersion": const.APP_VERSION, "mobileId": mobile_id, "osVersion": const.OS_VERSION,
                    "os": const.OS, "deviceModel": const.DEVICE_MODEL}
            async with session.post(f"{const.API_URL}/auth/v1/login", headers=post_headers, json=data) as resp:
                try:
                    json_data = await resp.json()
                except json.JSONDecodeError:
                    _LOGGER.error("No JSON Data after POST: %s", await resp.text())
                    return False
                self._cognito_token = json_data["cognitoUser"]["Token"]
        return True
