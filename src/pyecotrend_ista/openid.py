"""Authentication module for PyEcotrendIsta."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from enum import StrEnum
from http import HTTPStatus
from importlib.metadata import version
import logging
import platform
import time
from typing import Any, Self
from urllib.parse import parse_qs, urlparse

import httpx
from lxml.html import Element, document_fromstring

from .const import API_BASE_URL
from .exceptions import KeycloakError

_LOGGER = logging.getLogger(__name__)

class KeyCloakForm(StrEnum):
    """KeyCloak login flow steps."""

    LOGIN = "kc-form-login"
    OTP = "kc-otp-login-form"

class OpenIDAuthenticator:
    """openID Authenticator."""

    username: str | None = None
    password: str | None = None
    is_demo_login: bool = False
    _session: httpx.AsyncClient
    _close_session: bool = False
    _otp_callback: Callable[[], str] | None = None

    def __init__(
        self,
        provider_url: str,
        client_id: str,
        redirect_uri: str,
        post_logout_redirect_uri: str | None = None,
        response_mode: str ="fragment",
        response_type: str ="code",
        scope: str ="openid",
        timeout: int = 10,
        retries: int = 3,
        session: httpx.AsyncClient | None = None,
        logger: logging.Logger | None = None,
        max_login_attempts: int = 3,
    ):
        """Initialize the OpenIDAuthenticator."""

        self.provider_url = provider_url
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.post_logout_redirect_uri = post_logout_redirect_uri
        self.response_mode = response_mode
        self.response_type = response_type
        self.scope = scope
        self.timeout = timeout
        self.retries = retries
        self.max_login_attempts = max_login_attempts

        self._logger = logger or _LOGGER
        self._access_token: str | None = None
        self._access_token_expires_at: float | None = None
        self._refresh_token: str | None = None
        self._refresh_token_expires_at = None
        self._id_token: str | None = None

        default_headers = {
            "User-Agent": generate_user_agent(),
        }

        if session:
            self._session = session
            if str(self._session.headers.get("User-Agent")).startswith("python-httpx/"):
                self._session.headers.update(default_headers)
        else:
            transport = httpx.AsyncHTTPTransport(retries=self.retries)
            self._session = httpx.AsyncClient(headers=default_headers, transport=transport)
            self._close_session = True

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Async exit."""
        if self._close_session:
            await self._session.aclose()

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
        username: str,
        password: str,
        otp: str | None = None,
        otp_callback: Callable[[], str] | None = None,
    ) -> bool:
        """Login with username, password, and optional OTP code.

        Parameters
        ----------
        username : str
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
        KeycloakError
            If any step of the login process fails.
        """
        self.username = username
        self.password = password
        if otp_callback:
            self._otp_callback = otp_callback
        self.is_demo_login = False

        try:
            login_form = await self.initiate_auth_request()
            redirect_url_or_otp_form = await self.submit_login(username, password, login_form)

            if not isinstance(redirect_url_or_otp_form, str) and redirect_url_or_otp_form.attrib.get("id") == KeyCloakForm.OTP:
                if otp is not None:
                    redirect_url = await self.submit_otp(redirect_url_or_otp_form, otp)
                elif self._otp_callback and (otp := self._otp_callback()):
                    redirect_url = await self.submit_otp(redirect_url_or_otp_form, otp)
                else:
                    raise KeycloakError("OTP code is required but not provided.")

            authorization_code = self.extract_authorization_code(redirect_url)
            await self.exchange_code_for_tokens(authorization_code)

        except httpx.HTTPStatusError as e:
            raise KeycloakError(f"Login failed: {e}") from e

        return True

    async def logout(self) -> bool:
        """Logout and invalidate refresh token."""
        params: dict[str, str] = {
            "client_id": self.client_id,
        }


        if self.post_logout_redirect_uri:
            params.update(
                **{
                    "post_logout_redirect_uri": self.post_logout_redirect_uri,
                }
            )
        if self._id_token:
            params.update(
                **{
                    "id_token_hint": self._id_token,
                }
            )

        try:
            response = await self._session.get(
                url=f"{self.provider_url}logout",
                params=params,
                timeout=self.timeout,
                follow_redirects=False,
            )
            if response.status_code in (HTTPStatus.FOUND, HTTPStatus.OK):
                self._invalidate_access_token()
                self._invalidate_refresh_token()
                self._id_token = None
                return True

            self._raise_error_if_not_ok(response)

        except httpx.HTTPStatusError as e:
            raise KeycloakError(f"Failed to logout: {e}") from e

        return False

    async def re_authenticate(self):
        """Re-authenticate if the refresh token has expired."""

        if self.username and self.password:
            for login_attempts in range(self.max_login_attempts):
                try:
                    await self.login(username=self.username, password=self.password)

                except KeycloakError as e:
                    self._logger.debug(f"Re-authentication attempt {login_attempts + 1} failed: {e}")
                    login_attempts += 1
                    await asyncio.sleep(1)
                else:
                    return
            raise KeycloakError("Re-authentication failed after maximum attempts.")
        if self.is_demo_login:
            await self.demo_login()
            return
        raise KeycloakError("Re-authentication failed, no login credentials available or otp provider available.")

    async def exchange_code_for_tokens(self, authorization_code: str):
        """Exchange authorization code for tokens."""
        try:
            token_response = await self._request_tokens(authorization_code=authorization_code, grant_type="authorization_code")
            self._update_tokens(token_response)

        except httpx.HTTPStatusError as e:
            raise KeycloakError(f"Failed to exchange code for tokens: {e}") from e



    async def initiate_auth_request(self) -> Element:
        """Initiate the authentication request for OpenID Connect and retrieve the action URL.

        Returns
        -------
        tuple[str, str]
            The action URL and step id extracted from the HTML form.

        Raises
        ------
        KeycloakError
            If the GET request to the OpenID Connect provider returns a non-200 status code.
        """

        try:
            response = await self._send_request()
            return self._extract_form(response.text,  KeyCloakForm.LOGIN)
        except httpx.HTTPStatusError as e:
            raise KeycloakError(f"Failed to retrieve authentication page: {e}") from e


    async def submit_login(self, username: str, password: str, login_form: Element) -> Element:
        """Submit username and password for the authentication request.

        Parameters
        ----------
        username : str
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
        KeycloakError
            If the POST request to submit login credentials returns a non-200 status code.
        """

        if "username" in  login_form.fields:
            login_form.fields["username"] = username
        if "password" in  login_form.fields:
            login_form.fields["password"] = password

        try:
            response = await self._session.post(
                url=login_form.action,
                data=login_form.fields,
                timeout=self.timeout,
                follow_redirects=False,
            )
            if response.status_code == HTTPStatus.FOUND and response.headers.get("Location"):
                return response.headers["Location"], ""
            if response.status_code == HTTPStatus.OK:
                next_form = self._extract_form(response.text, login_form)
                # we received a request to enter an OTP code
                if next_form.attrib.get("id") == KeyCloakForm.OTP:
                    return next_form
                # we received again the same login page, login credentials are wrong
                if "username" in next_form.fields:
                    raise KeycloakError("Failed to login, please verify your login credentials")

                # we received again the login page, but it only has a password field
                # we have a 2-step Keycloak login flow. We submit now the password
                if "password" in next_form.fields:
                    await self.submit_login(username, password, next_form)

            self._raise_error_if_not_ok(response)

        except httpx.HTTPStatusError as e:
            raise KeycloakError(f"Failed to submit login credentials: {e}") from e

        return "", ""

    async def submit_otp(self, otp_form: Element, otp: str, otp_device: str | None = None) -> str:
        """Submit the OTP for the authentication request.

        Parameters
        ----------
        action_url : str
            The action URL to submit the OTP.
        otp : str
            The one-time password.
        otp_device : str
            uuid of the authenticator device to select if more
            than one is registered in the users' account

        Returns
        -------
        str
            The final redirect URL after OTP submission.

        Raises
        ------
        KeycloakError
            If the POST request to submit the OTP returns a non-200 status code.
        """
        otp_form.fields["otp"] = otp
        if "selectedCredentialId" in otp_form.fields:
            for radio in otp_form.inputs["selectedCredentialId"]:
                radio.checked = bool(radio.attrib["value"] == otp_device)

        try:
            response = await self._session.post(
                url=otp_form.action,
                data=otp_form.fields,
                timeout=self.timeout,
                follow_redirects=False,
            )
            if response.status_code == HTTPStatus.FOUND and response.headers.get("Location"):
                return response.headers["Location"]

            self._raise_error_if_not_ok(response)

            raise KeycloakError(f"OTP was invalid [{response.status_code}].")

        except httpx.HTTPStatusError as e:
            raise KeycloakError(f"Failed to submit OTP: {e}") from e


    async def _send_request(self) -> httpx.Response:
        """Send the authentication request to the OpenID Connect provider.

        Returns
        -------
        httpx.Response
            The response object from the GET request.
        """

        response = await self._session.get(
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

    def _extract_form(self, html_content: str, form_id:  KeyCloakForm) -> Element:
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
        # soup = BeautifulSoup(html_content, "html.parser")
        try:
            page: Element = document_fromstring(html_content)
            return next(form for form in page.forms if form.attrib.get("id") in KeyCloakForm)
        except StopIteration as e:
            raise KeycloakError(f"Failed to extract form {form_id.name} from page {e}") from e

    def _raise_error_if_not_ok(self, response: httpx.Response):
        """Raise an error if the response status code is not 200.

        Parameters
        ----------
        response : httpx.Response
            The response object to check.

        Raises
        ------
        KeycloakError
            If the response status code is not 200.
        """
        if response.status_code != HTTPStatus.OK:
            raise KeycloakError(f"Received non-200 status code: {response.status_code}")

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
        KeycloakError
            If the authorization code is not found in the redirect URL fragment.
        """
        parsed_url = urlparse(redirect_url)
        fragment = parsed_url.fragment
        query_params = parse_qs(fragment)
        authorization_code = query_params.get("code")
        if not authorization_code:
            raise KeycloakError("Authorization code not found in redirect URL fragment.")
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
            response = await self._session.post(
                url=f"{self.provider_url}token",
                data=data,
                timeout=self.timeout,
                follow_redirects=False,
            )

            response.raise_for_status()

        except httpx.HTTPStatusError as e:

            raise KeycloakError(
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
            self._id_token = None
        else:
            self.access_token = tokens["access_token"]
            self._access_token_expires_at = time.time() + tokens["expires_in"]
            self.refresh_token = tokens["refresh_token"]
            self._refresh_token_expires_at = time.time() + tokens["refresh_expires_in"]
            self._id_token = tokens["id_token"]

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
        except httpx.HTTPStatusError as e:
            if e.response.status_code is HTTPStatus.UNAUTHORIZED:
                self.refresh_token = None
                self._refresh_token_expires_at = None
            raise KeycloakError(f"Failed to refresh access token: {e}", response_code=e.response.status_code) from e

        self._update_tokens(token)


    def _invalidate_access_token(self):
        """Invalidate access token."""
        self.access_token = None
        self._access_token_expires_at = None

    def _invalidate_refresh_token(self):
        """Invalidate refresh token."""
        self.refresh_token = None
        self._refresh_token_expires_at = None

    async def ensure_valid_token(self):
        """Ensure that the access token is valid and refresh it if necessary."""
        try:
            if not self.access_token or self._token_expired():
                await self.refresh_access_token()
        except KeycloakError as e:
            if e.response_code is HTTPStatus.UNAUTHORIZED:
                self._logger.warning("Refresh token invalid, attempting re-authentication.")
                await self.re_authenticate()
            else:
                raise

    async def demo_login(self):
        """Get tokens from the demo user token endpoint."""
        self.is_demo_login = True
        response = await self._session.get(f"{API_BASE_URL}demo-user-token")

        response.raise_for_status()

        self._update_tokens(response.json())

    async def _demo_user_refresh_token(self, refresh_token: str | None = None) -> dict[str, Any]:
        """."""
        json = {
            "refreshToken": refresh_token
        }
        response = await self._session.post(f"{API_BASE_URL}demo-user-refresh-token", json=json)
        response.raise_for_status()

        return response.json()

    async def async_request(self, method, url, **kwargs):
        """Make an async HTTP request ensuring a valid access token."""
        await self.ensure_valid_token()

        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"Bearer {self.access_token}"
        kwargs['headers'] = headers

        response = None
        try:
            response = await self._session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code is HTTPStatus.UNAUTHORIZED:
                self._logger.debug("Access token expired, attempting to refresh or re-authenticate.")
                self._invalidate_access_token()
                await self.ensure_valid_token()
                headers = kwargs.get('headers', {})
                headers['Authorization'] = f"Bearer {self.access_token}"
                kwargs['headers'] = headers

                try:
                    response = await self._session.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code is HTTPStatus.UNAUTHORIZED:
                        self._logger.debug("Re-authentication failed, unauthorized access.")
                        raise KeycloakError(
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
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        """Make a sync POST request ensuring a valid access token."""
        return self.request("POST", url, **kwargs)


def generate_user_agent():
    """Generate the custom User-Agent string including OS information."""  #
    os_name = platform.system()
    os_version = platform.version()
    os_release = platform.release()
    arch, _ = platform.architecture()
    os_info = f"{os_name} {os_release} ({os_version}); {arch}"

    user_agent = (
        f"pyecotrend_ista/{version("pyecotrend_ista")} ({os_info}) "
        f"httpx/{httpx.__version__} Python/{platform.python_version()} "
        " +https://github.com/Ludy87/pyecotrend-ista)"
    )
    return user_agent
