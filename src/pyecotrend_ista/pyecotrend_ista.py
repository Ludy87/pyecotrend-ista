# numpydoc ignore=EX01,GL06,GL07
"""Unofficial python library for the ista EcoTrend API.

This module provides a Python client for interacting with the ista EcoTrend API.

Classes
-------
PyEcotrendIsta
    A Python client for interacting with the ista EcoTrend API.
"""

from __future__ import annotations

from http import HTTPStatus
import logging
import time
from typing import Any, cast
import warnings

import requests

from .const import API_BASE_URL, DEMO_USER_ACCOUNT, VERSION
from .exception_classes import KeycloakError, LoginError, ParserError, ServerError, deprecated
from .helper_object_de import CustomRaw
from .login_helper import LoginHelper
from .types import AccountResponse, ConsumptionsResponse, ConsumptionUnitDetailsResponse, GetTokenResponse

_LOGGER = logging.getLogger(__name__)


class PyEcotrendIsta:  # numpydoc ignore=PR01
    """
    A Python client for interacting with the ista EcoTrend API.

    This class provides methods to authenticate and interact with the ista EcoTrend API.

    Attributes
    ----------
    _account : AccountResponse
        The account information.
    _uuid : str
        The UUID of the consumption unit.
    _access_token : str | None
        The access token for API authentication.
    _refresh_token : str | None
        The refresh token for obtaining new access tokens.
    _access_token_expires_in : int
        The expiration time of the access token.
    _header : dict[str, str]
        The headers used in HTTP requests.
    _support_code : str | None
        The support code for the account.
    _start_timer : float
        The start time for tracking elapsed time.

    Examples
    --------
    Initialize the client and log in:

    >>> client = PyEcotrendIsta(email="user@example.com", password="password")
    >>> client.login()
    """

    _account: AccountResponse
    _uuid: str
    _access_token: str | None = None
    _refresh_token: str | None = None
    _access_token_expires_in: int = 0
    _header: dict[str, str] = {}
    _support_code: str | None = None
    _start_timer: float = 0.0

    def __init__(
        self,
        email: str,
        password: str,
        logger: logging.Logger | None = None,
        hass_dir: str | None = None,
        totp: str | None = None,
        session: requests.Session | None = None,
    ) -> None:  # numpydoc ignore=ES01,EX01
        """Initialize the PyEcotrendIsta client.

        Parameters
        ----------
        email : str
            The email address used to log in to the ista EcoTrend API.
        password : str
            The password used to log in to the ista EcoTrend API.
        logger : logging.Logger, optional
            [DEPRECATED] An optional logger instance for logging messages. Default is None.
        hass_dir : str, optional
            [DEPRECATED] An optional directory for Home Assistant configuration. Default is None.
        totp : str, optional
            An optional TOTP (Time-based One-Time Password) for two-factor authentication. Default is None.
        session : requests.Session, optional
            An optional requests session for making HTTP requests. Default is None.
        """
        if hass_dir:
            warnings.warn(
                "The 'hass_dir' parameter is deprecated and will be removed in a future release.",
                DeprecationWarning,
                stacklevel=2,
            )

        if logger:
            warnings.warn(
                "The 'logger' parameter is deprecated and will be removed in a future release.",
                DeprecationWarning,
                stacklevel=2,
            )

        self._email: str = email.strip()
        self._password: str = password


        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": self.get_user_agent()})

        self.loginhelper = LoginHelper(
            username=self._email,
            password=self._password,
            totp=totp,
            session=self.session,
            logger=_LOGGER,
        )

    @property
    def access_token(self):  # numpydoc ignore=EX01
        """
        Retrieve the access token, refreshing it if necessary.

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
            self._access_token_expires_in > 0
            and self._is_connected()
            and self._refresh_token
            and self._access_token_expires_in <= time.time() - self._start_timer
        ):
            self.__refresh()
        return self._access_token

    @access_token.setter
    def access_token(self, value: str) -> None:  # numpydoc ignore=ES01,EX01
        """
        Setter method for the access token attribute.

        Parameters
        ----------
        value : str
            The new access token value.

        Notes
        -----
        Sets the access token value and updates the start timer to the current time.
        This method is used to assign a new access token value and reset the timer
        tracking the token's validity period.
        """
        self._access_token = value
        self._start_timer = time.time()
        _LOGGER.debug(
            "Initialized start timer for refresh token at %s",
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._start_timer)),
        )

    def _is_connected(self) -> bool:  # numpydoc ignore=ES01,EX01
        """
        Check if the client is connected by verifying the presence of an access token.

        Returns
        -------
        bool
            True if the client has a valid access token, False otherwise.
        """
        return bool(self._access_token)

    def __login(self) -> str | None:  # numpydoc ignore=ES01,EX01
        """
        Perform the login process to obtain an access token.

        If the email is a demo account, it logs in using a demo user login function.
        For other accounts, it retrieves a token using a login helper.

        Returns
        -------
        str or None
            The access token if login is successful, None otherwise.
        """
        if self._email == DEMO_USER_ACCOUNT:
            _LOGGER.debug("Logging in as demo user")
            token = self.demo_user_login()
        else:
            token = self.loginhelper.get_token()
        if token:
            self.access_token = token["access_token"]
            self._access_token_expires_in = token["expires_in"]
            self._refresh_token = token["refresh_token"]
            return self.access_token
        return None

    def __refresh(self) -> None:  # numpydoc ignore=ES01,EX01
        """
        Refresh the access token using the refresh token.

        This method retrieves a new access token, updates internal variables,
        and resets the token expiration timer.

        Raises
        ------
        ParserError
            If there is an error parsing the request response.
        LoginError
            If there is an authorization failure.
        ServerError
            If there is a server error, connection timeout, or request exception.

        Notes
        -----
        This method assumes `self._refresh_token` is already set.
        """
        (
            self.access_token,
            self._access_token_expires_in,
            self._refresh_token,
        ) = self.loginhelper.refresh_token(self._refresh_token)

        self._header["Authorization"] = f"Bearer {self.access_token}"

    def __set_account(self) -> None:  # numpydoc ignore=ES01,EX01
        """
        Fetch and set account information from the API.

        This method performs an API request to retrieve account information,
        handles various potential errors that might occur during the request,
        and sets instance variables accordingly using the response data.

        Raises
        ------
        ParserError
            If there is an error parsing the JSON response.
        LoginError
            If the request fails due to an authorization error.
        ServerError
            If the request fails due to a server error, timeout, or other request exceptions.
        """
        self._header = {
            "Content-Type": "application/json",
            "User-Agent": self.get_user_agent(),
            "Authorization": f"Bearer {self.access_token}",
        }
        url = f"{API_BASE_URL}account"
        try:
            with self.session.get(url, headers=self._header) as r:
                _LOGGER.debug("Performed GET request: %s [%s]:\n%s", url, r.status_code, r.text)
                r.raise_for_status()
                try:
                    data = r.json()
                except requests.JSONDecodeError as exc:
                    raise ParserError(
                        "Loading account information failed due to an error parsing the request response"
                    ) from exc
        except requests.HTTPError as exc:
            if exc.response.status_code == HTTPStatus.UNAUTHORIZED:
                raise LoginError("Loading account information failed due to an authorization failure") from exc

            raise ServerError(
                "Loading account information failed due to a server error "
                f"[{exc.response.status_code}: {exc.response.reason}]"
            ) from exc
        except requests.Timeout as exc:
            raise ServerError("Loading account information failed due a connection timeout") from exc
        except requests.RequestException as exc:
            raise ServerError("Loading account information failed due to a request exception") from exc

        self._account = cast(AccountResponse, data)
        self._uuid = data["activeConsumptionUnit"]

    def get_version(self) -> str:  # numpydoc ignore=EX01,ES01
        """
        Get the version of the PyEcotrendIsta client.

        Returns
        -------
        str
            The version number of the PyEcotrendIsta client.
        """
        return VERSION

    getVersion = deprecated(get_version, "getVersion")  # noqa: N815

    def login(self, force_login: bool = False, debug: bool = False, **kwargs) -> str | None:  # numpydoc ignore=ES01,EX01,PR01,PR02
        """
        Perform the login process if not already connected or forced.

        Parameters
        ----------
        force_login : bool, optional
            If True, forces a fresh login attempt even if already connected. Default is False.
        debug : bool, optional
            [DEPRECATED] Flag indicating whether to enable debug logging. Default is False.

        Deprecated Parameters
        ----------------------
        forceLogin : bool, optional
            Use `force_login` instead. This parameter is deprecated and will be removed in a future release.

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

        Notes
        -----
        - The `forceLogin` parameter is handled via `**kwargs` for backward compatibility.
        - The `debug` parameter is deprecated; use appropriate logging configuration instead.
        """
        if debug:
            warnings.warn(
                "The 'debug' parameter is deprecated and will be removed in a future release.",
                DeprecationWarning,
                stacklevel=2,
            )

        if "forceLogin" in kwargs:
            warnings.warn(
                "The 'forceLogin' keyword parameter is deprecated and will be removed in a future release. "
                "Use force_login instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            force_login = kwargs["forceLogin"]

        if not self._is_connected() or force_login:
            try:
                self.__login()
                self.__set_account()
            except (KeycloakError, LoginError) as exc:
                # Login failed
                self._access_token = None
                raise LoginError(
                    "Login failed due to an authorization failure, please verify your email and password"
                ) from exc
            except ServerError as exc:
                raise ServerError("Login failed due to a request exception, please try again later") from exc

        return self.access_token

    def userinfo(self, token):
        """
        Retrieve user information using the provided access token.

        This method constructs an authorization header using the provided access token
        and sends a GET request to the userinfo endpoint of the provider API. It expects
        a JSON response with user information.

        Parameters
        ----------
        token : str
            The access token used for authentication.

        Returns
        -------
        Any
            JSON response containing user information.

        Raises
        ------
        requests.exceptions.RequestException
            If an error occurs while making the HTTP request.

        Notes
        -----
        This method constructs an authorization header using the provided access token
        and sends a GET request to the userinfo endpoint of the provider API.
        It expects a JSON response with user information.

        Examples
        --------
        >>> client = PyEcotrendIsta(email="user@example.com", password="password")
        >>> token = client.login()
        >>> user_info = client.userinfo(token)
        """
        return self.loginhelper.userinfo(token=token)

    def logout(self) -> None:
        """
        Perform logout operation by invalidating the current session.

        This method invokes the logout functionality in the loginhelper module,
        passing the current refresh token for session invalidation.

        Raises
        ------
        KeycloakPostError
        If an error occurs during the logout process. This error is raised based on the response from the logout request.

        Notes
        -----
        This method assumes `self._refresh_token` is already set.

        Examples
        --------
        >>> client = PyEcotrendIsta(email="user@example.com", password="password")
        >>> client.login()
        >>> client.logout()
        """
        if self.loginhelper.username != DEMO_USER_ACCOUNT:
            self.loginhelper.logout(self._refresh_token)

    def get_uuids(self) -> list[str]:  # numpydoc ignore=ES01
        """
        Retrieve UUIDs of consumption units registered in the account.

        Returns
        -------
        list[str]
            A list containing UUIDs of consumption units. Each UUID represents a consumption unit,
            which could be a flat or a house for which consumption readings are provided.

        Notes
        -----
        A consumption unit represents a residence or building where consumption readings are recorded.
        The UUIDs are extracted from the `_residentAndConsumptionUuidsMap` attribute.

        Examples
        --------
        >>> client = PyEcotrendIsta(email="user@example.com", password="password")
        >>> client.login()
        >>> uuids = client.get_uuids()
        >>> print(uuids)
        ['uuid1', 'uuid2', 'uuid3']
        """
        return list(self._account.get("residentAndConsumptionUuidsMap", {}).values())

    getUUIDs = deprecated(get_uuids, "getUUIDs")  # noqa: N815

    # pylint: disable=too-many-branches,too-many-statements
    def consum_raw(  # noqa: C901
        self,
        select_year: list[int] | None = None,
        select_month: list[int] | None = None,
        filter_none: bool = True,
        obj_uuid: str | None = None,
    ) -> dict[str, Any] | ConsumptionsResponse:  # noqa: C901
        """
        Process and filter consumption and cost data for a given consumption unit.

        This method processes consumption and cost data obtained from the `get_consumption_data` method.
        It filters and aggregates data based on the parameters provided.

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
        dict[str, Any] | ConsumptionsResponse
            Processed data including consumption types, total additional values, last values,
            last costs, sum by year, and last year compared consumption.

        Raises
        ------
        Exception
            If there is an unexpected error during data processing.

        Notes
        -----
        This method processes consumption and cost data obtained from the `get_consumption_data` method.
        It filters and aggregates data based on the parameters provided.

        Examples
        --------
        >>> api = PyEcotrendIsta()
        >>> result = api.consum_raw(select_year=[2023], select_month=[7], filter_none=True, obj_uuid="uuid")
        >>> print(result)
        """
        # Fetch raw consumption data for the specified UUID
        c_raw: ConsumptionsResponse = self.get_consumption_data(obj_uuid)

        if not isinstance(c_raw, dict) or (c_raw.get("consumptions") is None and c_raw.get("costs") is None):
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
                or consumption.get("readings") is None
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

        # pylint: disable=too-many-nested-blocks
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
            for costs_by_energy_type in costs[0]["costsByEnergyType"]:
                # pylint: disable=too-many-boolean-expressions
                if (
                    costs_by_energy_type is None
                    or "type" not in costs_by_energy_type
                    or costs_by_energy_type["type"] is None
                    or "comparedCost" not in costs_by_energy_type
                    or costs_by_energy_type["comparedCost"] is None
                    or "smiley" not in costs_by_energy_type["comparedCost"]
                    or costs_by_energy_type["comparedCost"]["smiley"] is None
                    or "comparedPercentage" not in costs_by_energy_type["comparedCost"]
                    or costs_by_energy_type["comparedCost"]["comparedPercentage"] is None
                ):
                    continue

                if costs_by_energy_type["type"] not in last_costs:
                    last_costs[costs_by_energy_type["type"]] = 0.0
                last_costs[costs_by_energy_type["type"]] += costs_by_energy_type["value"]
                last_costs["unit"] = costs_by_energy_type["unit"]
                if costs_by_energy_type["type"] == "warmwater":
                    if costs_by_energy_type["comparedCost"]["smiley"] == ["MAD", "EQUAL"]:
                        last_costs["ww"] = costs_by_energy_type["comparedCost"]["comparedPercentage"]
                    elif costs_by_energy_type["comparedCost"]["smiley"] in ["HAPPY"]:
                        last_costs["ww"] = costs_by_energy_type["comparedCost"]["comparedPercentage"] * -1
                elif costs_by_energy_type["type"] == "water":
                    if costs_by_energy_type["comparedCost"]["smiley"] == ["MAD", "EQUAL"]:
                        last_costs["w"] = costs_by_energy_type["comparedCost"]["comparedPercentage"]
                    elif costs_by_energy_type["comparedCost"]["smiley"] in ["HAPPY"]:
                        last_costs["w"] = costs_by_energy_type["comparedCost"]["comparedPercentage"] * -1
                elif costs_by_energy_type["type"] == "heating":
                    if costs_by_energy_type["comparedCost"]["smiley"] in ["MAD", "EQUAL"]:
                        last_costs["h"] = costs_by_energy_type["comparedCost"]["comparedPercentage"]
                    elif costs_by_energy_type["comparedCost"]["smiley"] in ["HAPPY"]:
                        last_costs["h"] = costs_by_energy_type["comparedCost"]["comparedPercentage"] * -1
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

    def get_consumption_data(self, obj_uuid: str | None = None) -> ConsumptionsResponse:
        """
        Fetch consumption data from the API for a specific consumption unit.

        This method sends a GET request to the ista EcoTrend API to retrieve consumption data
        for a specific consumption unit identified by the provided UUID. If no UUID is provided,
        the method uses the UUID associated with the instance.

        Parameters
        ----------
        obj_uuid : str, optional
            The UUID of the consumption unit. If not provided,
            defaults to the UUID associated with the instance (`self._uuid`).

        Returns
        -------
        ConsumptionsResponse
            A dictionary containing the consumption data fetched from the API.


        Raises
        ------
        LoginError
            If the API responds with an error indicating authorization failure.
        ParserError
            If there is an error parsing the request response.
        ValueError
            If the provided UUID is invalid.
        ServerError
            If there is a server error, connection timeout, or request exception.

        Examples
        --------
        >>> api = PyEcotrendIsta()
        >>> data = api.get_consumption_data(obj_uuid="uuid")
        >>> print(data)
        """
        params = {"consumptionUnitUuid": obj_uuid or self._uuid}
        url = f"{API_BASE_URL}consumptions"
        try:
            with self.session.get(
                url,
                params=params,
                headers=self._header,
            ) as result:
                _LOGGER.debug("Performed GET request: %s [%s]:\n%s", url, result.status_code, result.text[:100])
                result.raise_for_status()
                try:
                    return cast(ConsumptionsResponse, result.json())
                except requests.JSONDecodeError as exc:
                    raise ParserError("Loading consumption data failed due to an error parsing the request response") from exc
        except requests.HTTPError as exc:
            if exc.response.status_code == HTTPStatus.UNAUTHORIZED:
                raise LoginError("Loading consumption data failed failed due to an authorization failure") from exc
            if exc.response.status_code == HTTPStatus.BAD_REQUEST:
                raise ValueError(
                    f"Invalid UUID. Retrieving data for consumption unit {obj_uuid or self._uuid} failed"
                ) from exc
            raise ServerError(
                "Loading consumption data failed due to a server error " f"[{exc.response.status_code}: {exc.response.reason}]"
            ) from exc
        except requests.Timeout as exc:
            raise ServerError("Loading consumption data failed due a connection timeout") from exc
        except requests.RequestException as exc:
            raise ServerError("Loading consumption data failed due to a request exception") from exc

    get_raw = deprecated(get_consumption_data, "get_raw")

    def get_consumption_unit_details(self) -> ConsumptionUnitDetailsResponse:  # numpydoc ignore=ES01,EX01
        """
        Retrieve details of the consumption unit from the API.

        Returns
        -------
        ConsumptionUnitDetailsResponse
            A dictionary containing the details of the consumption unit.

        Raises
        ------
        LoginError
            If the API responds with an authorization failure.
        ParserError
            If there is an issue with decoding the JSON response
        ServerError
            If there is a server error, connection timeout, or request exception.
        """
        url = f"{API_BASE_URL}menu"
        try:
            with self.session.get(url, headers=self._header) as r:
                _LOGGER.debug("Performed GET request: %s [%s]:\n%s", url, r.status_code, r.text)

                r.raise_for_status()
                try:
                    return cast(ConsumptionUnitDetailsResponse, r.json())
                except requests.JSONDecodeError as exc:
                    raise ParserError(
                        "Loading consumption unit details failed due to an error parsing the request response"
                    ) from exc
        except requests.HTTPError as exc:
            if exc.response.status_code == HTTPStatus.UNAUTHORIZED:
                raise LoginError("Loading consumption unit details failed failed due to an authorization failure") from exc

            raise ServerError(
                "Loading consumption unit details failed due to a server error "
                f"[{exc.response.status_code}: {exc.response.reason}]"
            ) from exc
        except requests.Timeout as exc:
            raise ServerError("Loading consumption unit details failed due a connection timeout") from exc
        except requests.RequestException as exc:
            raise ServerError("Loading consumption unit details failed due to a request exception") from exc

    def get_support_code(self) -> str | None:  # numpydoc ignore=ES01,EX01
        """
        Return the support code associated with the instance.

        Returns
        -------
        str or None
            The support code associated with the instance, or None if not set.
        """
        return getattr(self, "_account", {}).get("supportCode")

    getSupportCode = deprecated(get_support_code, "getSupportCode")  # noqa: N815

    def get_user_agent(self) -> str:  # numpydoc ignore=ES01,EX01
        """
        Return the User-Agent string used for HTTP requests.

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

    def demo_user_login(self) -> GetTokenResponse:  # numpydoc ignore=ES01,EX01
        """
        Retrieve authentication tokens for the demo user.

        Returns
        -------
        GetTokenResponse
            A TypedDict containing authentication tokens including 'accessToken',
            'accessTokenExpiresIn', and 'refreshToken'.

        Raises
        ------
        ParserError
            If there is an error parsing the request response.
        ServerError
            If there is a server error, connection timeout, or request exception.
        """
        url = f"{API_BASE_URL}demo-user-token"
        try:
            self._header["User-Agent"] = self.get_user_agent()
            with self.session.get(url, headers=self._header) as r:
                _LOGGER.debug("Performed GET request %s [%s]:\n%s", url, r.status_code, r.text)

                r.raise_for_status()
                try:
                    data = r.json()
                    key = iter(GetTokenResponse.__annotations__)
                    token = {next(key): value for value in data.values()}
                    return cast(GetTokenResponse, token)
                except requests.JSONDecodeError as exc:
                    raise ParserError("Demo user authentication failed due to an error parsing the request response") from exc
        except requests.HTTPError as exc:
            raise ServerError(
                "Demo user authentication failed due to a server error " f"[{exc.response.status_code}: {exc.response.reason}]"
            ) from exc
        except requests.Timeout as exc:
            raise ServerError("Demo user authentication failed due a connection timeout") from exc
        except requests.RequestException as exc:
            raise ServerError("Demo user authentication failed due to a request exception") from exc

    def get_account(self) -> AccountResponse | None:  # numpydoc ignore=ES01,EX01
        """
        Retrieve the account information.

        Returns the `_account` attribute if it exists, otherwise returns None.

        Returns
        -------
        AccountResponse | None
            Account information if available, otherwise None.
        """
        return getattr(self, "_account", None)
