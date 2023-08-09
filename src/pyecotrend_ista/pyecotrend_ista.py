from __future__ import annotations

import functools
import json
import logging
import os
import ssl
import time
from asyncio import TimeoutError, sleep
from random import randint
from typing import Any

import aiohttp

from pyecotrend_ista.login_helper import LoginHelper

from .const import ACCOUNT_URL, CONSUMPTIONS_URL, LOGIN_HEADER, MAX_RETRIES, RETRY_DELAY, VERSION
from .exception_classes import Error, InternalServerError, LoginError, ServerError
from .helper_object_de import CustomRaw

_LOGGER = logging.getLogger(__name__)


class PyEcotrendIsta:
    def __init__(self, email: str, password: str, logger: logging.Logger = None, hass_dir: str | None = None) -> None:
        self._accessToken: str | None = None
        self._refreshToken: str | None = None
        self._accessTokenExpiresIn: int = 0
        self._header: dict[str, str] = {}
        self._supportCode: str | None = None
        self._uuid: str = ""

        self._email = email.strip()
        self._password = password

        self.start_timer: float = 0.0

        self._LOGGER = logger if logger else _LOGGER
        self._hass_dir = hass_dir

        self.loginhelper = LoginHelper(username=self._email, password=self._password)

    @staticmethod
    def refresh_now(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            if (
                self._accessTokenExpiresIn > 0
                and self._isConnected()
                and self._refreshToken
                and self._accessTokenExpiresIn <= (time.time() - self.start_timer).__round__(2)
            ):
                await self.__refresh()
            return await func(self, *args, **kwargs)

        return wrapper

    def _isConnected(self) -> bool:
        if self._accessToken:
            return True
        return False

    def _logoff(self) -> None:
        self._accessToken = None

    async def __login(self, debug: bool = False) -> str | None:
        if self._email == "demo@ista.de" and self._password == "Ausprobieren!" and self._hass_dir and not debug:
            self._LOGGER.debug("DEMO")
            with open(self._hass_dir + "/account_de_url.json", encoding="utf-8"):
                self._accessToken = "Demo"
            return self._accessToken
        self._accessToken, self._accessTokenExpiresIn, self._refreshToken = await self.loginhelper.getToken()
        return self._accessToken

    async def __refresh(self) -> None:
        if self._accessToken == "Demo":
            return
        self._LOGGER.debug("refresh Token")
        self._accessToken, self._accessTokenExpiresIn, self._refreshToken = await self.loginhelper.refreshToken(
            self._refreshToken
        )

        self._header["Authorization"] = f"Bearer {self._accessToken}"
        self.start_timer = time.time()

    async def __setAccount(self) -> None:
        if self._accessToken == "Demo" and self._hass_dir:
            with open(self._hass_dir + "/account_de_url.json", encoding="utf-8") as f:
                res = json.loads(f.read())
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
            return
        self._header = LOGIN_HEADER
        self._header["User-Agent"] = await self.getUA()
        self._header["Authorization"] = f"Bearer {self._accessToken}"
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(15), connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session, session.get(ACCOUNT_URL, headers=self._header) as response:
            res = await response.json()
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
        return VERSION

    async def login(self, forceLogin: bool = False, debug: bool = False) -> str | None:
        self.start_timer = time.time()
        if not self._isConnected() or forceLogin:
            self._logoff()
            retryCounter = 0
            while not self._isConnected() and (retryCounter < MAX_RETRIES + 2):
                retryCounter += 1
                try:
                    self._accessToken = await self.__login(debug)
                except LoginError as error:
                    # Login failed
                    self._accessToken = None
                    self._LOGGER.error(error)
                    raise LoginError from error
                except ServerError:
                    if retryCounter < MAX_RETRIES:
                        await sleep(RETRY_DELAY)
                    else:
                        raise ServerError()  # noqa: TRY200
                except InternalServerError as error:
                    raise Exception(error.msg)  # noqa: TRY200
                except Error as err:
                    raise Exception(err)  # noqa: TRY200
                if not self._accessToken:
                    await sleep(RETRY_DELAY)
                else:
                    await self.__setAccount()
        return self._accessToken

    @refresh_now
    async def consum_raw(self, select_year=None, select_month=None, filter_none=True) -> dict[str, Any]:
        c_raw: dict[str, Any] = await self.get_raw()

        if not isinstance(c_raw, dict) or (c_raw.get("consumptions", None) is None and c_raw.get("costs", None) is None):
            return c_raw

        if "consumptions" not in c_raw or not isinstance(c_raw.get("consumptions"), list):
            c_raw["consumptions"] = []

        consum_types = []
        all_dates = []
        indices_to_delete_consumption = []

        for i, consumption in enumerate(c_raw.get("consumptions", [])):
            if (
                not isinstance(consumption, dict)
                or "readings" not in consumption
                or consumption.get("readings", None) is None
                or not isinstance(consumption.get("readings"), list)
            ):
                consumption = {}
                continue

            for reading in consumption.get("readings", []):
                if reading["additionalValue"] is not None or reading["value"] is not None:
                    consum_types.append(reading["type"])

            consum_types = list({consum_type for consum_type in consum_types if i is not None})

            new_readings = []
            if "date" in consumption:
                all_dates.append(consumption["date"])
            if select_month is None and select_year is None:
                for reading in consumption.get("readings", []):
                    if filter_none and reading["type"] is not None:
                        new_readings.append(reading)
                    elif not filter_none:
                        new_readings.append(reading)
            elif (
                select_year is not None
                and select_month is not None
                and consumption["date"]["year"] in select_year
                and consumption["date"]["month"] in select_month
            ):
                for reading in consumption.get("readings", []):
                    if filter_none and reading["type"] is not None:
                        new_readings.append(reading)
                    elif not filter_none:
                        new_readings.append(reading)
            elif select_year is not None and consumption["date"]["year"] in select_year and select_month is None:
                for reading in consumption.get("readings", []):
                    if filter_none and reading["type"] is not None:
                        new_readings.append(reading)
                    elif not filter_none:
                        new_readings.append(reading)
            elif select_month is not None and consumption["date"]["month"] in select_month and select_year is None:
                for reading in consumption.get("readings", []):
                    if filter_none and reading["type"] is not None:
                        new_readings.append(reading)
                    elif not filter_none:
                        new_readings.append(reading)
            if new_readings:
                consumption["readings"] = new_readings
            else:
                indices_to_delete_consumption.append(i)

        for index in sorted(indices_to_delete_consumption, reverse=True):
            if index < len(c_raw["consumptions"]):
                del c_raw["consumptions"][index]

        _all_date = all_dates
        new_date = []
        sum_by_year = {}
        for date in _all_date:
            if select_year is None or date["year"] in select_year:
                new_date.append(date["year"])
        new_date = list(dict.fromkeys(new_date))

        cost_consum_types = consum_types

        sum_by_year = {typ: {year: 0.0 for year in new_date} for typ in cost_consum_types}

        for item in c_raw.get("consumptions", []):
            if "readings" not in item or not item["readings"]:
                continue
            for reading in item.get("readings", []):
                if reading.get("type", None) is None:
                    continue
                for typ in cost_consum_types:
                    for year in new_date:
                        if reading["type"] == typ and item["date"]["year"] == year:
                            if reading["value"]:
                                sum_by_year[typ][year] += round(
                                    float(reading["value"].replace(",", ".")),
                                    1,
                                )
                            else:
                                sum_by_year[typ][year] += round(
                                    (
                                        float(reading["additionalValue"].replace(",", "."))
                                        if reading["additionalValue"] is not None
                                        else 0.0
                                    ),
                                    1,
                                )

                            if reading["type"] == "warmwater":
                                sum_by_year["ww"] = reading["unit"]
                            elif reading["type"] == "water":
                                sum_by_year["w"] = reading["unit"]
                            elif reading["type"] == "heating" and reading["unit"]:
                                sum_by_year["h"] = reading["unit"]
                            elif reading["type"] == "heating":
                                sum_by_year["h"] = reading["additionalUnit"]

        indices_to_delete_costs = []

        if "costs" not in c_raw or not isinstance(c_raw.get("costs"), list):
            c_raw["costs"] = []

        for i, costs in enumerate(c_raw.get("costs", [])):
            new_readings = []
            if "costsByEnergyType" in costs:
                if select_month is None and select_year is None:
                    for reading in costs.get("costsByEnergyType", []):
                        if filter_none and reading["type"] is not None:
                            new_readings.append(reading)
                        elif not filter_none:
                            new_readings.append(reading)
                elif (
                    select_year is not None
                    and select_month is not None
                    and costs["date"]["year"] in select_year
                    and costs["date"]["month"] in select_month
                ):
                    for reading in costs.get("costsByEnergyType", []):
                        if filter_none and reading["type"] is not None:
                            new_readings.append(reading)
                        elif not filter_none:
                            new_readings.append(reading)
                elif select_year is not None and costs["date"]["year"] in select_year and select_month is None:
                    for reading in costs.get("costsByEnergyType", []):
                        if filter_none and reading["type"] is not None:
                            new_readings.append(reading)
                        elif not filter_none:
                            new_readings.append(reading)
                elif select_month is not None and costs["date"]["month"] in select_month and select_year is None:
                    for reading in costs.get("costsByEnergyType", []):
                        if filter_none and reading["type"] is not None:
                            new_readings.append(reading)
                        elif not filter_none:
                            new_readings.append(reading)
            if new_readings:
                costs["costsByEnergyType"] = new_readings
            else:
                indices_to_delete_costs.append(i)
        for index in sorted(indices_to_delete_costs, reverse=True):
            if "costs" in c_raw and index < len(c_raw["costs"]):
                del c_raw["costs"][index]

        for key in [
            "consumptionsBillingPeriods",
            "costsBillingPeriods",
            "resident",
            "co2Emissions",
            "co2EmissionsBillingPeriods",
        ]:
            if key in c_raw:
                del c_raw[key]

        consumptions: list = c_raw.get("consumptions", [])
        costs: list = c_raw.get("costs", [])

        combined_data = []
        for cost_entry in costs:
            for consumption_entry in consumptions:
                # Überprüfen, ob die Daten das gleiche Datum haben
                if cost_entry["date"] == consumption_entry["date"]:
                    # Wenn ja, kombiniere die Kosten- und Verbrauchsdaten in einem Eintrag
                    combined_entry = {
                        "date": cost_entry["date"],
                        "consumptions": consumption_entry["readings"],
                        "costs": cost_entry["costsByEnergyType"],
                    }

                    combined_data.append(combined_entry)

        total_additional_values = {}
        total_additional_custom_values = {}
        for consumption_unit in consumptions:
            if "readings" not in consumption_unit or not consumption_unit["readings"]:
                continue
            for reading in consumption_unit.get("readings", []):
                if reading["type"] is None or (reading["value"] is None and reading["additionalValue"] is None):
                    continue

                if reading["type"] not in total_additional_custom_values:
                    total_additional_custom_values[reading["type"]] = 0.0
                if reading["additionalValue"]:
                    total_additional_custom_values[reading["type"]] += round(
                        float(reading["additionalValue"].replace(",", ".")), 1
                    )
                else:
                    total_additional_custom_values[reading["type"]] += round(
                        (float(reading["value"].replace(",", ".")) if reading["value"] is not None else 0.0), 1
                    )

                if reading["type"] == "warmwater":
                    total_additional_custom_values["ww"] = reading["additionalUnit"]
                elif reading["type"] == "water":
                    total_additional_custom_values["w"] = reading["additionalUnit"]
                elif reading["type"] == "heating" and reading["additionalUnit"]:
                    total_additional_custom_values["h"] = reading["additionalUnit"]
                elif reading["type"] == "heating":
                    total_additional_custom_values["h"] = reading["unit"]

                if reading["type"] not in total_additional_values:
                    total_additional_values[reading["type"]] = 0.0
                if reading["value"]:
                    total_additional_values[reading["type"]] += round(float(reading["value"].replace(",", ".")), 1)
                else:
                    total_additional_values[reading["type"]] += round(
                        (
                            float(reading["additionalValue"].replace(",", "."))
                            if reading["additionalValue"] is not None
                            else 0.0
                        ),
                        1,
                    )

                if reading["type"] == "warmwater":
                    total_additional_values["ww"] = reading["unit"]
                elif reading["type"] == "water":
                    total_additional_values["w"] = reading["unit"]
                elif reading["type"] == "heating" and reading["unit"]:
                    total_additional_values["h"] = reading["unit"]
                elif reading["type"] == "heating":
                    total_additional_values["h"] = reading["additionalUnit"]

        last_value = None
        last_custom_value = None
        last_year_compared_consumption = None

        if consumptions:
            last_value = {}
            last_custom_value = {}
            last_year_compared_consumption = {}

            if len(consumptions) > 0 and "readings" in consumptions[0] and consumptions[0]["readings"]:
                for reading in consumptions[0]["readings"]:
                    if reading["type"] is None or (reading["value"] is None and reading["additionalValue"] is None):
                        continue

                    if reading["comparedConsumption"]:
                        last_year_compared_consumption[reading["type"]] = reading["comparedConsumption"]
                        last_year_compared_consumption[reading["type"]]["comparedValue"] = float(
                            last_year_compared_consumption[reading["type"]]["comparedValue"].replace(",", ".")
                        )

                        if reading["value"]:
                            last_year_compared_consumption[reading["type"]]["nowYearValue"] = float(
                                reading["value"].replace(",", ".")
                            )
                        elif reading["additionalValue"]:
                            last_year_compared_consumption[reading["type"]]["nowYearValue"] = float(
                                reading["additionalValue"].replace(",", ".")
                            )
                        if "period" in last_year_compared_consumption[reading["type"]]:
                            del last_year_compared_consumption[reading["type"]]["period"]

                    if reading["type"] not in last_custom_value:
                        last_custom_value[reading["type"]] = 0.0
                    if reading["additionalValue"]:
                        last_custom_value[reading["type"]] += float(reading["additionalValue"].replace(",", "."))
                    else:
                        last_custom_value[reading["type"]] += (
                            float(reading["value"].replace(",", ".")) if reading["value"] is not None else 0.0
                        )

                    if reading["type"] == "warmwater":
                        last_custom_value["ww"] = reading["additionalUnit"]
                    elif reading["type"] == "water":
                        last_custom_value["w"] = reading["additionalUnit"]
                    elif reading["type"] == "heating" and reading["additionalUnit"]:
                        last_custom_value["h"] = reading["additionalUnit"]
                    elif reading["type"] == "heating":
                        last_custom_value["h"] = reading["unit"]

                    if reading["type"] not in last_value:
                        last_value[reading["type"]] = 0.0
                    if reading["value"]:  # reading["type"] in ("warmwater", "water", "heating") and
                        last_value[reading["type"]] += float(reading["value"].replace(",", "."))
                    else:
                        last_value[reading["type"]] += (
                            float(reading["additionalValue"].replace(",", "."))
                            if reading["additionalValue"] is not None
                            else 0.0
                        )
                    if reading["type"] == "warmwater":
                        last_value["ww"] = reading["unit"]
                    elif reading["type"] == "water":
                        last_value["w"] = reading["unit"]
                    elif reading["type"] == "heating" and reading["unit"] == "kWh":
                        last_value["h"] = reading["unit"]
                    elif reading["type"] == "heating":
                        last_value["h"] = reading["additionalUnit"]

            last_custom_value["month"] = consumptions[0]["date"]["month"]
            last_custom_value["year"] = consumptions[0]["date"]["year"]

            last_value["month"] = consumptions[0]["date"]["month"]
            last_value["year"] = consumptions[0]["date"]["year"]

        last_costs = None
        if costs:
            if last_costs is None:
                last_costs = {}
            for costsByEnergyType in costs[0]["costsByEnergyType"]:
                if (
                    costsByEnergyType is None
                    or "type" not in costsByEnergyType
                    or costsByEnergyType["type"] is None
                    or "comparedCost" not in costsByEnergyType
                    or costsByEnergyType["comparedCost"] is None
                    or "smiley" not in costsByEnergyType["comparedCost"]
                    or costsByEnergyType["comparedCost"]["smiley"] is None
                    or "comparedPercentage" not in costsByEnergyType["comparedCost"]
                    or costsByEnergyType["comparedCost"]["comparedPercentage"] is None
                ):
                    continue

                if costsByEnergyType["type"] not in last_costs:
                    last_costs[costsByEnergyType["type"]] = 0.0
                last_costs[costsByEnergyType["type"]] += costsByEnergyType["value"]
                last_costs["unit"] = costsByEnergyType["unit"]
                if costsByEnergyType["type"] == "warmwater":
                    if costsByEnergyType["comparedCost"]["smiley"] == ["MAD", "EQUAL"]:
                        last_costs["ww"] = costsByEnergyType["comparedCost"]["comparedPercentage"]
                    elif costsByEnergyType["comparedCost"]["smiley"] in ["HAPPY"]:
                        last_costs["ww"] = costsByEnergyType["comparedCost"]["comparedPercentage"] * -1
                elif costsByEnergyType["type"] == "water":
                    if costsByEnergyType["comparedCost"]["smiley"] == ["MAD", "EQUAL"]:
                        last_costs["w"] = costsByEnergyType["comparedCost"]["comparedPercentage"]
                    elif costsByEnergyType["comparedCost"]["smiley"] in ["HAPPY"]:
                        last_costs["w"] = costsByEnergyType["comparedCost"]["comparedPercentage"] * -1
                elif costsByEnergyType["type"] == "heating":
                    if costsByEnergyType["comparedCost"]["smiley"] in ["MAD", "EQUAL"]:
                        last_costs["h"] = costsByEnergyType["comparedCost"]["comparedPercentage"]
                    elif costsByEnergyType["comparedCost"]["smiley"] in ["HAPPY"]:
                        last_costs["h"] = costsByEnergyType["comparedCost"]["comparedPercentage"] * -1
            last_costs["month"] = costs[0]["date"]["month"]
            last_costs["year"] = costs[0]["date"]["year"]

        return CustomRaw.from_dict(
            {
                "consum_types": consum_types,
                "combined_data": None,  # combined_data,
                "total_additional_values": total_additional_values,
                "total_additional_custom_values": total_additional_custom_values,
                "last_value": last_value,
                "last_custom_value": last_custom_value,
                "last_costs": last_costs,
                "all_dates": None,  # all_dates,
                "sum_by_year": sum_by_year,
                "last_year_compared_consumption": last_year_compared_consumption,
            }
        ).to_dict()

    async def get_raw(self) -> dict[str, Any]:
        raw: dict[str, Any] = {}

        if self._accessToken == "Demo":
            if self._hass_dir:
                with open(self._hass_dir + "/demo_de_url.json", encoding="utf-8") as f:
                    return json.loads(f.read())
            else:
                with open(os.getcwd() + "\\src\\pyecotrend_ista\\demo_de_url.json", encoding="utf-8") as f:
                    return json.loads(f.read())
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(15), connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session, session.get(CONSUMPTIONS_URL + self._uuid, headers=self._header) as response:
            retryCounter = 0
            while not raw and (retryCounter < MAX_RETRIES + 2):
                retryCounter += 1
                try:
                    raw = await response.json()
                    if "key" in raw:
                        raise Exception("Login fail, check your input!", raw["key"])
                except TimeoutError as error:
                    self._LOGGER.debug("TimeoutError", error)
                except aiohttp.ContentTypeError as err:
                    self._LOGGER.debug("ContentTypeError", err)
        return raw

    def getSupportCode(self) -> str | None:
        """Returns the support code associated with the instance."""
        return self._supportCode

    async def getUA(self) -> str:
        """Fetches a random User-Agent string from a public source."""
        url = "https://raw.githubusercontent.com/Ludy87/pyecotrend-ista/main/src/pyecotrend_ista/ua.json"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67"
                " Safari/537.36"
            )
        }
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(15), connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session, session.get(url, headers=headers) as response:
            try:
                data = await response.json(content_type=None)
                i = randint(0, len(data) - 1)
                _data = data[i]["useragent"]
            except Exception as err:
                self._LOGGER.info(f"Default User agent activ!\n{err}")
                _data = headers.get("User-Agent")
        return _data
