"""pyecotrend ista."""

from .const import VERSION
from .exceptions import (
    KeycloakAuthenticationError,
    KeycloakError,
    KeycloakGetError,
    KeycloakInvalidTokenError,
    KeycloakOperationError,
    KeycloakPostError,
    LoginError,
    ParserError,
    ServerError,
)
from .pyecotrend_ista import PyEcotrendIsta
from .types import ConsumptionsResponse

__all__ = [
    "ConsumptionsResponse",
    "KeycloakAuthenticationError",
    "KeycloakError",
    "KeycloakGetError",
    "KeycloakInvalidTokenError",
    "KeycloakOperationError",
    "KeycloakPostError",
    "LoginError",
    "ParserError",
    "PyEcotrendIsta",
    "ServerError",
]

__version__ = VERSION
