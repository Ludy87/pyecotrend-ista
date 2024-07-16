"""Tests for utility methods."""


from typing import cast

import pytest
from syrupy.assertion import SnapshotAssertion

from pyecotrend_ista import PyEcotrendIsta
from pyecotrend_ista.exceptions import LoginError
from pyecotrend_ista.types import AccountResponse


def test_get_uuids(ista_client: PyEcotrendIsta) -> None:
    """Test `get_uuids` method."""

    ista_client._account = cast( # pylint: disable=W0212
        AccountResponse,
        {
            "residentAndConsumptionUuidsMap": {
                "17c4dff7-799f-4f16-badc-a9b3607a9383": "7a226e08-2a90-4db9-ae9b-8148901c6ec2",
                "756a591c-185b-4441-a21a-46d4b94df4ad": "df3e8a64-a622-4ffb-97c5-b892a2cf331d",
            }
        },
    )
    assert ista_client.get_uuids() == ["7a226e08-2a90-4db9-ae9b-8148901c6ec2", "df3e8a64-a622-4ffb-97c5-b892a2cf331d"]


@pytest.mark.usefixtures("mock_httpx_login")
async def test_get_account(ista_client: PyEcotrendIsta, snapshot: SnapshotAssertion) -> None:
    """Test `get_account` method."""

    with pytest.raises(LoginError):
        assert ista_client.get_account() is None

    await ista_client.login()
    assert ista_client.get_account() == snapshot
