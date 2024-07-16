"""Unofficial python library for the ista EcoTrend API."""

from __future__ import annotations

from collections.abc import Callable
from http import HTTPStatus
from json import JSONDecodeError
import logging
from typing import cast

from httpx import AsyncClient, HTTPStatusError, RequestError, TimeoutException

from .const import (
    API_BASE_URL,
    CLIENT_ID,
    DEMO_USER_ACCOUNT,
    POST_LOGOUT_REDIRECT_URI,
    PROVIDER_URL,
    REDIRECT_URI,
    RESPONSE_MODE,
    RESPONSE_TPYE,
    SCOPE,
)
from .exceptions import KeycloakError, LoginError, ParserError, ServerError
from .keycloak import KeycloakAuthenticator
from .types import AccountResponse, ConsumptionsResponse, ConsumptionUnitDetailsResponse

_LOGGER = logging.getLogger(__package__)


class PyEcotrendIsta:
    """A Python client for interacting with the ista EcoTrend API.

    This class provides methods to authenticate and interact with the ista EcoTrend API.
    """

    _account: AccountResponse
    _uuid: str

    def __init__(
        self,
        email: str,
        password: str,
        otp_callback: Callable[[], str] | None = None,
        session: AsyncClient | None = None,
    ) -> None:
        """Initialize the PyEcotrendIsta client.

        Parameters
        ----------
        email : str
            The email address used to log in to the ista EcoTrend API.
        password : str
            The password used to log in to the ista EcoTrend API.
        otp_callback : callable, optional
            A callback function to request a new OTP if needed.
        session : httpx.AsyncClient, optional
            An optional httpx AsyncClient session for making HTTP requests. Default is None.

        """

        self._email: str = email
        self._password: str = password
        self._otp_callback = otp_callback

        self._client = KeycloakAuthenticator(
            provider_url=PROVIDER_URL,
            client_id=CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            response_mode=RESPONSE_MODE,
            response_type=RESPONSE_TPYE,
            scope=SCOPE,
            logger=_LOGGER,
            post_logout_redirect_uri=POST_LOGOUT_REDIRECT_URI,
            session=session,
        )

    async def __set_account(self) -> None:
        """Fetch and set account information from the API.

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

        url = f"{API_BASE_URL}account"
        try:
            r = await self._client.async_get(url)

        except JSONDecodeError as exc:
            raise ParserError("Loading account information failed due to an error parsing the request response") from exc
        except KeycloakError as exc:
            raise LoginError("Loading account information failed due to an authorization failure") from exc
        except HTTPStatusError as exc:
            raise ServerError(
                "Loading account information failed due to a server error: "
                f"[{exc.response.status_code}] {exc.response.reason_phrase}"
            ) from exc
        except TimeoutError as exc:
            raise ServerError("Loading account information failed due a connection timeout") from exc
        except RequestError as exc:
            raise ServerError("Loading account information failed due to a request exception") from exc

        self._account = cast(AccountResponse, r)
        self._uuid = self._account["activeConsumptionUnit"]


    async def login(self, otp: str | None = None) -> bool:
        """Perform the login process if not already connected or forced.

        Parameters
        ----------
        otp : str, optional
            An optional OTP code (Time-based One-Time Password) for two-factor authentication. Default is None.

        Returns
        -------
        bool
            True if login is successful.

        Raises
        ------
        LoginError
            If the login process fails due to an error.
        ServerError
            If a server error occurs during login attempts.
        """

        try:
            if self._email == DEMO_USER_ACCOUNT:
                await self._client.demo_login()
            else:
                await self._client.login(
                    username=self._email, password=self._password, otp=otp, otp_callback=self._otp_callback
                )

        except KeycloakError as exc:
            raise LoginError("Login failed due to an authorization failure, please verify your email and password") from exc
        except RequestError as exc:
            raise ServerError("Login failed due to a request exception, please try again later") from exc

        await self.__set_account()
        return True

    async def logout(self) -> None:
        """Perform logout operation by invalidating the current session.

        This method invokes the logout functionality in the loginhelper module,
        passing the current refresh token for session invalidation.


        Raises
        ------
        KeycloakError
            If an error occurs during the logout process. This error is raised based on the response from the logout request.

        Example:
        -------
        >>> client = PyEcotrendIsta(email='user@example.com', password='password')
        >>> await client.login()
        >>> await client.logout()

        """

        await self._client.logout()

    def get_uuids(self) -> list[str]:
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
        >>> uuids = client.get_uuids()
        >>> print(uuids)
        ['uuid1', 'uuid2', 'uuid3']

        """
        return list(self._account.get("residentAndConsumptionUuidsMap", {}).values())


    async def get_consumption_data(self, obj_uuid: str | None = None) -> ConsumptionsResponse:
        """Fetch consumption data from the API for a specific consumption unit.

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

        """

        params = {"consumptionUnitUuid": obj_uuid or self._uuid}
        url = f"{API_BASE_URL}consumptions"
        try:
            r = await self._client.async_get(url, params=params)
        except JSONDecodeError as exc:
            raise ParserError("Loading consumption data failed due to an error parsing the request response") from exc
        except KeycloakError as exc:
            raise LoginError("Loading consumption data failed failed due to an authorization failure") from exc
        except HTTPStatusError as exc:
            if exc.response.status_code == HTTPStatus.BAD_REQUEST:
                raise ValueError(
                    f"Retrieving data for consumption unit {obj_uuid or self._uuid} failed. Possibly invalid UUID."
                ) from exc
            raise ServerError(
                "Loading consumption data failed due to a server error: "
                f"[{exc.response.status_code}] {exc.response.reason_phrase}"
            ) from exc
        except TimeoutException as exc:
            raise ServerError("Loading consumption data failed due a connection timeout") from exc
        except RequestError as exc:
            raise ServerError("Loading consumption data failed due to a request exception") from exc

        return cast(ConsumptionsResponse, r)

    async def get_consumption_unit_details(self) -> ConsumptionUnitDetailsResponse:
        """Retrieve details of the consumption unit from the API.

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
            r = await self._client.async_get(url)
        except JSONDecodeError as exc:
            raise ParserError("Loading consumption unit details failed due to an error parsing the request response") from exc
        except KeycloakError as exc:
            raise LoginError("Loading consumption unit details failed failed due to an authorization failure") from exc
        except HTTPStatusError as exc:
            raise ServerError(
                "Loading consumption unit details failed due to a server error "
                f"[{exc.response.status_code}: {exc.response.reason_phrase}]"
            ) from exc
        except TimeoutException as exc:
            raise ServerError("Loading consumption unit details failed due a connection timeout") from exc
        except RequestError as exc:
            raise ServerError("Loading consumption unit details failed due to a request exception") from exc

        return cast(ConsumptionUnitDetailsResponse, r)


    def get_account(self) -> AccountResponse:
        """Retrieve the account information.

        Returns account information.

        Returns
        -------
        AccountResponse
            Account information if available.

        Raises
        ------
        LoginError
            If account data is unavailable due to missing authentication.

        Notes
        -----
        This method requires a previous call of `login()`, otherwise account data is unavailable.

        """
        try:
            return self._account
        except AttributeError as exc:
            raise LoginError(
                "Retrieving account data failed failed due to an authorization failure, please login first"
            ) from exc
