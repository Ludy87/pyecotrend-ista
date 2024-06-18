"""Tests for _set_account methods."""

from http import HTTPStatus

import pytest
import requests
from requests_mock.mocker import Mocker as RequestsMock
from syrupy.assertion import SnapshotAssertion

from pyecotrend_ista import LoginError, ParserError, PyEcotrendIsta, ServerError
from pyecotrend_ista.const import API_BASE_URL


@pytest.mark.usefixtures("mock_requests_login")
def test_set_account(ista_client: PyEcotrendIsta, snapshot: SnapshotAssertion) -> None:
    """Test `_set_account` method."""

    ista_client._PyEcotrendIsta__set_account()  # type: ignore[attr-defined] # pylint: disable=W0212

    assert ista_client._account == snapshot  # pylint: disable=W0212
    assert ista_client.get_uuids() == ["7a226e08-2a90-4db9-ae9b-8148901c6ec2"]


@pytest.mark.parametrize(
    ("exception", "expected_exception"), ([(requests.RequestException, ServerError), (requests.Timeout, ServerError)])
)
def test_set_account_exceptions(
    requests_mock: RequestsMock, ista_client: PyEcotrendIsta, exception, expected_exception
) -> None:
    """Test `_set_account` method exceptions."""

    requests_mock.get(f"{API_BASE_URL}account", exc=exception)

    with pytest.raises(expected_exception=expected_exception):
        ista_client._PyEcotrendIsta__set_account()  # type: ignore[attr-defined] # pylint: disable=W0212

@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    ([(HTTPStatus.OK, ParserError), (HTTPStatus.BAD_REQUEST, ServerError), (HTTPStatus.UNAUTHORIZED, LoginError)]),
)
def test_set_account_httperrors(
    requests_mock: RequestsMock, ista_client: PyEcotrendIsta, status_code: HTTPStatus, expected_exception
) -> None:
    """Test `_set_account` method http status errors."""

    requests_mock.get(f"{API_BASE_URL}account", status_code=status_code)

    with pytest.raises(expected_exception=expected_exception):
        ista_client._PyEcotrendIsta__set_account()  # type: ignore[attr-defined] # pylint: disable=W0212
