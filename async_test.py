"""Testing the async authentication backend."""
import asyncio
import logging

from httpx import AsyncClient

from pyecotrend_ista.const import PROVIDER_URL, REDIRECT_URI

# from pyecotrend_ista.exception_classes import KeycloakGetError
from pyecotrend_ista.openid import OpenIDAuthenticator

logging.basicConfig(level=logging.DEBUG)



async def main():
    """."""

    async with AsyncClient() as client:
        client = OpenIDAuthenticator(
            provider_url=PROVIDER_URL,
            client_id="ecotrend",
            redirect_uri=REDIRECT_URI,
            client=client,
        )
        def otp_callback():
            """Prompt user to enter the OTP code."""
            return input("Enter OTP code: ")


        # uncomment to test with production account. Will prompt for OTP-code if 2FA enabled
        # for retries in range(3):
        #     try:
        #         await client.login("", password="", otp_callback=otp_callback)
        #     except KeycloakGetError:
        #         retries += 1
        #     else:
        #         return

        # instead of login use this to authenticate with a demo user

        await client.get_demo_user_tokens()


        try:

            account = await client.async_get("https://api.prod.eed.ista.com/account")
            print(account)

            await asyncio.sleep(5) # set to 60s to test refresh of authentication token between requests
            params = {
                "consumptionUnitUuid": account["activeConsumptionUnit"]
            }


            details = await client.async_get("https://api.prod.eed.ista.com/menu")
            print(details)
            await asyncio.sleep(5)

            consumption = await client.async_get("https://api.prod.eed.ista.com/consumptions", params=params)
            print(consumption)


        except KeyboardInterrupt:
            print('interrupted!')
asyncio.run(main())
