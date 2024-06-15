"""Unofficial python library for the ista EcoTrend API."""

from __future__ import annotations

import logging
import time
import warnings
from typing import Any

import requests

from .const import (
    ACCOUNT_URL,
    CONSUMPTION_UNIT_DETAILS_URL,
    CONSUMPTIONS_URL,
    DEMO_USER_TOKEN,
    MAX_RETRIES,
    RETRY_DELAY,
    VERSION,
)
from .exception_classes import Error, InternalServerError, LoginError, ServerError
from .helper_object_de import CustomRaw
from .login_helper import LoginHelper


class PyEcotrendIsta:
    """A Python client for interacting with the ista EcoTrend API.

    This class provides methods to authenticate and interact with the ista EcoTrend API.
    """

    def __init__(
        self,
        email: str,
        password: str,
        logger: logging.Logger | None = None,
        hass_dir: str | None = None,
        totp: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize the PyEcotrendIsta client.

        Parameters
        ----------
        email : str
            The email address used to log in to the ista EcoTrend API.
        password : str
            The password used to log in to the ista EcoTrend API.
        logger : logging.Logger, optional
            An optional logger instance for logging messages. Default is None.
        hass_dir : str, optional
            [DEPRECATED] An optional directory for Home Assistant configuration. Default is None.
        totp : str, optional
            An optional TOTP (Time-based One-Time Password) for two-factor authentication. Default is None.
        session : requests.Session, optional
            An optional requests session for making HTTP requests. Default is None.

        """

        if hass_dir:
            warnings.warn(
                "The 'hass_dir' parameter is deprecated and will be removed in a future release.", DeprecationWarning
            )

        self._accessToken: str | None = None
        self._refreshToken: str | None = None
        self._accessTokenExpiresIn: int = 0
        self._header: dict[str, str] = {}
        self._supportCode: str | None = None
        self._uuid: str = ""

        self._email = email.strip()
        self._password = password

        self.start_timer: float = 0.0

        self._LOGGER = logger if logger else logging.getLogger(__name__)
        self._hass_dir = hass_dir

        self.loginhelper = LoginHelper(
            username=self._email, password=self._password, totp=totp, session=session, logger=self._LOGGER
        )

        self.session = self.loginhelper.session

    @property
    def accessToken(self):
        """Retrieve the access token, refreshing it if necessary.

        This property checks if the access token is still valid. If the token has expired and the client is connected,
        it refreshes the token. The token is considered expired if the current time minus the start time exceeds the
        token's expiration period.

        Returns
        -------
        str
            The current access token.

        Notes
        -----
        This method will automatically refresh the access token if it has expired.

        """
        if (
            self._accessTokenExpiresIn > 0
            and self._isConnected()
            and self._refreshToken
            and self._accessTokenExpiresIn <= (time.time() - self.start_timer).__round__(2)
        ):
            self.__refresh()
        return self._accessToken

    def _isConnected(self) -> bool:
        """Check if the client is connected by verifying the presence of an access token.

        Returns
        -------
        bool
            True if the client has a valid access token, False otherwise.

        """
        if self._accessToken:
            return True
        return False

    def _logoff(self) -> None:
        """Log off the client by invalidating the current access token.

        This method sets the access token to None, effectively logging off the client.
        """
        self._accessToken = None

    def __login(self, debug: bool = False) -> str | None:
        """Perform the login process to obtain an access token.

        If the email is a demo account, it logs in using a demo user login function.
        For other accounts, it retrieves a token using a login helper.

        Parameters
        ----------
        debug : bool, optional
            [DEPRECATED] Whether to enable debug logging. Default is False.

        Returns
        -------
        str or None
            The access token if login is successful, None otherwise.

        """
        if self._email == "demo@ista.de":
            self._LOGGER.debug("DEMO")
            token = self.demo_user_login()
            self._accessToken = token["accessToken"]
            self._accessTokenExpiresIn = token["accessTokenExpiresIn"]
            self._refreshToken = token["refreshToken"]
            return self.accessToken
        self._accessToken, self._accessTokenExpiresIn, self._refreshToken = self.loginhelper.getToken()
        return self.accessToken

    def __refresh(self) -> None:
        """Refresh the access token using the refresh token.

        This method retrieves a new access token, updates internal variables,
        and resets the token expiration timer.

        Notes
        -----
        This method assumes `self._refreshToken` is already set.

        """
        self._accessToken, self._accessTokenExpiresIn, self._refreshToken = self.loginhelper.refreshToken(self._refreshToken)
        new_token = self._accessToken

        self._header["Authorization"] = f"Bearer {new_token}"
        self.start_timer = time.time()
        self._LOGGER.debug("refresh Token %s", self.start_timer)

    def __setAccountValues(self, res_json: dict[str, Any]) -> None:
        """Set account values based on the provided JSON response.

        Parameters
        ----------
        res_json : dict
            JSON response containing account information.

        Notes
        -----
        Sets instance variables for various account details based on keys in `res_json`.

        """
        self._a_ads = res_json["ads"]
        self._a_authcode = res_json["authcode"]
        self._a_betaPhase = res_json["betaPhase"]
        self._a_consumptionUnitUuids = res_json["consumptionUnitUuids"]
        self._a_country = res_json["country"]
        self._a_email = res_json["email"]
        self._a_emailConfirmed = res_json["emailConfirmed"]
        self._a_enabled = res_json["enabled"]
        self._a_fcmToken = res_json["fcmToken"]
        self._a_firstName = res_json["firstName"]
        self._a_isDemo = res_json["isDemo"]
        self._a_keycloakId = res_json["keycloakId"]
        self._a_lastName = res_json["lastName"]
        self._a_locale = res_json["locale"]
        self._a_marketing = res_json["marketing"]
        self._a_mobileLoginStatus = res_json["mobileLoginStatus"]
        self._a_notificationMethod = res_json["notificationMethod"]
        self._a_notificationMethodEmailConfirmed = res_json["notificationMethodEmailConfirmed"]
        self._a_password = res_json["password"]
        self._a_privacy = res_json["privacy"]
        self._residentAndConsumptionUuidsMap: dict[str, str] = res_json["residentAndConsumptionUuidsMap"]  # multi
        self._a_residentTimeRangeUuids = res_json["residentTimeRangeUuids"]
        self._supportCode = res_json["supportCode"]
        self._a_tos = res_json["tos"]
        self._a_tosUpdated = res_json["tosUpdated"]
        self._a_transitionMobileNumber = res_json["transitionMobileNumber"]
        self._a_unconfirmedPhoneNumber = res_json["unconfirmedPhoneNumber"]
        self._a_userGroup = res_json["userGroup"]
        self._uuid = res_json["activeConsumptionUnit"]  # single

    def __setAccount(self) -> None:
        """Fetch and set account information from the API.

        This method performs an API request to retrieve account information
        and sets instance variables accordingly using __setAccountValues.
        """
        self._header = {"Content-Type": "application/json"}
        self._header["User-Agent"] = self.getUA()
        self._header["Authorization"] = f"Bearer {self.accessToken}"
        response = self.session.get(ACCOUNT_URL, headers=self._header)
        res = response.json()
        self.__setAccountValues(res)

    def getVersion(self) -> str:
        """Get the version of the PyEcotrendIsta client.

        Returns
        -------
        str
            The version number of the PyEcotrendIsta client.

        """
        return VERSION

    def login(self, forceLogin: bool = False, debug: bool = False) -> str | None:
        """Perform the login process if not already connected or forced.

        Parameters
        ----------
        forceLogin : bool, optional
            If True, forces a fresh login attempt even if already connected. Default is False.
        debug : bool, optional
            [DEPRECATED] Flag indicating whether to enable debug logging. Default is False.

        Returns
        -------
        str or None
            The access token if login is successful, None otherwise.

        Raises
        ------
        LoginError
            If the login process fails due to an error.
        ServerError
            If a server error occurs during login attempts.
        InternalServerError
            If an internal server error occurs during login attempts.
        Exception
            For any other unexpected errors during the login process.

        """
        if debug:
            warnings.warn("The 'debug' parameter is deprecated and will be removed in a future release.", DeprecationWarning)

        self.start_timer = time.time()
        if not self._isConnected() or forceLogin:
            self._logoff()
            retryCounter = 0
            while not self._isConnected() and (retryCounter < MAX_RETRIES + 2):
                retryCounter += 1
                try:
                    self._accessToken = self.__login(debug)
                except LoginError as error:
                    # Login failed
                    self._accessToken = None
                    self._LOGGER.error(error)
                    raise LoginError(error.res) from error
                except ServerError:
                    if retryCounter < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
                    else:
                        raise ServerError()  # noqa: TRY200
                except InternalServerError as error:
                    raise Exception(error.msg)  # noqa: TRY200
                except requests.ReadTimeout:
                    time.sleep(RETRY_DELAY)
                except Error as err:
                    raise Exception(err)  # noqa: TRY200
                if not self.accessToken:
                    time.sleep(RETRY_DELAY)
                else:
                    self.__setAccount()
        return self.accessToken

    def userinfo(self, token):
        """Retrieve user information using the provided access token.

        Parameters
        ----------
        token : str
            The access token used for authentication.

        Returns
        -------
        Any
            JSON response containing user information.

        Notes
        -----
        This method constructs an authorization header using the provided access token
        and sends a GET request to the userinfo endpoint of the provider API.
        It expects a JSON response with user information.

        Raises
        ------
        requests.exceptions.RequestException
            If an error occurs while making the HTTP request.

        Example
        -------
        >>> client = PyEcotrendIsta(email='user@example.com', password='password')
        >>> token = client.login()
        >>> user_info = client.userinfo(token)

        """
        return self.loginhelper.userinfo(token=token)

    def logout(self) -> None:
        """Perform logout operation by invalidating the current session.

        This method invokes the logout functionality in the loginhelper module,
        passing the current refresh token for session invalidation.

        Notes
        -----
        This method assumes `self._refreshToken` is already set.

        Raises
        ------
        KeycloakPostError
            If an error occurs during the logout process. This error is raised based on the response from the logout request.

        Example:
        -------
        >>> client = PyEcotrendIsta(email='user@example.com', password='password')
        >>> client.login()
        >>> client.logout()

        """
        self.loginhelper.logout(self._refreshToken)

    def getUUIDs(self) -> list[str]:
        """Retrieve UUIDs of consumption units registered in the account.

        Returns
        -------
        list[str]
            A list containing UUIDs of consumption units. Each UUID represents a consumption unit,
            which could be a flat or a house for which consumption readings are provided.

        Notes
        -----
        A consumption unit represents a residence or building where consumption readings are recorded.
        The UUIDs are extracted from the `_residentAndConsumptionUuidsMap` attribute.

        Example:
        -------
        >>> client = PyEcotrendIsta(email='user@example.com', password='password')
        >>> client.login()
        >>> uuids = client.getUUIDs()
        >>> print(uuids)
        ['uuid1', 'uuid2', 'uuid3']

        """
        uuids = []
        for _, value in self._residentAndConsumptionUuidsMap.items():
            uuids.append(value)
        return uuids

    # @refresh_now
    def consum_raw(  # noqa: C901
        self,
        select_year: list[int] | None = None,
        select_month: list[int] | None = None,
        filter_none: bool = True,
        obj_uuid: str | None = None,
    ) -> dict[str, Any]:  # noqa: C901
        """Process consumption and cost data for a given consumption unit.

        Parameters
        ----------
        select_year : list[int] | None, optional
            List of years to filter data by year, default is None.
        select_month : list[int] | None, optional
            List of months to filter data by month, default is None.
        filter_none : bool, optional
            Whether to filter out None values in readings, default is True.
        obj_uuid : str | None, optional
            UUID of the consumption unit to fetch data for, default is None.

        Returns
        -------
        dict[str, Any]
            Processed data including consumption types, total additional values, last values,
            last costs, sum by year, and last year compared consumption.

        Notes
        -----
        This method processes raw consumption and cost data obtained from the `_get_raw` method.
        It filters and aggregates data based on the parameters provided.

        Raises
        ------
        Exception
            If there is an unexpected error during data processing.

        """
        # Fetch raw consumption data for the specified UUID
        c_raw: dict[str, Any] = self.get_raw(obj_uuid)

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
                        (float(reading["value"].replace(",", ".")) if reading["value"] is not None else 0.0),
                        1,
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
                    elif reading["type"] == "heating" and reading["additionalUnit"]:
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

    def get_raw(self, obj_uuid: str | None = None) -> dict[str, Any]:
        """Fetch raw consumption data from the API for a specific consumption unit.

        Parameters
        ----------
        obj_uuid : str, optional
            The UUID of the consumption unit. If not provided,
            defaults to the UUID associated with the instance (`self._uuid`).

        Returns
        -------
        dict
            A dictionary containing the raw consumption data fetched from the API.

        Raises
        ------
        LoginError
            If the API responds with an error indicating login failure or invalid input.

        """
        raw: dict[str, Any] = {}

        if obj_uuid is None:
            obj_uuid = self._uuid
        response = self.session.get(CONSUMPTIONS_URL + obj_uuid, headers=self._header)
        retryCounter = 0
        while not raw and (retryCounter < MAX_RETRIES + 2):
            retryCounter += 1
            try:
                raw = response.json()
                if "key" in raw:
                    raise LoginError("Login fail, check your input! %s", raw["key"])
            except requests.Timeout as error:
                self._LOGGER.debug("TimeoutError: %s", error)
            except requests.JSONDecodeError as err:
                self._LOGGER.debug("JSONDecodeError: %s", err)
        return raw

    def get_consumption_unit_details(self) -> dict[str, Any]:
        """Retrieve details of the consumption unit from the API.

        Returns
        -------
        dict
            A dictionary containing the details of the consumption unit.

        Raises
        ------
        ServerError
            If there is an issue with decoding the JSON response or if any request-related
            exceptions occur (e.g., network issues, timeouts).

        """
        try:
            with self.session.get(CONSUMPTION_UNIT_DETAILS_URL, headers=self._header) as r:
                r.raise_for_status()
                try:
                    return r.json()
                except requests.JSONDecodeError as e:
                    self._LOGGER.debug("JSONDecodeError: %s", e)
                    raise ServerError from e
        except (requests.RequestException, requests.Timeout) as e:
            self._LOGGER.debug("RequestException: %s", e)
            raise ServerError from e

    def getSupportCode(self) -> str | None:
        """Return the support code associated with the instance.

        Returns
        -------
        str or None
            The support code associated with the instance, or None if not set.

        """
        return self._supportCode

    def getUA(self) -> str:
        """Return the User-Agent string used for HTTP requests.

        Returns
        -------
        str
            The User-Agent string.

        Notes
        -----
        This method provides a static User-Agent string commonly used for web browsers.

        """
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67"
            " Safari/537.36"
        )

    def demo_user_login(self) -> dict[str, Any]:
        """Retrieve authentication tokens for the demo user.

        Returns
        -------
        dict[str, Any]
            A dictionary containing authentication tokens including 'accessToken',
            'accessTokenExpiresIn', and 'refreshToken'.

        Raises
        ------
        ServerError
            If there is an issue with the server response or decoding JSON data.

        """
        try:
            self._header["User-Agent"] = self.getUA()
            with self.session.get(
                DEMO_USER_TOKEN,
                headers=self._header,
            ) as r:
                r.raise_for_status()
                try:
                    return r.json()
                except requests.JSONDecodeError as e:
                    self._LOGGER.debug("JSONDecodeError: %s", e)
                    raise ServerError from e
        except (requests.RequestException, requests.Timeout) as e:
            self._LOGGER.debug("RequestException: %s", e)
            raise ServerError from e
