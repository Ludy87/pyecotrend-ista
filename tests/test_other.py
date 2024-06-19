"""Tests for utility methods."""


from typing import cast

import pytest

from pyecotrend_ista import PyEcotrendIsta
from pyecotrend_ista.const import VERSION
from pyecotrend_ista.types import AccountResponse


def test_get_uuids(ista_client: PyEcotrendIsta) -> None:
    """Test `get_uuids` method."""


    ista_client._account = cast(AccountResponse , { # pylint: disable=W0212
        "residentAndConsumptionUuidsMap": {
            "17c4dff7-799f-4f16-badc-a9b3607a9383": "7a226e08-2a90-4db9-ae9b-8148901c6ec2",
            "756a591c-185b-4441-a21a-46d4b94df4ad": "df3e8a64-a622-4ffb-97c5-b892a2cf331d",
        }
    })
    assert ista_client.get_uuids() == ["7a226e08-2a90-4db9-ae9b-8148901c6ec2", "df3e8a64-a622-4ffb-97c5-b892a2cf331d"]



def test_get_version(ista_client: PyEcotrendIsta) -> None:
    """Test `get_version` method."""

    assert ista_client.get_version() == VERSION

def test_get_user_agent(ista_client: PyEcotrendIsta) -> None:
    """Test `get_user_agent` method."""

    assert ista_client.get_user_agent() == (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67"
        " Safari/537.36"
    )
@pytest.mark.xfail
@pytest.mark.usefixtures("mock_requests_login")
def test_get_support_code(ista_client: PyEcotrendIsta) -> None:
    """Test `get_support_code` method."""

    assert ista_client.get_support_code() == "XXXXXXXXX"


@pytest.mark.parametrize(("access_token", "expected_result"), [("ACCESS_TOKEN", True), (None, False)])
def test_is_connected(ista_client: PyEcotrendIsta, access_token: str | None, expected_result: bool) -> None:
    """Test `_is_connected` method."""

    ista_client._access_token = access_token  # pylint: disable=W0212
    assert ista_client._is_connected() is expected_result  # pylint: disable=W0212


@pytest.mark.parametrize(("deprecated_method"), ["getVersion", "getUUIDs", "getSupportCode"])
def test_method_deprecations(ista_client: PyEcotrendIsta, deprecated_method: str) -> None:
    """Test warnings for deprecated methods."""
    with pytest.warns(DeprecationWarning):
        try:
            getattr(ista_client, deprecated_method)()
        except Exception:  # pylint: disable=W0718
            pass


@pytest.mark.parametrize(("param"), ["debug", "forceLogin"])
def test_login_deprecated_parameters(ista_client: PyEcotrendIsta, param: str) -> None:
    """Test warnings for deprecated methods."""
    with pytest.warns(DeprecationWarning):
        try:
            ista_client.login(**{param: True})
        except Exception:  # pylint: disable=W0718
            pass

@pytest.mark.parametrize(("param"), ["logger", "hass_dir"])
def test_init_deprecated_parameters(param: str) -> None:
    """Test warnings for deprecated methods."""
    with pytest.warns(DeprecationWarning):
        PyEcotrendIsta(email="", password="", **{param: True}) # type: ignore
