"""Tests for _set_account methods."""

from http import HTTPStatus

import pytest
import requests
from requests_mock.mocker import Mocker as RequestsMock
from syrupy.assertion import SnapshotAssertion
from syrupy.filters import paths

from pyecotrend_ista import LoginError, ParserError, PyEcotrendIsta, ServerError
from pyecotrend_ista.const import API_BASE_URL


def test_get_comsumption_data(ista_client: PyEcotrendIsta, requests_mock: RequestsMock, snapshot: SnapshotAssertion, dataset) -> None:
    """Test `_set_account` method."""

    requests_mock.get(f"{API_BASE_URL}consumptions", json=dataset["test_data"])

    assert ista_client.get_comsumption_data("26e93f1a-c828-11ea-87d0-0242ac130003") == snapshot


@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    (
        [
            (HTTPStatus.OK, ParserError),
            (HTTPStatus.INTERNAL_SERVER_ERROR, ServerError),
            (HTTPStatus.BAD_REQUEST, ValueError),
            (HTTPStatus.UNAUTHORIZED, LoginError),
        ]
    ),
)
def test_get_comsumption_data_http_errors(
    requests_mock: RequestsMock, ista_client: PyEcotrendIsta, status_code: HTTPStatus, expected_exception
) -> None:
    """Test Login method."""

    requests_mock.get(
        f"{API_BASE_URL}consumptions?consumptionUnitUuid=26e93f1a-c828-11ea-87d0-0242ac130003",
        status_code=status_code,
    )

    with pytest.raises(expected_exception=expected_exception):
        ista_client.get_comsumption_data("26e93f1a-c828-11ea-87d0-0242ac130003")


@pytest.mark.parametrize(
    ("exception", "expected_exception"), ([(requests.RequestException, ServerError), (requests.Timeout, ServerError)])
)
def test_get_comsumption_data_exceptions(requests_mock: RequestsMock, ista_client: PyEcotrendIsta, exception, expected_exception) -> None:
    """Test Login method."""

    requests_mock.get(
        f"{API_BASE_URL}consumptions?consumptionUnitUuid=26e93f1a-c828-11ea-87d0-0242ac130003", exc=exception
    )

    with pytest.raises(expected_exception=expected_exception):
        ista_client.get_comsumption_data("26e93f1a-c828-11ea-87d0-0242ac130003")


def test_consum_raw(ista_client: PyEcotrendIsta, requests_mock: RequestsMock, snapshot: SnapshotAssertion, dataset) -> None:
    """Test `cunsum_raw` method."""

    requests_mock.get(f"{API_BASE_URL}consumptions", json=dataset["test_data"])
    result = ista_client.consum_raw(obj_uuid="26e93f1a-c828-11ea-87d0-0242ac130003")

    # consum_raw returns consum_types list in random order, so we exclude it from snapshot matcher
    assert ["heating", "warmwater"] == sorted(result["consum_types"])
    assert result == snapshot(exclude=paths("consum_types"))
