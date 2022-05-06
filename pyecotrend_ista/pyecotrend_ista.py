from __future__ import annotations

from asyncio import sleep, TimeoutError
from datetime import datetime
from random import randint
from typing import Any, Dict, List

import aiohttp
import json
import logging

from .const import LOGIN_HEADER, LOGIN_URL, VERSION

_LOGGER = logging.getLogger(__name__)


class PyEcotrendIsta:
    def __init__(self, email: str, password: str) -> None:
        self._accessToken = None
        self._header = None
        self._supportCode = None
        self._uuid = None

        self._version = VERSION

        self.maxRetries = 3
        self.retryDelay = 2

        self._email = email
        self._password = password

        self._consum: List[Dict[str, Any]] = []

    def _isConnected(self) -> bool:
        return self._accessToken

    def _logoff(self) -> None:
        self._accessToken = None

    async def __login(self) -> str:
        payload = {
            "email": self._email,
            "password": self._password,
            "fromMobileApp": "true",
        }
        LOGIN_HEADER["User-Agent"] = await self.getUA()
        async with aiohttp.ClientSession() as session:
            async with session.post(LOGIN_URL, headers=LOGIN_HEADER, data=json.dumps(payload)) as response:
                try:
                    if response.status != 200:
                        raise Exception("Login fail, check your input!", await response.json())
                    else:
                        json_str_resp = await response.json()
                        self._accessToken = json_str_resp["accessToken"]
                except Exception as err:
                    _LOGGER.debug(err)
                    raise Exception(err)
                finally:
                    await session.close()
        return self._accessToken

    async def __setAccount(self) -> None:
        self._header = LOGIN_HEADER
        self._header.pop("Accept-Encoding")
        self._header.pop("Content-Type")
        self._header["User-Agent"] = await self.getUA()
        self._header["Authorization"] = "Bearer {}".format(self._accessToken)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.prod.eed.ista.com/account", headers=self._header) as response:
                res = await response.json()
                await session.close()
                self._a_ads = res["ads"]
                self._a_authcode = res["authcode"]
                self._a_betaPhase = res["betaPhase"]
                self._a_consumptionUnitUuids = res["consumptionUnitUuids"]
                self._a_country = res["country"]
                self._a_email = res["email"]
                self._a_emailConfirmed = res["emailConfirmed"]
                self._a_enabled = res["enabled"]
                self._a_fcmToken = res["fcmToken"]
                self._a_firstName = res["firstName"]
                self._a_isDemo = res["isDemo"]
                self._a_keycloakId = res["keycloakId"]
                self._a_lastName = res["lastName"]
                self._a_locale = res["locale"]
                self._a_marketing = res["marketing"]
                self._a_mobileLoginStatus = res["mobileLoginStatus"]
                self._a_notificationMethod = res["notificationMethod"]
                self._a_notificationMethodEmailConfirmed = res["notificationMethodEmailConfirmed"]
                self._a_password = res["password"]
                self._a_privacy = res["privacy"]
                self._a_residentAndConsumptionUuidsMap = res["residentAndConsumptionUuidsMap"]
                self._a_residentTimeRangeUuids = res["residentTimeRangeUuids"]
                self._supportCode = res["supportCode"]
                self._a_tos = res["tos"]
                self._a_tosUpdated = res["tosUpdated"]
                self._a_transitionMobileNumber = res["transitionMobileNumber"]
                self._a_unconfirmedPhoneNumber = res["unconfirmedPhoneNumber"]
                self._a_userGroup = res["userGroup"]
                self._uuid = res["activeConsumptionUnit"]

    def getVersion(self) -> str:
        return self._version

    async def login(self, forceLogin=False) -> str:
        if not self._isConnected() or forceLogin:
            try:
                self._logoff()
                retryCounter = 0
                while not self._isConnected() and (retryCounter < self.maxRetries + 2):
                    retryCounter += 1
                    try:
                        self._accessToken = await self.__login()
                    except Exception as err:
                        raise Exception(err)
                    if not self._accessToken:
                        await sleep(self.retryDelay)
                    else:
                        await self.__setAccount()
            except Exception as err:
                # Login failed
                self._accessToken = None
                _LOGGER.error(err)
        return self._accessToken

    async def consum_raw(self) -> List[Dict[str, Any]]:
        c_raw: List[Dict[str, Any]] = []
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.prod.eed.ista.com/consumptions?consumptionUnitUuid={}".format(self._uuid),
                headers=self._header,
            ) as response:
                retryCounter = 0
                while not c_raw and (retryCounter < self.maxRetries + 2):
                    retryCounter += 1
                    try:
                        c_raw = await response.json()
                        if "key" in c_raw:
                            raise Exception(c_raw["key"])
                    except TimeoutError as error:
                        _LOGGER.debug(error)
                await session.close()
        return c_raw

    def getSupportCode(self) -> str:
        return self._supportCode

    async def consum_small(self):
        consum_raw: list = []
        retryCounter = 0
        while not consum_raw and ("consumptions" not in consum_raw) and (retryCounter < self.maxRetries + 2):
            retryCounter += 1
            await self.login()
            consum_raw: dict = await self.consum_raw()
            if "consumptions" not in consum_raw:
                await sleep(self.retryDelay)
        if "consumptions" not in consum_raw:
            raise Exception("Login fail!")
        consumptions: dict = consum_raw.get("consumptions")
        for consum in consumptions:
            for reading in consum.get("readings"):
                if "type" in reading:
                    if reading.get("type"):
                        self._consum.append(
                            {
                                "entity_id": "{}_{}_{}_{}".format(
                                    # sensor.yyyy_m_warmwasser_xxxxxxxxx
                                    consum["date"]["year"],
                                    consum["date"]["month"],
                                    reading["type"],
                                    self._supportCode,
                                ),
                                "year": consum["date"]["year"],
                                "month": consum["date"]["month"],
                                "type": reading["type"],
                                "value": reading["value"],
                                "valuekwh": reading["additionalValue"],
                                "unit": reading["unit"],
                                "unitkwh": reading["additionalUnit"],
                                "supportCode": self._supportCode,
                                "date": consum["date"],
                            }
                        )
            # consum_now.append(self._consum)
        return self._consum

    async def getConsumsNow(self) -> Dict[str, Any]:
        datetimenow = datetime.now()
        _consums: List[Dict[str, Any]] = []
        if self._consum:
            consums: List[Dict[str, Any]] = self._consum
        else:
            consums: List[Dict[str, Any]] = await self.consum_small()
        for consum in consums:
            if datetimenow.year == consum["year"] and datetimenow.month == (consum["month"] + 1):
                _consums.append(consum)
        return _consums

    async def getConsumNowByType(self, _type: str | None) -> Dict[str, Any]:
        if self._consum:
            consums: List[Dict[str, Any]] = self._consum
        else:
            consums: List[Dict[str, Any]] = await self.consum_small()
        for consum in consums:
            if _type == consum["type"]:
                return consum

    async def getConsumById(self, entity_id: str | None) -> Dict[str, Any]:
        if self._consum:
            consums: List[Dict[str, Any]] = self._consum
        else:
            consums: List[Dict[str, Any]] = await self.consum_small()
        for consum in consums:
            if entity_id == consum["entity_id"]:
                return consum

    async def getConsumsByType(self, _type: str | None) -> Dict[str, Any]:
        __type: List[Dict, Any] = []
        if self._consum:
            consums: List[Dict[str, Any]] = self._consum
        else:
            consums: List[Dict[str, Any]] = await self.consum_small()
        for consum in consums:
            if _type == consum["type"]:
                __type.append(consum)
        return __type

    async def getConsumsByYear(self, year: int | None) -> Dict[str, Any]:
        __type: List[Dict, Any] = []
        if self._consum:
            consums: List[Dict[str, Any]] = self._consum
        else:
            consums: List[Dict[str, Any]] = await self.consum_small()
        for consum in consums:
            if year == consum["year"]:
                __type.append(consum)
        return __type

    async def getConsumsByMonth(self, month: int | None) -> Dict[str, Any]:
        __type: List[Dict, Any] = []
        if self._consum:
            consums: List[Dict[str, Any]] = self._consum
        else:
            consums: List[Dict[str, Any]] = await self.consum_small()
        for consum in consums:
            if month == consum["month"]:
                __type.append(consum)
        return __type

    async def getConsumsByMonthYear(self, month: int | None, year: int | None) -> Dict[str, Any]:
        __type: List[Dict, Any] = []
        if self._consum:
            consums: List[Dict[str, Any]] = self._consum
        else:
            consums: List[Dict[str, Any]] = await self.consum_small()
        for consum in consums:
            if month == consum["month"] and year == consum["year"]:
                __type.append(consum)
        return __type

    async def getUA(self) -> str:
        url = "https://raw.githubusercontent.com/Ludy87/pyecotrend-ista/main/pyecotrend_ista/ua.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json(content_type=None)
                i = randint(0, len(data) - 1)
                return data[i]["useragent"]
