"""Tests for `get_consumption_unit_details` method."""

from http import HTTPStatus

import pytest
import requests
from requests_mock.mocker import Mocker as RequestsMock
from syrupy.assertion import SnapshotAssertion

from pyecotrend_ista import LoginError, ParserError, PyEcotrendIsta, ServerError
from pyecotrend_ista.const import API_BASE_URL


@pytest.mark.usefixtures("mock_requests_login")
def test_get_consumption_unit_details(ista_client: PyEcotrendIsta, snapshot: SnapshotAssertion) -> None:
    """Test `get_consumption_unit_details` method."""

    ista_client.login()

    assert ista_client.get_consumption_unit_details() == snapshot


@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    (
        [
            (HTTPStatus.OK, ParserError),
            (HTTPStatus.BAD_REQUEST, ServerError),
            (HTTPStatus.UNAUTHORIZED, LoginError),
        ]
    ),
)
def test_get_consumption_unit_details_http_errors(
    requests_mock: RequestsMock, ista_client: PyEcotrendIsta, status_code: HTTPStatus, expected_exception
) -> None:
    """Test Login method."""

    requests_mock.get(
        f"{API_BASE_URL}menu",
        status_code=status_code,
    )

    with pytest.raises(expected_exception=expected_exception):
        ista_client.get_consumption_unit_details()


@pytest.mark.parametrize(
    ("exception", "expected_exception"), ([(requests.RequestException, ServerError), (requests.Timeout, ServerError)])
)
def test_get_consumption_unit_details_exceptions(
    ista_client: PyEcotrendIsta,
    requests_mock: RequestsMock,
    exception,
    expected_exception,
) -> None:
    """Test exceptions for method `get_consumption_unit_details`."""

    requests_mock.get(f"{API_BASE_URL}menu", exc=exception)

    with pytest.raises(expected_exception=expected_exception):
        ista_client.get_consumption_unit_details()
