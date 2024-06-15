"""Types for PyEcotrendIsta."""

from typing import TypedDict


class GetTokenResponse(TypedDict):
    """A TypedDict for the response returned by the getToken function.

    Attributes
    ----------
    accessToken : str
        The access token issued by the authentication provider.
    accessTokenExpiresIn : int
        The number of seconds until the access token expires.
    refreshToken : str
        The refresh token that can be used to obtain new access tokens.
    refreshTokenExpiresIn : int
        The number of seconds until the refresh token expires.

    """

    accessToken: str
    accessTokenExpiresIn: int
    refreshToken: str
    refreshTokenExpiresIn: int
