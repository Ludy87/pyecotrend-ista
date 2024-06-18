"""Tests for Login methods."""

from http import HTTPStatus

import pytest
import requests
from requests_mock.mocker import Mocker as RequestsMock
from syrupy.assertion import SnapshotAssertion

from pyecotrend_ista import ParserError, PyEcotrendIsta, ServerError
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


@pytest.mark.parametrize(
    ("exception", "expected_exception"), ([(requests.RequestException, ServerError), (requests.Timeout, ServerError)])
)
def test_demo_user_login_exceptions(
    ista_client: PyEcotrendIsta,
    requests_mock: RequestsMock,
    exception,
    expected_exception,
) -> None:
    """Test exceptions for method `demo_user_login`."""

    requests_mock.get(f"{API_BASE_URL}demo-user-token", exc=exception)

    with pytest.raises(expected_exception=expected_exception):
        ista_client.demo_user_login()


@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    ([(HTTPStatus.OK, ParserError), (HTTPStatus.BAD_REQUEST, ServerError)]),
)
def test_demo_user_login_http_errors(
    ista_client: PyEcotrendIsta,
    requests_mock: RequestsMock,
    status_code: HTTPStatus,
    expected_exception,
) -> None:
    """Test http errors for method `demo_user_login`."""

    requests_mock.get(f"{API_BASE_URL}demo-user-token", status_code=status_code)

    with pytest.raises(expected_exception=expected_exception):
        ista_client.demo_user_login()
