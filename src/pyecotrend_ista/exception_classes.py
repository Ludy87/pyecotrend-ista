from __future__ import annotations

from typing import Any


class Error(Exception):
    pass


class ServerError(Error):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "Server error, go to: https://ecotrend.ista.de/error"


class InternalServerError(Error):
    def __init__(self, msg) -> None:
        super().__init__(msg)
        self.msg = msg

    def __str__(self) -> str:
        return self.res


class LoginError(Error):
    def __init__(self, res: Any) -> None:
        super().__init__(res)
        self.res = res

    def __str__(self) -> str:
        return "Login fail, check your input! {}".format(self.res)
