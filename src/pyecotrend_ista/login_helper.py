"""Login helper for Keycloak."""

from __future__ import annotations

import base64
import hashlib
import html
import json
import logging
import re
import secrets
import urllib.parse
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .const import (
    CLIENT_ID,
    CODE_CHALLENGE_METHODE,
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


class LoginHelper:
    """Login helper for Keycloak.

    Attributes
    ----------
    code_verifier : str
        Random URL-safe string used in OAuth2 code exchange.
    code_challenge : str | None
        Base64 URL-safe encoded SHA-256 hash of `code_verifier`, used in OAuth2 code exchange.
    session : requests.Session | None
        Optional session object for making HTTP requests.
    username : str
        Username for authentication.
    password : str
        Password for authentication.
    cookie : str | None
        Authentication cookie.
    auth_code : str | None
        Authorization code.
    form_action : str | None
        Form action URL for authentication.

    Notes
    -----
    This class provides utility methods for handling authentication and session management
    using Keycloak.

    """

    code_verifier = secrets.token_urlsafe(32)
    code_challenge = None

    session = None

    username = None
    password = None
    cookie = None
    auth_code = None
    form_action = None

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
        self.username = username
        self.password = password
        self.totp = totp

        __code_challenge: bytes = hashlib.sha256(self.code_verifier.encode("utf-8")).digest()
        _code_challenge: str = base64.urlsafe_b64encode(__code_challenge).decode("utf-8")

        self.code_challenge = _code_challenge.rstrip("=")

        if session:
            self.session = session
        else:
            self.session = requests.Session()

        self.session.verify = True
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504, 408])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        self.logger = logger if logger else logging.getLogger(__name__)

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
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error("Request error: %s", e)
            raise KeycloakOperationError from e

    def _login(self) -> None:
        """Log in to ista EcoTrend.

        Raises
        ------
        KeycloakAuthenticationError
            If an authentication error occurs during the login process.
        """
        try:
            self.auth_code = self._getAuthCode()
        except KeycloakAuthenticationError as error:
            raise KeycloakAuthenticationError(error) from error

    def _getAuthCode(self) -> str:
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
        cookie, form_action = self._getCookieAndAction()

        resp: requests.Response = self._send_request(
            "POST",
            form_action,
            data={"username": self.username, "password": self.password, "login": "Login", "credentialId": None},
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

    def _getCookieAndAction(self) -> tuple:
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
            url=PROVIDER_URL + "auth",
            params={
                "response_mode": RESPONSE_MODE,  # fragment
                "response_type": RESPONSE_TPYE,  # code
                "client_id": CLIENT_ID,
                "scope": SCOPE,
                "redirect_uri": REDIRECT_URI,
                "code_challenge": self.code_challenge,
                "code_challenge_method": CODE_CHALLENGE_METHODE,
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

    def refreshToken(self, refresh_token) -> tuple:
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
            url=PROVIDER_URL + "token",
            data={
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "client_id": CLIENT_ID,  # ecotrend
                "refresh_token": refresh_token,
            },
        )

        result = resp.json()

        return result["access_token"], result["expires_in"], result["refresh_token"]

    def getToken(self) -> tuple:
        """Retrieve access and refresh tokens using the obtained authorization code.

        Raises
        ------
        KeycloakPostError
            If there's an error during the POST request to retrieve tokens.

        KeycloakInvalidTokenError
            If the response status code is not 200, indicating an invalid token.

        Returns
        -------
        tuple[str, int, str]
            Tuple containing the access token, its expiration time in seconds,
            and the refresh token obtained from the authentication server.

        """
        self._login()
        _data = {
            "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
            "client_id": CLIENT_ID,  # ecotrend
            "redirect_uri": REDIRECT_URI,
            "code": self.auth_code,
            "code_verifier": self.code_verifier,
        }
        if self.totp:
            _data["totp"] = self.totp
        resp: requests.Response = self._send_request(
            "POST",
            url=PROVIDER_URL + "token",
            data=_data,
            timeout=TIMEOUT,
            allow_redirects=False,
        )

        raise_error_from_response(response=resp, error=KeycloakPostError)
        # If the response code is not 200 raise an exception.
        if resp.status_code != 200:
            raise KeycloakInvalidTokenError()
        result = resp.json()

        return result["access_token"], result["expires_in"], result["refresh_token"]

    def userinfo(self, token) -> Any:
        """."""
        header = {"Authorization": "Bearer " + token}
        resp: requests.Response = self._send_request("GET", url=PROVIDER_URL + "userinfo", headers=header)
        return resp.json()

    def well_know(self) -> Any:
        resp: requests.Response = self._send_request(
            "GET", url="https://keycloak.ista.com/realms/eed-prod/.well-known/openid-configuration"
        )
        raise_error_from_response(resp, KeycloakGetError)
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
            url=PROVIDER_URL + "logout",
            data={
                "client_id": CLIENT_ID,
                "refresh_token": token,
            },
        )

        return raise_error_from_response(resp, KeycloakPostError)


def _b64_decode(data) -> str:
    """Decode base64 data and pad with spaces to 4 - byte boundary."""
    data += "=" * (4 - len(data) % 4)
    return base64.b64decode(data).decode("utf-8")


def jwt_payload_decode(jwt) -> str:
    """Decodes and returns the JSON Web Token."""
    _, payload, _ = jwt.split(".")
    return json.dumps(json.loads(_b64_decode(payload)), indent=4)


def raise_error_from_response(
    response: requests.Response, error, expected_codes=None, skip_exists=False
) -> dict | Any | bytes | dict[str, str]:
    """Raise an exception for the response.

    :param response: The response object
    :type response: Response
    :param error: Error object to raise
    :type error: dict or Exception
    :param expected_codes: Set of expected codes, which should not raise the exception
    :type expected_codes: Sequence[int]
    :param skip_exists: Indicates whether the response on already existing object should be ignored
    :type skip_exists: bool

    :returns: Content of the response message
    :type: bytes or dict
    :raises KeycloakError: In case of unexpected status codes

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
