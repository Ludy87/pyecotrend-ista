VERSION = "2.0.11"
LOGIN_HEADER = {"Content-Type": "application/json"}
BASE_URL = "https://api.prod.eed.ista.com/"
ACCOUNT_URL = BASE_URL + "account"
CONSUMPTIONS_URL = BASE_URL + "consumptions?consumptionUnitUuid="
LOGIN_URL = BASE_URL + "login"
REFRESH_TOKEN_URL = BASE_URL + "account/refresh-token"

MAX_RETRIES = 3
RETRY_DELAY = 2
