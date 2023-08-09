"""Login helper file."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import json
import os
import re
import urllib.parse

import httpx


class LoginHelper:
    """Login helper for keycloak."""

    provider = "https://keycloak.ista.com/realms/eed-prod"
    redirect_uri = "https://ecotrend.ista.de/login-redirect"
    client_id = "ecotrend"
    response_mode = "fragment"
    response_type = "code"
    scope = "openid"
    code_challenge_method = "S256"
    grant_type_authorization_code = "authorization_code"
    grant_type_refresh_token = "refresh_token"
    code_verifier = None
    code_challenge = None

    username = None
    password = None
    cookie = None
    auth_code = None
    form_action = None

    def __init__(self, username, password) -> None:
        """Initializes the object with username and password."""
        self.username = username
        self.password = password

        self.code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8")
        self.code_verifier = re.sub("[^a-zA-Z0-9]+", "", self.code_verifier)

        self.code_challenge = hashlib.sha256(self.code_verifier.encode("utf-8")).digest()
        self.code_challenge = base64.urlsafe_b64encode(self.code_challenge).decode("utf-8")
        self.code_challenge = self.code_challenge.replace("=", "")

    async def _login(self) -> None:
        """Logs in to ista."""
        self.cookie, self.form_action = await self._getCookieAndAction()
        self.auth_code = await self._getAuthCode()

    async def refreshToken(self, refresh_token):
        """Refresh Token."""
        URL_TOKEN = self.provider + "/protocol/openid-connect/token"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url=URL_TOKEN,
                data={
                    "grant_type": self.grant_type_refresh_token,
                    "client_id": self.client_id,  # ecotrend
                    "refresh_token": refresh_token,
                },
                timeout=10,
                follow_redirects=False,
            )
            # If the response code is not 200 raise an exception.
            if resp.status_code != 200:
                raise Exception()
            result = resp.json()

            return result["access_token"], result["expires_in"], result["refresh_token"]

    async def getToken(self, refresh=False):
        """Get access and refresh tokens."""
        await self._login()
        URL_TOKEN = self.provider + "/protocol/openid-connect/token"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url=URL_TOKEN,
                data={
                    "grant_type": self.grant_type_refresh_token if refresh else self.grant_type_authorization_code,
                    "client_id": self.client_id,  # ecotrend
                    "redirect_uri": self.redirect_uri,
                    "code": self.auth_code,
                    "code_verifier": self.code_verifier,
                },
                timeout=10,
                follow_redirects=False,
            )
            # If the response code is not 200 raise an exception.
            if resp.status_code != 200:
                raise Exception()
            result = resp.json()

            return result["access_token"], result["expires_in"], result["refresh_token"]

    async def _getAuthCode(self) -> str:
        """Get auth code from ista."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url=self.form_action,
                data={"username": self.username, "password": self.password},
                headers={"Cookie": self.cookie},
                timeout=10,
                follow_redirects=False,
            )
            # If the response code is 302
            if resp.status_code != 302:
                raise Exception()

            # If Location header is not present raise exception.
            if "Location" not in resp.headers:
                raise Exception()
            redirect = resp.headers["Location"]
            query = urllib.parse.urlparse(redirect).fragment
            redirect_params = urllib.parse.parse_qs(query)
            # If code is not in redirect_params or len redirect_params code is less than 1
            if "code" not in redirect_params or len(redirect_params["code"]) < 1:
                raise Exception()
            return redirect_params["code"][0]

    async def _getCookieAndAction(self) -> tuple:
        """Get cookie and action from openid - connect."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                url=self.provider + "/protocol/openid-connect/auth",
                params={
                    "response_mode": self.response_mode,  # fragment
                    "response_type": self.response_type,  # code
                    "client_id": self.client_id,
                    "scope": self.scope,
                    "redirect_uri": self.redirect_uri,
                    "code_challenge": self.code_challenge,
                    "code_challenge_method": self.code_challenge_method,
                },
                timeout=10,
                follow_redirects=False,
            )
            # If the response code is not 200 raise an exception.
            if resp.status_code != 200:
                raise Exception()
            cookie = resp.headers["Set-Cookie"]
            cookie = "; ".join(c.split(";")[0] for c in cookie.split(", "))
            form_action = html.unescape(re.search(r'<form\s+.*?\s+action="(.*?)"', resp.text, re.DOTALL).group(1))
            return cookie, form_action


def _b64_decode(data):
    """Decode base64 data and pad with spaces to 4 - byte boundary."""
    data += "=" * (4 - len(data) % 4)
    return base64.b64decode(data).decode("utf-8")


def jwt_payload_decode(jwt):
    """Decodes and returns the JSON Web Token."""
    _, payload, _ = jwt.split(".")
    return json.dumps(json.loads(_b64_decode(payload)), indent=4)


# This is the main module.
async def main():
    """Login and get a JWT token from the loginhelper."""
    username = "demo@ista.de"
    password = "Ausprobieren!"
    loginhelper = LoginHelper(username=username, password=password)
    access_token, refresh_expires_in, refresh_token = await loginhelper.getToken()
    print(jwt_payload_decode(access_token))
    print(jwt_payload_decode(refresh_token))
    access_token, refresh_expires_in, refresh_token = await loginhelper.refreshToken(refresh_token=refresh_token)
    print(jwt_payload_decode(access_token))
    print(jwt_payload_decode(refresh_token))


# run main function if __main__ is not defined
if __name__ == "__main__":
    asyncio.run(main())
