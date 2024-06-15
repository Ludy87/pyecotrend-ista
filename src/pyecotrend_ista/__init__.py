"""pyecotrend ista."""

from .exception_classes import (
    Error,
    InternalServerError,
    KeycloakAuthenticationError,
    KeycloakError,
    KeycloakGetError,
    KeycloakInvalidTokenError,
    KeycloakOperationError,
    KeycloakPostError,
    LoginError,
    ServerError,
)

__all__ = [
    "Error",
    "InternalServerError",
    "KeycloakAuthenticationError",
    "KeycloakError",
    "KeycloakGetError",
    "KeycloakInvalidTokenError",
    "KeycloakOperationError",
    "KeycloakPostError",
    "LoginError",
    "ServerError",
]
