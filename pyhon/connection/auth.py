import json
import logging
import re
import secrets
import urllib
from datetime import datetime, timedelta
from pprint import pformat
from urllib import parse
from urllib.parse import quote

from aiohttp import ClientResponse
from yarl import URL

from pyhon import const, exceptions
from pyhon.connection.handler.auth import HonAuthConnectionHandler

_LOGGER = logging.getLogger(__name__)


class HonAuth:
    _TOKEN_EXPIRES_AFTER_HOURS = 8
    _TOKEN_EXPIRE_WARNING_HOURS = 7

    def __init__(self, session, email, password, device) -> None:
        self._session = session
        self._request = HonAuthConnectionHandler(session)
        self._email = email
        self._password = password
        self._access_token = ""
        self._refresh_token = ""
        self._cognito_token = ""
        self._id_token = ""
        self._device = device
        self._expires: datetime = datetime.utcnow()

    @property
    def cognito_token(self) -> str:
        return self._cognito_token

    @property
    def id_token(self) -> str:
        return self._id_token

    @property
    def access_token(self) -> str:
        return self._access_token

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    def _check_token_expiration(self, hours: int) -> bool:
        return datetime.utcnow() >= self._expires + timedelta(hours=hours)

    @property
    def token_is_expired(self) -> bool:
        return self._check_token_expiration(self._TOKEN_EXPIRES_AFTER_HOURS)

    @property
    def token_expires_soon(self) -> bool:
        return self._check_token_expiration(self._TOKEN_EXPIRE_WARNING_HOURS)

    async def _error_logger(self, response: ClientResponse, fail: bool = True) -> None:
        output = "hOn Authentication Error\n"
        for i, (status, url) in enumerate(self._request.called_urls):
            output += f" {i + 1: 2d}     {status} - {url}\n"
        output += f"ERROR - {response.status} - {response.request_info.url}\n"
        output += f"{15 * '='} Response {15 * '='}\n{await response.text()}\n{40 * '='}"
        _LOGGER.error(output)
        if fail:
            raise exceptions.HonAuthenticationError("Can't login")

    def _generate_nonce(self) -> str:
        nonce = secrets.token_hex(16)
        return f"{nonce[:8]}-{nonce[8:12]}-{nonce[12:16]}-{nonce[16:20]}-{nonce[20:]}"

    async def _load_login(self):
        login_url = await self._introduce()
        login_url = await self._handle_redirects(login_url)
        return await self._login_url(login_url)

    async def _introduce(self) -> str:
        redirect_uri = urllib.parse.quote(f"{const.APP}://mobilesdk/detect/oauth/done")
        params = {
            "response_type": "token+id_token",
            "client_id": const.CLIENT_ID,
            "redirect_uri": redirect_uri,
            "display": "touch",
            "scope": "api openid refresh_token web",
            "nonce": self._generate_nonce(),
        }
        params = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{const.AUTH_API}/services/oauth2/authorize/expid_Login?{params}"
        async with self._request.get(url) as response:
            text = await response.text()
            self._expires = datetime.utcnow()
            if not (login_url := re.findall("url = '(.+?)'", text)):
                if "oauth/done#access_token=" in text:
                    self._parse_token_data(text)
                    raise exceptions.HonNoAuthenticationNeeded()
                await self._error_logger(response)
        return login_url[0]

    async def _manual_redirect(self, url: str) -> str:
        async with self._request.get(url, allow_redirects=False) as response:
            if not (new_location := response.headers.get("Location")):
                await self._error_logger(response)
        return new_location

    async def _handle_redirects(self, login_url) -> str:
        redirect1 = await self._manual_redirect(login_url)
        redirect2 = await self._manual_redirect(redirect1)
        return f"{redirect2}&System=IoT_Mobile_App&RegistrationSubChannel=hOn"

    async def _login_url(self, login_url: str) -> str:
        headers = {"user-agent": const.USER_AGENT}
        url = URL(login_url, encoded=True)
        async with self._request.get(url, headers=headers) as response:
            text = await response.text()
            if context := re.findall('"fwuid":"(.*?)","loaded":(\\{.*?})', text):
                fw_uid, loaded_str = context[0]
                loaded = json.loads(loaded_str)
                result = login_url.replace("/".join(const.AUTH_API.split("/")[:-1]), "")
                return fw_uid, loaded, result
            await self._error_logger(response)

    async def _login(self, fw_uid, loaded, login_url):
        data = {
            "message": {
                "actions": [
                    {
                        "id": "79;a",
                        "descriptor": "apex://LightningLoginCustomController/ACTION$login",
                        "callingDescriptor": "markup://c:loginForm",
                        "params": {
                            "username": quote(self._email),
                            "password": quote(self._password),
                            "startUrl": parse.unquote(
                                login_url.split("startURL=")[-1]
                            ).split("%3D")[0],
                        },
                    }
                ]
            },
            "aura.context": {
                "mode": "PROD",
                "fwuid": fw_uid,
                "app": "siteforce:loginApp2",
                "loaded": loaded,
                "dn": [],
                "globals": {},
                "uad": False,
            },
            "aura.pageURI": login_url,
            "aura.token": None,
        }
        params = {"r": 3, "other.LightningLoginCustom.login": 1}
        async with self._request.post(
            const.AUTH_API + "/s/sfsites/aura",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="&".join(f"{k}={json.dumps(v)}" for k, v in data.items()),
            params=params,
        ) as response:
            if response.status == 200:
                try:
                    data = await response.json()
                    return data["events"][0]["attributes"]["values"]["url"]
                except json.JSONDecodeError:
                    pass
                except KeyError:
                    _LOGGER.error(
                        "Can't get login url - %s", pformat(await response.json())
                    )
            await self._error_logger(response)
            return ""

    def _parse_token_data(self, text):
        if access_token := re.findall("access_token=(.*?)&", text):
            self._access_token = access_token[0]
        if refresh_token := re.findall("refresh_token=(.*?)&", text):
            self._refresh_token = refresh_token[0]
        if id_token := re.findall("id_token=(.*?)&", text):
            self._id_token = id_token[0]

    async def _get_token(self, url):
        async with self._request.get(url) as response:
            if response.status != 200:
                await self._error_logger(response)
                return False
            url = re.findall("href\\s*=\\s*[\"'](.+?)[\"']", await response.text())
            if not url:
                await self._error_logger(response)
                return False
        if "ProgressiveLogin" in url[0]:
            async with self._request.get(url[0]) as response:
                if response.status != 200:
                    await self._error_logger(response)
                    return False
                url = re.findall("href\\s*=\\s*[\"'](.*?)[\"']", await response.text())
        url = "/".join(const.AUTH_API.split("/")[:-1]) + url[0]
        async with self._request.get(url) as response:
            if response.status != 200:
                await self._error_logger(response)
                return False
            self._parse_token_data(await response.text())
        return True

    async def _api_auth(self):
        post_headers = {"id-token": self._id_token}
        data = self._device.get()
        async with self._request.post(
            f"{const.API_URL}/auth/v1/login", headers=post_headers, json=data
        ) as response:
            try:
                json_data = await response.json()
            except json.JSONDecodeError:
                await self._error_logger(response)
                return False
            self._cognito_token = json_data["cognitoUser"]["Token"]
        return True

    async def authenticate(self):
        self.clear()
        try:
            if not (login_site := await self._load_login()):
                raise exceptions.HonAuthenticationError("Can't open login page")
            if not (url := await self._login(*login_site)):
                raise exceptions.HonAuthenticationError("Can't login")
            if not await self._get_token(url):
                raise exceptions.HonAuthenticationError("Can't get token")
            if not await self._api_auth():
                raise exceptions.HonAuthenticationError("Can't get api token")
        except exceptions.HonNoAuthenticationNeeded:
            return

    async def refresh(self):
        params = {
            "client_id": const.CLIENT_ID,
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
        }
        async with self._request.post(
            f"{const.AUTH_API}/services/oauth2/token", params=params
        ) as response:
            if response.status >= 400:
                await self._error_logger(response, fail=False)
                return False
            data = await response.json()
        self._expires = datetime.utcnow()
        self._id_token = data["id_token"]
        self._access_token = data["access_token"]
        return await self._api_auth()

    def clear(self):
        self._session.cookie_jar.clear_domain(const.AUTH_API.split("/")[-2])
        self._request.called_urls = []
        self._cognito_token = ""
        self._id_token = ""
        self._access_token = ""
        self._refresh_token = ""
