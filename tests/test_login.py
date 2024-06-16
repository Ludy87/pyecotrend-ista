"""Tests for Login methods."""



import pytest
from pyecotrend_ista.pyecotrend_ista import PyEcotrendIsta

from tests.conftest import DEMO_EMAIL, TEST_EMAIL


@pytest.mark.parametrize('ista_client', [TEST_EMAIL, DEMO_EMAIL], indirect=True)
@pytest.mark.usefixtures("mock_requests_login")
def test_login(ista_client: PyEcotrendIsta) -> None:
    """Test Login method."""
    assert ista_client.login() == "ACCESS_TOKEN"


