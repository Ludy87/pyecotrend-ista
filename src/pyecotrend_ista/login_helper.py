"""Login helper for Keycloak."""

from __future__ import annotations

import html
import logging
import re
from typing import Any, cast
import urllib.parse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .const import (
    CLIENT_ID,
    DEMO_USER_ACCOUNT,
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    PROVIDER_URL,
    REDIRECT_URI,
    RESPONSE_MODE,
    RESPONSE_TPYE,
    SCOPE,
    TIMEOUT,
)
from .exception_classes import (
    KeycloakAuthenticationError,
    KeycloakCodeNotFound,
    KeycloakGetError,
    KeycloakInvalidTokenError,
    KeycloakOperationError,
    KeycloakPostError,
)
from .types import GetTokenResponse


class LoginHelper:
    """Login helper for Keycloak.

    Attributes
    ----------
    session : requests.Session
        Optional session object for making HTTP requests.
    username : str
        Username for authentication.
    password : str
        Password for authentication.
    cookie : str
        Authentication cookie.
    auth_code : str
        Authorization code.
    form_action : str
        Form action URL for authentication.

    Notes
    -----
    This class provides utility methods for handling authentication and session management
    using Keycloak.

    """

    session: requests.Session
    cookie: str
    auth_code: str
    form_action: str

    def __init__(
        self,
        username: str,
        password: str,
        totp: str | None = None,
        session: requests.Session | None = None,
        logger=None,
    ) -> None:
        """Initialize the object with username and password.

        Parameters
        ----------
        username : str
            Username for authentication.
        password : str
            Password for authentication.
        totp : str, optional
            Time-based One-Time Password if enabled, by default None.
        session : requests.Session, optional
            Optional session object for making HTTP requests, by default None.
        logger : logging.Logger, optional
            Logger object for logging messages, by default None.

        """
        self.username: str = username
        self.password: str = password
        self.totp: str | None = totp


        self.session = session or requests.Session()

        self.session.verify = True
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504, 408])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        self.logger = logger or logging.getLogger(__name__)

    def _send_request(self, method, url, **kwargs) -> requests.Response:
        """Send an HTTP request using the session object.

        Parameters
        ----------
        method : str
            HTTP method for the request (e.g., 'GET', 'POST', 'PUT', 'DELETE').
        url : str
            URL to send the request to.
        **kwargs : dict
            Additional keyword arguments to pass to `session.request`.

        Returns
        -------
        requests.Response
            Response object returned by the HTTP request.

        Raises
        ------
        ValueError
            If `self.session` is not initialized (i.e., is `None`).
        KeycloakOperationError
            If an HTTP request exception (`requests.RequestException`) occurs.

        """
        if self.session is None:
            raise ValueError("Session object is not initialized.")
        try:
            response = self.session.request(method, url, **kwargs)
            self.logger.debug("Performed % request: %s [%s]:\n%s", method, url, response.status_code, response.text[:100])
            response.raise_for_status()
        except requests.RequestException as e:
            raise KeycloakOperationError from e

        return response

    def _login(self) -> None:
        """Log in to ista EcoTrend.

        Raises
        ------
        KeycloakAuthenticationError
            If an authentication error occurs during the login process.
        """
        try:
            self.auth_code = self._get_auth_code()
        except KeycloakAuthenticationError as error:
            raise KeycloakAuthenticationError(error.error_message) from error

    def _get_auth_code(self) -> str:
        """
        Retrieve the authentication code for ista EcoTrend.

        Returns
        -------
        str
            The authentication code obtained from the ista EcoTrend API.

        Raises
        ------
        KeycloakAuthenticationError
            If an authentication error occurs during the login process.
        KeycloakCodeNotFound
            If the authentication code ('code') is not found in the redirection URL parameters.

        """
        cookie, form_action = self._get_cookie_and_action()

        resp: requests.Response = self._send_request(
            "POST",
            form_action,
            data={
                "username": self.username,
                "password": self.password,
                "login": "Login",
                "credentialId": None,
            },
            headers={"Cookie": cookie},
            timeout=TIMEOUT,
            allow_redirects=False,
        )

        # If the response code is not 302
        # raise_error_from_response(resp, KeycloakAuthenticationError, expected_codes=[302])
        if resp.status_code != 302:
            if resp.status_code == 200:
                form_action = re.search(r'<form\s+.*?\s+action="(.*?)"', resp.text, re.DOTALL)
                if form_action and form_action.group(1):
                    self._login()
            else:
                raise_error_from_response(resp, KeycloakAuthenticationError)

        # If Location header is not present raise exception.
        if "Location" not in resp.headers:
            raise KeycloakCodeNotFound("header[Location] not found", response_code=resp.status_code)
        redirect = resp.headers["Location"]
        query = urllib.parse.urlparse(redirect).fragment
        redirect_params = urllib.parse.parse_qs(query)

        # If code is not in redirect_params or len redirect_params code is less than 1
        if "code" not in redirect_params or len(redirect_params["code"]) < 1:
            raise KeycloakCodeNotFound("header[Location] Code not found", response_code=resp.status_code)
        return redirect_params["code"][0]

    def _get_cookie_and_action(self) -> tuple:
        """Retrieve the cookie and action URL from the OpenID Connect provider.

        Returns
        -------
        tuple[str, str]
            A tuple containing the cookie obtained from the response headers and the action URL extracted from the HTML form.

        Raises
        ------
        KeycloakGetError
            If the GET request to the OpenID Connect provider returns a non-200 status code.

        """
        form_action = None
        resp: requests.Response = self._send_request(
            "GET",
            url=f"{PROVIDER_URL}auth",
            params={
                "response_mode": RESPONSE_MODE,  # fragment
                "response_type": RESPONSE_TPYE,  # code
                "client_id": CLIENT_ID,
                "scope": SCOPE,
                "redirect_uri": REDIRECT_URI,
            },
            timeout=TIMEOUT,
            allow_redirects=False,
        )

        # If the response code is not 200 raise an exception.
        raise_error_from_response(resp, KeycloakGetError)

        cookie = resp.headers["Set-Cookie"]
        cookie = "; ".join(c.split(";")[0] for c in cookie.split(", "))
        search = re.search(r'<form\s+.*?\s+action="(.*?)"', resp.text, re.DOTALL)
        if search:
            form_action = html.unescape(search.group(1))
        return cookie, form_action

    def refresh_token(self, refresh_token) -> tuple:
        """Refresh the access token using the provided refresh token.

        Parameters
        ----------
        refresh_token : str
            The refresh token obtained from previous authentication.

        Returns
        -------
        tuple[str, int, str]
            Tuple containing the refreshed access token, its expiration time in seconds,
            and the new refresh token.
        """
        resp: requests.Response = self._send_request(
            "POST",
            url=f"{PROVIDER_URL}token",
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "client_id": CLIENT_ID,  # ecotrend
                "refresh_token": refresh_token,
            },
        )

        result = resp.json()

        return result["access_token"], result["expires_in"], result["refresh_token"]

    def get_token(self) -> GetTokenResponse:
        """Retrieve access and refresh tokens using the obtained authorization code.

        Raises
        ------
        KeycloakPostError
            If there's an error during the POST request to retrieve tokens.

        KeycloakInvalidTokenError
            If the response status code is not 200, indicating an invalid token.

        Returns
        -------
        GetTokenResponse
            A TypedDict containing authentication tokens including 'accessToken',
            'accessTokenExpiresIn', and 'refreshToken'.

        """
        self._login()
        _data = {
            "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
            "client_id": CLIENT_ID,  # ecotrend
            "redirect_uri": REDIRECT_URI,
            "code": self.auth_code,
        }
        if self.totp:
            _data["totp"] = self.totp
        resp: requests.Response = self._send_request(
            "POST",
            url=f"{PROVIDER_URL}token",
            data=_data,
            timeout=TIMEOUT,
            allow_redirects=False,
        )

        raise_error_from_response(response=resp, error=KeycloakPostError)
        # If the response code is not 200 raise an exception.
        if resp.status_code != 200:
            raise KeycloakInvalidTokenError()

        return cast(GetTokenResponse, resp.json())

    def userinfo(self, token) -> Any:
        """Retrieve user information from the Keycloak provider.

        This method sends a GET request to the Keycloak `userinfo` endpoint using the provided
        token in the Authorization header. It returns the JSON response containing user information.

        Parameters
        ----------
        token : str
            The access token to be used for authorization.

        Returns
        -------
        Any
            A dictionary containing the user information if the request is successful, or an empty
            dictionary if the user is a demo user.

        Raises
        ------
        KeycloakOperationError
            If the request fails due to a Keycloak operation error.
        """
        if self.username == DEMO_USER_ACCOUNT:
            return {}

        header = {"Authorization": f"Bearer {token}"}
        url = f"{PROVIDER_URL}userinfo"

        resp: requests.Response = self._send_request("GET", url=url, headers=header)

        return resp.json()

    def logout(self, token) -> dict | Any | bytes | dict[str, str]:
        """Log out the user session from the identity provider.

        Parameters
        ----------
        token : str
            Refresh token associated with the user session.

        Returns
        -------
        Union[dict, Any, bytes, dict[str, str]]
            Response data from the logout request. The exact type may vary based on the response content.

        Raises
        ------
        KeycloakPostError
            If an error occurs during the POST request to logout the user.

        """
        resp: requests.Response = self._send_request(
            "POST",
            url=f"{PROVIDER_URL}logout",
            data={
                "client_id": CLIENT_ID,
                "refresh_token": token,
            },
        )

        return raise_error_from_response(resp, KeycloakPostError)


