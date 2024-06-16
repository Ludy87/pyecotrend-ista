"""Types for PyEcotrendIsta."""

from typing import TypedDict


class GetTokenResponse(TypedDict):
    """A TypedDict for the response returned by the getToken function.

    Attributes
    ----------
    access_token : str
        The access token issued by the authentication provider.
    expires_in : int
        The number of seconds until the access token expires.
    refresh_token : str
        The refresh token that can be used to obtain new access tokens.
    refresh_expires_in : int
        The number of seconds until the refresh token expires.

    """

    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
