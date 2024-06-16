"""Types for PyEcotrendIsta."""

from typing import TypedDict


class GetTokenResponse(TypedDict):
    """A TypedDict for the response returned by the getToken function.

    Attributes
    ----------
    access_token : str
        The access token issued by the authentication provider.
    expires_in : int
        The number of seconds until the access token expires.
    refresh_token : str
        The refresh token that can be used to obtain new access tokens.
    refresh_expires_in : int
        The number of seconds until the refresh token expires.

    """

    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int


class AccountResponse(TypedDict):
    """Represents the response for an account in the ista EcoTrend API.

    Attributes
    ----------
    firstName : str
        The first name of the account holder.
    lastName : str
        The last name of the account holder.
    email : str
        The email address of the account holder.
    keycloakId : str
        The Keycloak ID associated with the account.
    country : str
        The country associated with the account.
    locale : str
        The locale setting for the account.
    authcode : str
        The authentication code for the account.
    tos : str
        The terms of service agreed to by the account holder.
    tosUpdated : str
        The date the terms of service were last updated.
    privacy : str
        The privacy setting for the account.
    mobileNumber : str
        The mobile phone number associated with the account.
    transitionMobileNumber : str
        The mobile number used during the transition period.
    unconfirmedPhoneNumber : str
        The unconfirmed phone number associated with the account.
    password : str
        The password for the account.
    enabled : bool
        Indicates whether the account is enabled.
    consumptionUnitUuids : list of str
        List of UUIDs for the consumption units.
    residentTimeRangeUuids : list of str
        List of UUIDs for the resident time ranges.
    ads : bool
        Indicates whether advertisements are enabled.
    marketing : bool
        Indicates whether the account holder has opted into marketing communications.
    fcmToken : str
        The FCM (Firebase Cloud Messaging) token for push notifications.
    betaPhase : str
        Indicates if the account is in the beta phase.
    notificationMethod : str
        The method of notification preferred by the account holder.
    emailConfirmed : bool
        Indicates whether the email address is confirmed.
    isDemo : bool
        Indicates whether the account is a demo account.
    userGroup : str
        The user group the account belongs to.
    mobileLoginStatus : str
        The status of mobile login for the account.
    residentAndConsumptionUuidsMap : dict of str to str
        A map of resident UUIDs to consumption unit UUIDs.
    activeConsumptionUnit : str
        The UUID of the active consumption unit.
    supportCode : str
        The support code for the account.
    notificationMethodEmailConfirmed : bool
        Indicates whether the email for notification method is confirmed.
    """

    firstName: str
    lastName: str
    email: str
    keycloakId: str
    country: str
    locale: str
    authcode: str
    tos: str
    tosUpdated: str
    privacy: str
    mobileNumber: str
    transitionMobileNumber: str
    unconfirmedPhoneNumber: str
    password: str
    enabled: bool
    consumptionUnitUuids: list[str]
    residentTimeRangeUuids: list[str]
    ads: bool
    marketing: bool
    fcmToken: str
    betaPhase: str
    notificationMethod: str
    emailConfirmed: bool
    isDemo: bool
    userGroup: str
    mobileLoginStatus: str
    residentAndConsumptionUuidsMap: dict[str, str]
    activeConsumptionUnit: str
    supportCode: str
    notificationMethodEmailConfirmed: bool
