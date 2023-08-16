"""Login helper file."""
from __future__ import annotations

import base64
import hashlib
import html
import json
import re
import secrets
import urllib.parse
from typing import Any

import requests

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
)
from .exception_classes import (
    KeycloakAuthenticationError,
    KeycloakGetError,
    KeycloakInvalidTokenError,
    KeycloakOperationError,
    KeycloakPostError,
)


class LoginHelper:
    """Login helper for keycloak."""

    code_verifier = secrets.token_urlsafe(32)
    code_challenge = None

    session = None

    username = None
    password = None
    cookie = None
    auth_code = None
    form_action = None

    def __init__(self, username: str, password: str, totp: str = None, session: requests.Session = None) -> None:
        """Initializes the object with username and password."""
        self.username = username
        self.password = password
        self.totp = totp

        _code_challenge = hashlib.sha256(self.code_verifier.encode("utf-8")).digest()
        _code_challenge = base64.urlsafe_b64encode(_code_challenge).decode("utf-8")

        self.code_challenge = _code_challenge.rstrip("=")

        if session:
            self.session = session
        else:
            self.session = requests.Session()

        self.session.verify = True

    def _login(self) -> None:
        """Logs in to ista."""
        try:
            self.auth_code = self._getAuthCode()
        except KeycloakAuthenticationError as error:
            raise KeycloakAuthenticationError(error) from error

    def _getAuthCode(self) -> str:
        """Get auth code from ista."""
        cookie, form_action = self._getCookieAndAction()

        resp: requests.Response = self.session.post(
            url=form_action,
            data={"username": self.username, "password": self.password},
            headers={"Cookie": cookie},
            timeout=60,
            allow_redirects=False,
        )
        # If the response code is not 302
        # raise_error_from_response(resp, KeycloakAuthenticationError, expected_codes=[302])
        if resp.status_code != 302:
            if resp.status_code == 200:
                form_action = re.search(r'<form\s+.*?\s+action="(.*?)"', resp.text, re.DOTALL)
                if form_action and form_action.group(1):
                    raise KeycloakAuthenticationError(
                        error_message="Authentication failed, check your credentials. If you have activated 2-factor authentication, remember to enter the OTP code.",
                        response_code=resp.status_code,
                        response_body=resp.content,
                    )
            else:
                raise_error_from_response(resp, KeycloakAuthenticationError)

        # If Location header is not present raise exception.
        if "Location" not in resp.headers:
            raise KeycloakInvalidTokenError("Code not found")
        redirect = resp.headers["Location"]
        query = urllib.parse.urlparse(redirect).fragment
        redirect_params = urllib.parse.parse_qs(query)

        # If code is not in redirect_params or len redirect_params code is less than 1
        if "code" not in redirect_params or len(redirect_params["code"]) < 1:
            raise Exception()
        return redirect_params["code"][0]

    def _getCookieAndAction(self) -> tuple:
        """Get cookie and action from openid - connect."""
        form_action = None
        resp: requests.Response = self.session.get(
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
            timeout=60,
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
        """Refresh Token."""
        resp: requests.Response = self.session.post(
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
        """Get access and refresh tokens."""
        self._login()
        _data = {
            "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
            "client_id": CLIENT_ID,  # ecotrend
            "redirect_uri": REDIRECT_URI,
            "code": self.auth_code,
            "code_verifier": self.code_verifier,
        }
        if self.totp:
            print(f"otp: {self.totp}")
            _data["totp"] = self.totp
        resp: requests.Response = self.session.post(
            url=PROVIDER_URL + "token",
            data=_data,
            timeout=60,
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
        resp: requests.Response = self.session.get(url=PROVIDER_URL + "userinfo", headers=header)
        return resp.json()

    def logout(self, token) -> dict | Any | bytes | dict[str, str]:
        resp: requests.Response = self.session.post(
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
