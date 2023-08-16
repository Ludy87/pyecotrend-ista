VERSION = "2.2.4"
LOGIN_HEADER = {"Content-Type": "application/json"}
BASE_URL = "https://api.prod.eed.ista.com/"
ACCOUNT_URL = BASE_URL + "account"
CONSUMPTIONS_URL = BASE_URL + "consumptions?consumptionUnitUuid="
LOGIN_URL = BASE_URL + "login"
REFRESH_TOKEN_URL = BASE_URL + "account/refresh-token"

PROVIDER_URL = "https://keycloak.ista.com/realms/eed-prod/protocol/openid-connect/"
REDIRECT_URI = "https://ecotrend.ista.de/login-redirect"
CLIENT_ID = "ecotrend"
SCOPE = "openid"
RESPONSE_MODE = "fragment"
RESPONSE_TPYE = "code"
CODE_CHALLENGE_METHODE = "S256"
GRANT_TYPE_REFRESH_TOKEN = "refresh_token"
GRANT_TYPE_AUTHORIZATION_CODE = "authorization_code"

MAX_RETRIES = 3
RETRY_DELAY = 2
