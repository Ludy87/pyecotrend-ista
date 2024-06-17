"""Tests for Login methods."""

from unittest.mock import MagicMock

import pytest
import requests
from requests.exceptions import JSONDecodeError
from requests_mock.mocker import Mocker as RequestsMock
from syrupy.assertion import SnapshotAssertion

from pyecotrend_ista import PyEcotrendIsta, ServerError
from pyecotrend_ista.const import API_BASE_URL
from tests.conftest import DEMO_EMAIL, TEST_EMAIL


@pytest.mark.parametrize("ista_client", [TEST_EMAIL, DEMO_EMAIL], indirect=True)
@pytest.mark.usefixtures("mock_requests_login")
def test_login(ista_client: PyEcotrendIsta) -> None:
    """Test Login method."""
    assert ista_client.login() == "ACCESS_TOKEN"


@pytest.mark.parametrize("ista_client", [DEMO_EMAIL], indirect=True)
@pytest.mark.usefixtures("mock_requests_login")
def test_demo_user_login(ista_client: PyEcotrendIsta, snapshot: SnapshotAssertion) -> None:
    """Test Login method."""

    assert ista_client.demo_user_login() == snapshot



@pytest.mark.parametrize("ista_client", [DEMO_EMAIL], indirect=True)
@pytest.mark.parametrize(
    ("exception", "expected_exception"), ([(requests.RequestException, ServerError), (requests.Timeout, ServerError)])
)
def test_demo_user_login_exceptions(
    ista_client: PyEcotrendIsta,
    mock_requests_login: RequestsMock,
    exception,
    expected_exception,
) -> None:
    """Test exceptions for method `demo_user_login`."""

    mock_requests_login.get(f"{API_BASE_URL}demo-user-token", exc=exception)

    with pytest.raises(expected_exception=expected_exception):
        ista_client.demo_user_login()


@pytest.mark.parametrize("ista_client", [DEMO_EMAIL], indirect=True)
def test_demo_user_login_parser_exception(ista_client: PyEcotrendIsta, mock_requests_login: RequestsMock) -> None:
    """Test JSONDecodeError exception for method `demo_user_login`."""

    json_encoder = MagicMock().json.side_effect = JSONDecodeError("test", "test", 0)
    mock_requests_login.get(f"{API_BASE_URL}demo-user-token", json_encoder=json_encoder)

    with pytest.raises(expected_exception=ServerError):
        ista_client.demo_user_login()

