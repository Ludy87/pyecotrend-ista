"""Fixtures for Tests."""

from collections.abc import AsyncGenerator
from http import HTTPStatus

from httpx import AsyncClient
import pytest
from pytest_httpx import HTTPXMock

from pyecotrend_ista import PyEcotrendIsta
from pyecotrend_ista.const import API_BASE_URL, DEMO_USER_ACCOUNT, PROVIDER_URL

TEST_EMAIL = "max.istamann@test.com"
DEMO_EMAIL = DEMO_USER_ACCOUNT
TEST_PASSWORD = "password"


@pytest.fixture
async def ista_client(request, httpx_mock: HTTPXMock) -> AsyncGenerator[PyEcotrendIsta, None]:
    """Create Bring instance."""

    async with AsyncClient() as session:
        ista = PyEcotrendIsta(
            email=getattr(request, "param", TEST_EMAIL),
            password=TEST_PASSWORD,
            session=session
        )
        yield ista


@pytest.fixture
def assert_all_responses_were_requested() -> bool:
    """Don't fail if not all mocks requested."""

    return False

@pytest.fixture
def mock_httpx_login(httpx_mock: HTTPXMock, assert_all_responses_were_requested: bool) -> HTTPXMock:
    """Mock requests to Login Endpoints."""

    httpx_mock.add_response(
        url=PROVIDER_URL + "auth?response_mode=fragment&response_type=code&client_id=ecotrend&scope=openid&redirect_uri=https%3A%2F%2Fecotrend.ista.de%2Flogin-redirect",
        method="GET",
        text="""<html><bod><form id="kc-form-login" onsubmit="return validateForm();"  action="https://keycloak.ista.com/realms/eed-prod/login-actions/authenticate?session_code=SESSION_CODE&amp;execution=EXECUTION&amp;client_id=ecotrend&amp;tab_id=TAB_ID" method="post"></body></html>"""
    )
    httpx_mock.add_response(
        url="https://keycloak.ista.com/realms/eed-prod/login-actions/authenticate?session_code=SESSION_CODE&execution=EXECUTION&client_id=ecotrend&tab_id=TAB_ID",
        method="POST",
        headers={"Location": "https://ecotrend.ista.de/login-redirect#state=STATE&session_state=SESSION_STATE&code=AUTH_CODE"},
        status_code=302
    )

    httpx_mock.add_response(
        url=PROVIDER_URL + "token",
        method="POST",
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


    httpx_mock.add_response(
        url=f"{API_BASE_URL}account",
        method="GET",
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
    httpx_mock.add_response(
        url=f"{PROVIDER_URL}logout?client_id=ecotrend&post_logout_redirect_uri=https%3A%2F%2Fecotrend.ista.de&id_token_hint=ID_TOKEN",
        method="GET",
        status_code=HTTPStatus.FOUND,
    )

    httpx_mock.add_response(
        url=f"{API_BASE_URL}menu",
        method="GET",
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

    httpx_mock.add_response(
        url=f"{API_BASE_URL}demo-user-token",
        method="GET",
        text="""{
                "accessToken": "DEMO_USER_ACCESS_TOKEN",
                "accessTokenExpiresIn": 60,
                "refreshToken": "DEMO_USER_REFRESH_TOKEN",
                "refreshTokenExpiresIn": 5184000
                }"""
    )
    httpx_mock.add_response(
        url=f"{PROVIDER_URL}logout?client_id=ecotrend&post_logout_redirect_uri=https%3A%2F%2Fecotrend.ista.de",
        method="GET",
        status_code=HTTPStatus.FOUND
    )

    return httpx_mock
