"""Exception Class."""  # numpydoc ignore=ES01,EX01

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar
import warnings

T = TypeVar("T")


def deprecated(func: Callable[..., T], alias_func: str | None = None) -> Callable[..., T]:  # numpydoc ignore=ES01,PR01,PR02,PR04,PR10,EX01
    """
    Decorate a function as deprecated and emit a warning when called.

    Parameters
    ----------
    func: Callable[..., T])
        The function to be marked as deprecated.
    alias_func : str, optional
        The real function name to show as deprecated, in case the function was called
        through an alias.

    Returns
    -------
    Callable[..., T]
        A wrapper function that emits a deprecation warning when called.

    """

    def deprecated_func(*args, **kwargs):  # numpydoc ignore=ES01,SA01,EX01
        """
        Emit a deprecation warning and call the decorated function.

        Parameters
        ----------
        *args : tuple
            Positional arguments passed to the decorated function.
        **kwargs : dict
            Keyword arguments passed to the decorated function.

        Returns
        -------
        T
            The return value of the decorated function.
        """
        if alias_func:
            warning_message = (
                f"The `{alias_func}` function is deprecated and will be removed in a future release. "
                f"Use `{func.__name__}` instead."
            )
        else:
            warning_message = f"The `{func.__name__}` function is deprecated and will be removed in a future release."

        warnings.warn(warning_message, category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)

    return deprecated_func


class BaseError(Exception):  # numpydoc ignore=ES01,EX01
    """Base class for exceptions in this module.

    This is the base class for all custom exceptions in the module. It inherits
    from Python's built-in Exception class and can be used to catch errors specific
    to this module.
    """


class ServerError(BaseError):  # numpydoc ignore=ES01,EX01
    """Exception raised for server errors during requests.

    This exception is raised when a exception occurs during a request.
    It inherits from BaseError  and can be used to handle server-related
    issues specifically.
    """

    def __str__(self) -> str:
        """Return a string representation of the error.."""
        return "Server error occurred during the request"


class LoginError(BaseError):  # numpydoc ignore=ES01,EX01
    """Exception raised for login- and authentication related errors.

    This exception is raised when an authentication exception occurs during a request.
    It inherits from BaseError and is used specifically to handle issues related
    to authentication and login.
    """

    def __str__(self) -> str:
        """Return a string representation of an authentication error."""
        return "An authentication error occurred during the request"


class ParserError(ServerError):  # numpydoc ignore=ES01,EX01
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

# Source from
# https://github.com/marcospereirampj/python-keycloak/blob/c98189ca6951f12f1023ed3370c9aaa0d81e4aa4/src/keycloak/exceptions.py

# Keycloak custom exceptions module.


class KeycloakError(Exception):  # numpydoc ignore=ES01,EX01,PR01
    """Base class for custom Keycloak errors."""

    def __init__(self, error_message="", response_code=None, response_body=None):  # numpydoc ignore=ES01,EX01
        """Init method.

        Parameters
        ----------
        error_message : str, optional
            The error message (default is an empty string).
        response_code : int, optional
            The code of the response (default is None).
        response_body : bytes, optional
            Body of the response (default is None).
        """
        Exception.__init__(self, error_message)

        self.response_code = response_code
        self.response_body = response_body
        self.error_message = error_message

    def __str__(self):
        """Str method.

        Returns
        -------
        str
            String representation of the object.
        """
        if self.response_code is not None:
            return f"{self.response_code}: {self.error_message}"
        return f"{self.error_message}"


class KeycloakAuthenticationError(KeycloakError):  # numpydoc ignore=ES01,EX01
    """Keycloak authentication error exception."""


class KeycloakOperationError(KeycloakError):  # numpydoc ignore=ES01,EX01
    """Keycloak operation error exception."""


class KeycloakGetError(KeycloakOperationError):  # numpydoc ignore=ES01,EX01
    """Keycloak request get error exception."""


class KeycloakPostError(KeycloakOperationError):  # numpydoc ignore=ES01,EX01
    """Keycloak request post error exception."""


class KeycloakCodeNotFound(KeycloakOperationError):  # noqa: N818  numpydoc ignore=ES01,EX01
    """Keycloak Code not found exception."""


class KeycloakInvalidTokenError(KeycloakOperationError):  # numpydoc ignore=ES01,EX01
    """Keycloak invalid token exception."""