def raise_error_from_response(
    response: requests.Response, error, expected_codes=None, skip_exists=False
) -> dict | Any | bytes | dict[str, str]:
    """Raise an exception for the response.

    Parameters
    ----------
    response : Response
        The response object.
    error : dict or Exception
        Error object to raise.
    expected_codes : Sequence[int], optional
        Set of expected codes, which should not raise the exception.
    skip_exists : bool, optional
        Indicates whether the response on already existing object should be ignored.

    Returns
    -------
    bytes or dict
        Content of the response message.

    Raises
    ------
    KeycloakError
        In case of unexpected status codes.

    Notes
    -----
    Source from https://github.com/marcospereirampj/python-keycloak/blob/c98189ca6951f12f1023ed3370c9aaa0d81e4aa4/src/keycloak/exceptions.py
    """  # noqa: DAR401,DAR402
    if expected_codes is None:
        expected_codes = [200, 201, 204]

    if response.status_code in expected_codes:
        if response.status_code == requests.codes.no_content:
            return {}

        try:
            return response.json()
        except ValueError:
            return response.content

    if skip_exists and response.status_code == 409:
        return {"msg": "Already exists"}

    try:
        message = response.json()["message"]
    except (KeyError, ValueError):
        message = response.content

    if isinstance(error, dict):
        error = error.get(response.status_code, KeycloakOperationError)
    else:
        if response.status_code == 401:
            error = KeycloakAuthenticationError

    raise error(error_message=message, response_code=response.status_code, response_body=response.content)
