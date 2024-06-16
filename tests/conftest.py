"""Fixtures for Tests."""

import pytest
from pyecotrend_ista.const import ACCOUNT_URL, DEMO_USER_TOKEN, PROVIDER_URL
from pyecotrend_ista.pyecotrend_ista import PyEcotrendIsta

TEST_EMAIL = "max.istamann@test.com"
DEMO_EMAIL = "demo@ista.de"
TEST_PASSWORD = "password"


@pytest.fixture
def ista_client(request) -> PyEcotrendIsta:
    """Create Bring instance."""
    ista = PyEcotrendIsta(
        email=request.param,
        password=TEST_PASSWORD,
    )
    return ista


@pytest.fixture
def mock_requests_login(requests_mock):
    """Mock requests to Login Endpoints."""
    requests_mock.post(
        PROVIDER_URL + "token",
        json={
            "accessToken": "ACCESS_TOKEN",
            "accessTokenExpiresIn": 60,
            "refreshToken": "REFRESH_TOKEN",
            "refreshTokenExpiresIn": 5184000,
        },
    )
    requests_mock.get(
        DEMO_USER_TOKEN,
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
        ACCOUNT_URL,
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
