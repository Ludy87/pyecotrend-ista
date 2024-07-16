"""pyecotrend ista."""

from importlib.metadata import PackageNotFoundError, version

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

try:
    __version__ = version(__package__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

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
