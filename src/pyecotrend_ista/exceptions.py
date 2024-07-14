"""Exception Class."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")

class BaseError(Exception):
    """
    Base class for exceptions in this module.

    This is the base class for all custom exceptions in the module. It inherits
    from Python's built-in Exception class and can be used to catch errors specific
    to this module.
    """

class ServerError(BaseError):
    """Exception raised for server errors during requests.

    This exception is raised when a exception occurs during a request.
    It inherits from BaseError  and can be used to handle server-related
    issues specifically.
    """

    def __str__(self) -> str:
        """Return a string representation of the error.."""
        return "Server error occurred during the request"


class LoginError(BaseError):
    """Exception raised for login- and authentication related errors.

    This exception is raised when an authentication exception occurs during a request.
    It inherits from BaseError and is used specifically to handle issues related
    to authentication and login.
    """

    def __str__(self) -> str:
        """Return a string representation of an authentication error."""
        return "An authentication error occurred during the request"

class ParserError(ServerError):
    """Exception raised for errors encountered during parsing.

    This exception is raised when an error occurs during the parsing process
    of the request response. It inherits from BaseError and can be used
    to handle issues specifically related to parsing.
    """

    def __str__(self) -> str:
        """Return a string representation of parser error."""
        return "Error occurred during parsing of the request response"


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

# Keycloak custom exceptions module.


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


class KeycloakOperationError(KeycloakError):
    """Keycloak operation error exception."""


class KeycloakGetError(KeycloakOperationError):
    """Keycloak request get error exception."""


class KeycloakPostError(KeycloakOperationError):
    """Keycloak request post error exception."""


class KeycloakCodeNotFound(KeycloakOperationError):  # noqa: N818
    """Keycloak Code not found exception."""


class KeycloakInvalidTokenError(KeycloakOperationError):
    """Keycloak invalid token exception."""
