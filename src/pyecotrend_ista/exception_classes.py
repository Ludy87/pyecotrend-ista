"""Exception Class."""
from __future__ import annotations

from typing import Any


class Error(Exception):
    """This is a class to catch exceptions that are thrown when trying to create a node."""

    pass


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
        return self.res


class LoginError(Error):
    """Create LoginError."""

    def __init__(self, res: Any) -> None:
        """Initialize the object with the result of the call."""
        super().__init__(res)
        self.res = res

    def __str__(self) -> str:
        """String representation of LoginFail."""
        return f"Login fail, check your input! {self.res}"
