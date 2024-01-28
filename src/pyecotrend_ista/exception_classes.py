"""Exception Class."""

from __future__ import annotations

from typing import Any


class Error(Exception):
    """This is a class to catch exceptions that are thrown when trying to create a node."""


class ServerError(Error):
    """Create ServerError."""

    def __init__(self) -> None:
        """Initialize the object."""
        super().__init__()

    def __str__(self) -> str:
        """Returns a string representation of the error.."""
        return "Server error, go to: https://ecotrend.ista.de/error"


class InternalServerError(Error):
    """Create InternalServerError."""

    def __init__(self, msg) -> None:
        """Initialize the exception with a message."""
        super().__init__(msg)
        self.msg = msg

    def __str__(self) -> str:
        """Convert to string. This is useful for debugging."""
        return self.msg


class LoginError(Error):
    """Create LoginError."""

    def __init__(self, res: Any) -> None:
        """Initialize the object with the result of the call."""
        super().__init__(res)
        self.res = res

    def __str__(self) -> str:
        """String representation of LoginFail."""
        return f"Login fail, check your input! {self.res}"


# The MIT License (MIT)
#
# Copyright (C) 2017 Marcos Pereira <marcospereira.mpj@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Source from https://github.com/marcospereirampj/python-keycloak/blob/c98189ca6951f12f1023ed3370c9aaa0d81e4aa4/src/keycloak/exceptions.py

"""Keycloak custom exceptions module."""


class KeycloakError(Exception):
    """Base class for custom Keycloak errors.

    :param error_message: The error message
    :type error_message: str
    :param response_code: The response status code
    :type response_code: int
    """

    def __init__(self, error_message="", response_code=None, response_body=None):
        """Init method.

        :param error_message: The error message
        :type error_message: str
        :param response_code: The code of the response
        :type response_code: int
        :param response_body: Body of the response
        :type response_body: bytes
        """
        Exception.__init__(self, error_message)

        self.response_code = response_code
        self.response_body = response_body
        self.error_message = error_message

    def __str__(self):
        """Str method.

        :returns: String representation of the object
        :rtype: str
        """
        if self.response_code is not None:
            return f"{self.response_code}: {self.error_message}"
        else:
            return f"{self.error_message}"


class KeycloakAuthenticationError(KeycloakError):
    """Keycloak authentication error exception."""


class KeycloakConnectionError(KeycloakError):
    """Keycloak connection error exception."""


class KeycloakOperationError(KeycloakError):
    """Keycloak operation error exception."""


class KeycloakDeprecationError(KeycloakError):
    """Keycloak deprecation error exception."""


class KeycloakGetError(KeycloakOperationError):
    """Keycloak request get error exception."""


class KeycloakPostError(KeycloakOperationError):
    """Keycloak request post error exception."""


class KeycloakPutError(KeycloakOperationError):
    """Keycloak request put error exception."""


class KeycloakDeleteError(KeycloakOperationError):
    """Keycloak request delete error exception."""


class KeycloakSecretNotFound(KeycloakOperationError):
    """Keycloak secret not found exception."""


class KeycloakRPTNotFound(KeycloakOperationError):
    """Keycloak RPT not found exception."""


class KeycloakCodeNotFound(KeycloakOperationError):
    """Keycloak Code not found exception."""


class KeycloakAuthorizationConfigError(KeycloakOperationError):
    """Keycloak authorization config exception."""


class KeycloakInvalidTokenError(KeycloakOperationError):
    """Keycloak invalid token exception."""


class KeycloakPermissionFormatError(KeycloakOperationError):
    """Keycloak permission format exception."""


class PermissionDefinitionError(Exception):
    """Keycloak permission definition exception."""
