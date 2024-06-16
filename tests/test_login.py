"""Tests for Login methods."""

import pytest
from pyecotrend_ista.pyecotrend_ista import PyEcotrendIsta

from tests.conftest import DEMO_EMAIL, TEST_EMAIL


@pytest.mark.parametrize("ista_client", [TEST_EMAIL, DEMO_EMAIL], indirect=True)
@pytest.mark.usefixtures("mock_requests_login")
def test_login(ista_client: PyEcotrendIsta) -> None:
    """Test Login method."""
    assert ista_client.login() == "ACCESS_TOKEN"


@pytest.mark.parametrize("ista_client", [TEST_EMAIL, DEMO_EMAIL], indirect=True)
@pytest.mark.usefixtures("mock_requests_login")
def test_account_data(ista_client: PyEcotrendIsta) -> None:
    """Test Login method."""
    ista_client.login()

    assert ista_client._account["activeConsumptionUnit"] == "7a226e08-2a90-4db9-ae9b-8148901c6ec2"
    assert ista_client._uuid == "7a226e08-2a90-4db9-ae9b-8148901c6ec2"
    assert ista_client.get_uuids() == ["7a226e08-2a90-4db9-ae9b-8148901c6ec2"]
