"""Tests for Login methods."""


import pytest

from pyecotrend_ista import PyEcotrendIsta
from tests.conftest import DEMO_EMAIL, TEST_EMAIL


@pytest.mark.usefixtures("mock_httpx_login")
@pytest.mark.parametrize("ista_client", [TEST_EMAIL, DEMO_EMAIL], indirect=True)
async def test_login_and_logout(ista_client: PyEcotrendIsta) -> None:
    """Test Login method."""
    assert await ista_client.login()
    try:
        await ista_client.logout()
    except Exception:
        pytest.fail("Logout failed.")
