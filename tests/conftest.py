"""Fixtures for Tests."""

from http import HTTPStatus
from pathlib import Path

import pytest
from requests_mock.mocker import Mocker as RequestsMock

from pyecotrend_ista import PyEcotrendIsta
from pyecotrend_ista.const import API_BASE_URL, DEMO_USER_ACCOUNT, PROVIDER_URL

TEST_EMAIL = "max.istamann@test.com"
DEMO_EMAIL = DEMO_USER_ACCOUNT
TEST_PASSWORD = "password"

@pytest.fixture
def json_data(request) -> str:
    """Load json test data."""
    file = getattr(request, "param", "test_data")
    path = Path(__file__).parent / "data" / f"{file}.json"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def ista_client(request) -> PyEcotrendIsta:
    """Create Bring instance."""
    ista = PyEcotrendIsta(
        email=getattr(request, "param", TEST_EMAIL),
        password=TEST_PASSWORD,
    )
    return ista


@pytest.fixture
def mock_requests_login(requests_mock: RequestsMock) -> RequestsMock:
    """Mock requests to Login Endpoints."""
    requests_mock.post(
        PROVIDER_URL + "token",
        json={
            "access_token": "ACCESS_TOKEN",
            "expires_in": 60,
            "refresh_expires_in": 5183999,
            "refresh_token": "REFRESH_TOKEN",
            "token_type": "Bearer",
            "id_token": "ID_TOKEN",
            "not-before-policy": 0,
            "session_state": "SESSION_STATE",
            "scope": "openid profile email",
        },
    )
    requests_mock.get(
        f"{API_BASE_URL}demo-user-token",
        json={
            "accessToken": "ACCESS_TOKEN",
            "accessTokenExpiresIn": 60,
            "refreshToken": "REFRESH_TOKEN",
            "refreshTokenExpiresIn": 5184000,
        },
    )
    requests_mock.get(
        PROVIDER_URL + "auth",
        text="""<form id="kc-form-login" onsubmit="return validateForm();"  action="https://keycloak.ista.com/realms/eed-prod/login-actions/authenticate?session_code=SESSION_CODE&amp;execution=EXECUTION&amp;client_id=ecotrend&amp;tab_id=TAB_ID" method="post">""",
        headers={
            "Set-Cookie": "AUTH_SESSION_ID=xxxxx.keycloak-xxxxxx; Version=1; Path=/realms/eed-prod/; SameSite=None; Secure; HttpOnly"
        },
    )
    requests_mock.post(
        "https://keycloak.ista.com/realms/eed-prod/login-actions/authenticate",
        headers={"Location": "https://ecotrend.ista.de/login-redirect#state=STATE&session_state=SESSION_STATE&code=AUTH_CODE"},
    )
    requests_mock.get(
        f"{API_BASE_URL}account",
        json={
            "firstName": "Max",
            "lastName": "Istamann",
            "email": "max.istamann@test.com",
            "keycloakId": None,
            "country": "DE",
            "locale": "de_DE",
            "authcode": None,
            "tos": "1.0",
            "tosUpdated": "01.01.1970",
            "privacy": None,
            "mobileNumber": "+49123456789",
            "transitionMobileNumber": "",
            "unconfirmedPhoneNumber": "",
            "password": None,
            "enabled": True,
            "consumptionUnitUuids": None,
            "residentTimeRangeUuids": None,
            "ads": False,
            "marketing": False,
            "fcmToken": "null",
            "betaPhase": None,
            "notificationMethod": "email",
            "emailConfirmed": False,
            "isDemo": False,
            "userGroup": "resident",
            "mobileLoginStatus": "non_initial",
            "residentAndConsumptionUuidsMap": {"17c4dff7-799f-4f16-badc-a9b3607a9383": "7a226e08-2a90-4db9-ae9b-8148901c6ec2"},
            "activeConsumptionUnit": "7a226e08-2a90-4db9-ae9b-8148901c6ec2",
            "supportCode": "XXXXXXXXX",
            "notificationMethodEmailConfirmed": True,
        },
    )
    requests_mock.post(PROVIDER_URL + "logout", status_code=HTTPStatus.NO_CONTENT)

    requests_mock.get(
        f"{API_BASE_URL}menu",
        json={
            "consumptionUnits": [
                {
                    "id": "7a226e08-2a90-4db9-ae9b-8148901c6ec2",
                    "address": {
                        "street": "Luxemburger Str.",
                        "houseNumber": "1",
                        "postalCode": "45131",
                        "city": "Essen",
                        "country": "DE",
                        "floor": "2. OG links",
                        "propertyNumber": "112233445",
                        "consumptionUnitNumber": "0001",
                        "idAtCustomerUser": "6234XB",
                    },
                    "booked": {"cost": True, "co2": False},
                    "propertyNumber": "57352474",
                }
            ],
            "coBranding": None,
        },
    )

    return requests_mock
