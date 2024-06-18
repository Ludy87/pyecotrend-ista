"""Exception Class."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar
import warnings

T = TypeVar("T")


def deprecated(func: Callable[..., T], alias_func: str | None = None) -> Callable[..., T]:
    """Decorate a function as deprecated and emit a warning when called.

    Parameters
    ----------
    func: Callable[..., T])
        The function to be marked as deprecated.
    alias_func : str, optional
        The real function name to show as deprecated, in case the function was called through an alias.


    Returns
    -------
    Callable[..., T]
        A wrapper function that emits a deprecation warning when called.

    """

    def deprecated_func(*args, **kwargs):
        if alias_func:
            warning_message = f"The `{alias_func}` function is deprecated and will be removed in a future release. Use `{func.__name__}` instead."
        else:
            warning_message = f"The `{func.__name__}` function is deprecated and will be removed in a future release."

        warnings.warn(warning_message, category=DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)

    return deprecated_func


class BaseError(Exception):
    """
    Base class for exceptions in this module.

    This is the base class for all custom exceptions in the module. It inherits
    from Python's built-in Exception class and can be used to catch errors specific
    to this module.
    """

class ServerError(BaseError):
    """Create ServerError."""

    def __init__(self) -> None:
        """Initialize the object."""
        super().__init__()

    def __str__(self) -> str:
        """Returns a string representation of the error.."""
        return "Server error, go to: https://ecotrend.ista.de/error"



class LoginError(BaseError):
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


class KeycloakOperationError(KeycloakError):
    """Keycloak operation error exception."""


class KeycloakGetError(KeycloakOperationError):
    """Keycloak request get error exception."""


class KeycloakPostError(KeycloakOperationError):
    """Keycloak request post error exception."""


class KeycloakCodeNotFound(KeycloakOperationError):
    """Keycloak Code not found exception."""


class KeycloakInvalidTokenError(KeycloakOperationError):
    """Keycloak invalid token exception."""
