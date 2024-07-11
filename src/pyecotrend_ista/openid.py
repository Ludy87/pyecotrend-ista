"""Authentication module for PyEcotrendIsta."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import html
from http import HTTPStatus
import logging
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag
import httpx
from httpx import AsyncHTTPTransport, Headers, HTTPStatusError

from .exception_classes import KeycloakGetError

_LOGGER = logging.getLogger(__name__)

API_URL = "https://api.prod.eed.ista.com/"

class OpenIDAuthenticator:
    """openID Authenticator."""

    email: str | None = None
    password: str | None = None
    is_demo_login: bool = False

    def __init__(
        self,
        provider_url: str,
        client_id: str,
        redirect_uri: str,
        response_mode: str ="fragment",
        response_type: str ="code",
        scope: str ="openid",
        timeout: int = 10,
        retries: int = 3,
        client: httpx.AsyncClient | None = None,
        logger: logging.Logger | None = None,
        otp_callback: Callable[[], str] | None = None,
        max_login_attempts: int = 3,
    ):
        """Initialize the OpenIDAuthenticator."""

        self.provider_url = provider_url
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.response_mode = response_mode
        self.response_type = response_type
        self.scope = scope
        self.timeout = timeout
        self.retries = retries
        self._otp_callback = otp_callback
        self.max_login_attempts = max_login_attempts

        self._logger = logger or _LOGGER
        self._access_token: str | None = None
        self._access_token_expires_at: float | None = None
        self._refresh_token: str | None = None
        self._refresh_token_expires_at = None


        default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.37"
            ),
        }

        if client:
            self.client = client
            self.client.headers = Headers(default_headers)
        else:
            transport = AsyncHTTPTransport(retries=self.retries)
            self.client = httpx.AsyncClient(headers=default_headers, transport=transport)


    @property
    def access_token(self):
        """Get the access token.

        If the access token has expired, it will be set to None.

        Returns
        -------
        str or None
            The current access token if it has not expired, otherwise None.
        """

        if self._access_token_expires_at and time.time() > self._access_token_expires_at:
            self._access_token = None
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        """Set the access token.

        Parameters
        ----------
        value : str
            The new access token.
        """

        self._access_token = value

    @property
    def refresh_token(self):
        """Get the refresh token.

        If the refresh token has expired, it will be set to None.

        Returns
        -------
        str or None
            The current refresh token if it has not expired, otherwise None.
        """

        if self._refresh_token_expires_at and time.time() > self._refresh_token_expires_at:
            self._refresh_token = None
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value):
        """Set the refresh token.

        Parameters
        ----------
        value : str
            The new refresh token.
        """

        self._refresh_token = value


    async def login(
        self,
        email: str,
        password: str,
        otp: str | None = None,
        otp_callback: Callable[[], str] | None = None,
    ) -> bool:
        """Login with email, password, and optional OTP code.

        Parameters
        ----------
        email : str
            The user's email or username.
        password : str
            The user's password.
        otp : str, optional
            The one-time password (OTP) code, if required.
        otp_callback : callable, optional
            A callback function to request a new OTP if needed.

        Returns
        -------
        str
            The final redirect URL after successful login.

        Raises
        ------
        KeycloakGetError
            If any step of the login process fails.
        """
        self.email = email
        self.password = password
        self._otp_callback = otp_callback

        try:
            action_url = await self.initiate_auth_request()
            redirect_url = await self.submit_login(email, password, action_url)


            if not redirect_url:
                raise KeycloakGetError("Login failed: Redirect URL is None")


            if not redirect_url.startswith(self.redirect_uri):
                if otp is not None:
                    redirect_url = await self.submit_otp(redirect_url, otp)
                elif otp_callback and (otp := otp_callback()):
                    redirect_url = await self.submit_otp(redirect_url, otp)
                else:
                    raise KeycloakGetError("OTP code is required but not provided.")

            authorization_code = self.extract_authorization_code(redirect_url)
            await self.exchange_code_for_tokens(authorization_code)

        except HTTPStatusError as e:
            raise KeycloakGetError(f"Login failed: {e}") from e

        return True

    async def re_authenticate(self):
        """Re-authenticate if the refresh token has expired."""

        if self.email and self.password and self._otp_callback:
            for login_attempts in range(self.max_login_attempts):
                try:
                    await self.login(email=self.email, password=self.password, otp_callback=self._otp_callback)

                except KeycloakGetError as e:
                    self._logger.debug(f"Re-authentication attempt {login_attempts + 1} failed: {e}")
                    login_attempts += 1
                else:
                    return
            raise KeycloakGetError("Re-authentication failed after maximum attempts.")
        if self.is_demo_login:
            await self.get_demo_user_tokens()
            return
        raise KeycloakGetError("Re-authentication failed, no login credentials available or otp provider available.")

    async def exchange_code_for_tokens(self, authorization_code: str):
        """Exchange authorization code for tokens."""
        try:
            token_response = await self._request_tokens(authorization_code=authorization_code, grant_type="authorization_code")
            self._update_tokens(token_response)

        except httpx.HTTPStatusError as e:
            raise KeycloakGetError(f"Failed to exchange code for tokens: {e}") from e



    async def initiate_auth_request(self) -> str:
        """Initiate the authentication request for OpenID Connect and retrieve the action URL.

        Returns
        -------
        str
            The action URL extracted from the HTML form.

        Raises
        ------
        KeycloakGetError
            If the GET request to the OpenID Connect provider returns a non-200 status code.
        HTTPStatusError
            If there is an issue with the network request.
        """

        try:
            response = await self._send_request()
            self._raise_error_if_not_ok(response)
            return  self._extract_action_url(response.text)
        except HTTPStatusError as e:
            raise KeycloakGetError(f"Failed to retrieve authentication page: {e}") from e


    async def submit_login(self, email: str, password: str, action_url: str) -> str | None:
        """Submit email and password for the authentication request.

        Parameters
        ----------
        email : str
            The user's email or username.
        password : str
            The user's password.
        action_url : str
            The action URL to submit the login credentials.

        Returns
        -------
        str
            The final redirect URL after successful login.

        Raises
        ------
        KeycloakGetError
            If the POST request to submit login credentials returns a non-200 status code.
        """
        try:
            response = await self.client.post(
                url=action_url,
                data={"username": email, "password": password, "credentialId": "", "login": "Login"},
                timeout=self.timeout,
                follow_redirects=False,
            )
            if response.status_code == HTTPStatus.FOUND:
                return response.headers.get("Location")
            if response.status_code == HTTPStatus.OK:
                return self._extract_action_url(response.text)

            self._raise_error_if_not_ok(response)

        except HTTPStatusError as e:
            raise KeycloakGetError(f"Failed to submit login credentials: {e}") from e

        return None

    async def submit_otp(self, action_url: str, otp: str) -> str:
        """Submit the OTP for the authentication request.

        Parameters
        ----------
        action_url : str
            The action URL to submit the OTP.
        otp : str
            The one-time password.

        Returns
        -------
        str
            The final redirect URL after OTP submission.

        Raises
        ------
        KeycloakGetError
            If the POST request to submit the OTP returns a non-200 status code.
        """

        try:
            response = await self.client.post(
                url=action_url,
                data={"otp": otp},
                timeout=self.timeout,
                follow_redirects=False,
            )
            if response.status_code == 302 or response.headers.get("Location"):
                return response.headers.get("Location")

            self._raise_error_if_not_ok(response)

            raise KeycloakGetError(f"OTP was invalid [{response.status_code}].")

        except HTTPStatusError as e:
            raise KeycloakGetError(f"Failed to submit OTP: {e}") from e


    async def _send_request(self) -> httpx.Response:
        """Send the authentication request to the OpenID Connect provider.

        Returns
        -------
        httpx.Response
            The response object from the GET request.
        """

        response = await self.client.get(
            url=f"{self.provider_url}auth",
            params={
                "response_mode": self.response_mode,
                "response_type": self.response_type,
                "client_id": self.client_id,
                "scope": self.scope,
                "redirect_uri": self.redirect_uri,
            },
            timeout=self.timeout,
            follow_redirects=False,
        )

        response.raise_for_status()
        return response

    def _extract_action_url(self, html_content: str) -> str:
        """Extract the action URL from the HTML content.

        Parameters
        ----------
        html_content : str
            The HTML content of the response.

        Returns
        -------
        str
            The extracted action URL.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        form = soup.find("form")
        if isinstance(form, Tag) and form.has_attr("action"):
            return html.unescape(form["action"])
        return ""

    def _raise_error_if_not_ok(self, response: httpx.Response):
        """Raise an error if the response status code is not 200.

        Parameters
        ----------
        response : httpx.Response
            The response object to check.

        Raises
        ------
        KeycloakGetError
            If the response status code is not 200.
        """
        if response.status_code != 200:
            raise KeycloakGetError(f"Received non-200 status code: {response.status_code}")

    def extract_authorization_code(self, redirect_url: str) -> str:
        """Extract the authorization code from the redirect URL.

        Parameters
        ----------
        redirect_url : str
            The redirect URL containing the authorization code in the fragment.

        Returns
        -------
        str
            The authorization code.

        Raises
        ------
        KeycloakGetError
            If the authorization code is not found in the redirect URL fragment.
        """
        parsed_url = urlparse(redirect_url)
        fragment = parsed_url.fragment
        query_params = parse_qs(fragment)
        authorization_code = query_params.get("code")
        if not authorization_code:
            raise KeycloakGetError("Authorization code not found in redirect URL fragment.")
        return authorization_code[0]

    async def _request_tokens(
        self,
        authorization_code=None,
        refresh_token=None,
        grant_type="authorization_code",
    ):
        """Request tokens from token endpoint."""

        data = {
            "client_id": self.client_id,
        }

        if grant_type == "authorization_code":
            data.update(
                **{
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": self.redirect_uri,
                }
            )
        elif grant_type == "refresh_token":
            data.update(
                **{
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }
            )

        try:
            response = await self.client.post(
                url=f"{self.provider_url}token",
                data=data,
                timeout=self.timeout,
                follow_redirects=False,
            )

            response.raise_for_status()

        except httpx.HTTPStatusError as e:

            raise KeycloakGetError(
                error_message=e.response.json()["error_description"],
                response_code=e.response.status_code,
            ) from e
        return response.json()

    def _update_tokens(self, tokens: dict[str, Any]):
        """Update tokens and expiration times."""
        if self.is_demo_login:
            self.access_token = tokens["accessToken"]
            self._access_token_expires_at = time.time() + tokens["accessTokenExpiresIn"]
            self.refresh_token = tokens["refreshToken"]
            self._refresh_token_expires_at = time.time() + tokens["refreshTokenExpiresIn"]
        else:
            self.access_token = tokens["access_token"]
            self._access_token_expires_at = time.time() + tokens["expires_in"]
            self.refresh_token = tokens["refresh_token"]
            self._refresh_token_expires_at = time.time() + tokens["refresh_expires_in"]

    def _token_expired(self):
        """Check if access token is expired."""
        return self._access_token_expires_at is None or time.time() > self._access_token_expires_at

    def _refresh_token_expired(self):
        """Check if refresh token is expired."""
        return self._refresh_token_expires_at is None or time.time() > self._refresh_token_expires_at

    async def refresh_access_token(self):
        """Refresh access token using refresh token."""


        try:
            if self.is_demo_login:
                token = await self._demo_user_refresh_token(
                    refresh_token=self.refresh_token
                )
            else:
                token = await self._request_tokens(
                    refresh_token=self.refresh_token,
                    grant_type="refresh_token",
                )
        except HTTPStatusError as e:
            if e.response.status_code is HTTPStatus.UNAUTHORIZED:
                self.refresh_token = None
                self._refresh_token_expires_at = None
            raise KeycloakGetError(f"Failed to refresh access token: {e}", response_code=e.response.status_code) from e

        self._update_tokens(token)


    def _invalidate_access_token(self):
        """Invalidate access token."""
        self.access_token = None
        self._access_token_expires_at = None

    async def ensure_valid_token(self):
        """Ensure that the access token is valid and refresh it if necessary."""
        try:
            if not self.access_token or self._token_expired():
                await self.refresh_access_token()
        except KeycloakGetError as e:
            if e.response_code is HTTPStatus.UNAUTHORIZED:
                self._logger.warning("Refresh token invalid, attempting re-authentication.")
                await self.re_authenticate()
            else:
                raise

    async def get_demo_user_tokens(self):
        """Get tokens from the demo user token endpoint."""
        self.is_demo_login = True
        response = await self.client.get(f"{API_URL}demo-user-token")

        response.raise_for_status()

        self._update_tokens(response.json())

    async def _demo_user_refresh_token(self, refresh_token: str | None = None) -> dict[str, Any]:
        """."""
        json = {
            "refreshToken": refresh_token
        }
        response = await self.client.post(f"{API_URL}demo-user-refresh-token", json=json)

        return response.json()

    async def async_request(self, method, url, **kwargs):
        """Make an async HTTP request ensuring a valid access token."""
        await self.ensure_valid_token()

        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"Bearer {self.access_token}"
        kwargs['headers'] = headers

        response = None
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            if e.response.status_code is HTTPStatus.UNAUTHORIZED:
                self._logger.debug("Access token expired, attempting to refresh or re-authenticate.")
                self._invalidate_access_token()
                await self.ensure_valid_token()
                headers = kwargs.get('headers', {})
                headers['Authorization'] = f"Bearer {self.access_token}"
                kwargs['headers'] = headers

                try:
                    response = await self.client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
                except HTTPStatusError as exc:
                    if exc.response.status_code is HTTPStatus.UNAUTHORIZED:
                        self._logger.debug("Re-authentication failed, unauthorized access.")
                        raise KeycloakGetError(
                            "Unauthorized access, re-authentication failed.", response_code=exc.response.status_code
                        ) from exc
                    else:
                        raise
            else:
                raise

    async def async_get(self, url, **kwargs):
        """Make an async GET request ensuring a valid access token."""
        return await self.async_request('GET', url, **kwargs)

    async def async_post(self, url, **kwargs):
        """Make an async POST request ensuring a valid access token."""
        return await self.async_request('POST', url, **kwargs)

    def _run_async(self, coro):
        """Run an async coroutine in a synchronous context."""
        return asyncio.run(coro)

    def request(self, method, url, **kwargs):
        """Make a sync HTTP request ensuring a valid access token."""
        return self._run_async(self.async_request(method, url, **kwargs))

    def get(self, url, **kwargs):
        """Make a sync GET request ensuring a valid access token."""
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        """Make a sync POST request ensuring a valid access token."""
        return self.request('POST', url, **kwargs)
