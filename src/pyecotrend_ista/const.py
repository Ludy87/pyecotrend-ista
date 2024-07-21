"""Constants for PyEcotrendIsta."""

from pyecotrend_ista.__version import __version__

VERSION = __version__

API_BASE_URL = "https://api.prod.eed.ista.com/"

DEMO_USER_ACCOUNT = "demo@ista.de"

PROVIDER_URL = "https://keycloak.ista.com/realms/eed-prod/protocol/openid-connect/"
REDIRECT_URI = "https://ecotrend.ista.de/login-redirect"
CLIENT_ID = "ecotrend"
SCOPE = "openid"
RESPONSE_MODE = "fragment"
RESPONSE_TPYE = "code"
GRANT_TYPE_REFRESH_TOKEN = "refresh_token"
GRANT_TYPE_AUTHORIZATION_CODE = "authorization_code"

TIMEOUT = 10
