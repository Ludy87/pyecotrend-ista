"""Types for PyEcotrendIsta."""

from typing import Any, Literal, TypedDict


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

class IstaMonthYear(TypedDict):
    """A TypedDict representing a month and year.

    Attributes
    ----------
    month : int
        The month value.
    year : int
        The year value.
    """

    month: int
    year: int

class IstaAverageConsumption(TypedDict):
    """A TypedDict representing average consumption values.

    Attributes
    ----------
    additionalAverageConsumptionPercentage : int
        Percentage of additional average consumption.
    additionalAverageConsumptionValue : str
        Value of additional average consumption.
    additionalResidentConsumptionPercentage : int
        Percentage of additional resident consumption.
    additionalResidentConsumptionValue : str
        Value of additional resident consumption.
    averageConsumptionPercentage : int
        Percentage of average consumption.
    averageConsumptionValue : str
        Value of average consumption.
    residentConsumptionPercentage : int
        Percentage of resident consumption.
    residentConsumptionValue : str
        Value of resident consumption.
    """

    additionalAverageConsumptionPercentage: int
    additionalAverageConsumptionValue: str
    additionalResidentConsumptionPercentage: int
    additionalResidentConsumptionValue: str
    averageConsumptionPercentage: int
    averageConsumptionValue: str
    residentConsumptionPercentage: int
    residentConsumptionValue: str

class IstaCompared(TypedDict):
    """A TypedDict representing compared values.

    Attributes
    ----------
    comparedPercentage : int
        Percentage comparison value.
    comparedValue : str
        Compared value.
    lastYearValue : float
        Value from the last year.
    period : IstaMonthYear
        Period associated with the comparison.
    smiley : str
        Smiley associated with the comparison.
    """

    comparedPercentage: int
    comparedValue: str
    lastYearValue: float
    period: IstaMonthYear
    smiley: str

class IstaReading(TypedDict):
    """A TypedDict representing a reading.

    Attributes
    ----------
    additionalUnit : str
        Additional unit associated with the reading.
    additionalValue : str
        Additional value associated with the reading.
    averageConsumption : IstaAverageConsumption
        Average consumption details.
    comparedConsumption : dict
        Compared consumption details.
    comparedCost : IstaCompared
        Compared cost details.
    estimated : bool
        Indicates if the reading is estimated.
    type : Literal["heating", "warmwater", "water"]
        Type of the reading (heating, warmwater, water).
    unit : str
        Unit of measurement for the reading.
    value : str
        Value of the reading.
    """

    additionalUnit: str
    additionalValue: str
    averageConsumption: IstaAverageConsumption
    comparedConsumption: dict
    comparedCost: IstaCompared
    estimated: bool
    type: Literal["heating", "warmwater", "water"]
    unit: str
    value: str

class IstaTimeRange(TypedDict):
    """A TypedDict representing a time range.

    Attributes
    ----------
    end : IstaMonthYear
        The end of the time range.
    start : IstaMonthYear
        The start of the time range.
    """

    end: IstaMonthYear
    start: IstaMonthYear

class IstaBillingPeriod(TypedDict):
    """A TypedDict representing a billing period.

    Attributes
    ----------
    exception : Any, optional
        Any exceptions related to this billing period. (data type unknown)
    readings : list[IstaReading]
        List of readings associated with this billing period.
    timeRange : IstaTimeRange
        The time range for this billing period.
    """

    exception: Any
    readings: list[IstaReading]
    timeRange:IstaTimeRange

class IstaBillingPeriods(TypedDict):
    """A TypedDict representing the billing periods.

    Attributes
    ----------
    currentBillingPeriod : IstaBillingPeriod
        The details of the current billing period.
    previousBillingPeriod : IstaBillingPeriod
        The details of the previous billing period.
    """

    currentBillingPeriod: IstaBillingPeriod
    previousBillingPeriod: IstaBillingPeriod

class IstaCostsByEnergyType(TypedDict):
    """A TypedDict representing the costs associated with a specific energy type.

    Attributes
    ----------
    comparedCost : IstaCompared
        The cost comparison data for the energy type.
    estimated : bool
        Indicates whether the cost is estimated.
    type : Literal["heating", "warmwater", "water"]
        The type of energy (heating, warm water, or water).
    unit : str
        The unit of measurement for the cost.
    value : int
        The cost value.
    """

    comparedCost: IstaCompared
    estimated: bool
    type: Literal["heating", "warmwater", "water"]
    unit: str
    value: int

class IstaPeriods(TypedDict):
    """A TypedDict representing data for a specific period.

    Attributes
    ----------
    date : IstaMonthYear
        The month and year for the period.
    documentNumber : str | None
        The document number associated with the period, if any.
    exception : Any
        An exception associated with the period (data type unspecified).
    isSCEedBasic : bool
        Indicates if the SCEed basic plan is active for the period.
    readings : list[IstaReading]
        A list of readings recorded during the period.
    costsByEnergyType : list[IstaCostsByEnergyType]
        A list of costs categorized by energy type for the period.
    """

    date: IstaMonthYear
    documentNumber: str | None
    exception: Any
    isSCEedBasic: bool
    readings: list[IstaReading]
    costsByEnergyType: list[IstaCostsByEnergyType]



class ConsumptionsResponse(TypedDict, total=False):
    """A TypedDict representing the response structure for consumption data.

    Attributes
    ----------
    co2Emissions : list[IstaPeriods]
        A list of CO2 emission data over different periods.
    co2EmissionsBillingPeriods : list[IstaBillingPeriods]
        A list of CO2 emission data over different billing periods.
    consumptionUnitId : str
        The unique identifier for the consumption unit.
    consumptions : list[IstaPeriods]
        A list of consumption data over different periods.
    consumptionsBillingPeriods : IstaBillingPeriods
        The consumption data over different billing periods.
    costs : list[IstaPeriods]
        A list of cost data over different periods.
    costsBillingPeriods : IstaBillingPeriods
        The cost data over different billing periods.
    isSCEedBasicForCurrentMonth : bool
        Indicates if the SCEed basic plan is active for the current month.
    nonEEDBasicStartDate : Any
        The start date for non-EED basic plan (data type unknown).
    resident : dict[str, Any]
        A dictionary containing resident information.

    """

    co2Emissions: list[IstaPeriods]
    co2EmissionsBillingPeriods: list[IstaBillingPeriods]
    consumptionUnitId: str
    consumptions: list[IstaPeriods]
    consumptionsBillingPeriods: IstaBillingPeriods
    costs: list[IstaPeriods]
    costsBillingPeriods: IstaBillingPeriods
    isSCEedBasicForCurrentMonth: bool
    nonEEDBasicStartDate: Any
    resident: dict[str, Any]



class IstaConsumptionUnitAddress(TypedDict):
    """Represents the address of a consumption unit.

    Attributes
    ----------
    street : str
        The street name of the address.
    houseNumber : str
        The house number of the address.
    postalCode : str
        The postal code of the address.
    city : str
        The city of the address.
    country : str
        The country code of the address.
    floor : str
        The floor number of the address.
    propertyNumber : str
        The property number of the address.
    consumptionUnitNumber : str
        The consumption unit number associated with the address.
    idAtCustomerUser : str
        The ID assigned to the address at the customer user's end.
    """

    street: str
    houseNumber: str
    postalCode: str
    city: str
    country: str # country code
    floor: str
    propertyNumber: str
    consumptionUnitNumber: str
    idAtCustomerUser: str

class IstaConsumptionUnitBookedServices(TypedDict):
    """Represents the booked extra services for an Ista consumption unit.

    Attributes
    ----------
    cost : bool
        Indicates if cost service is booked.
    co2 : bool
        Indicates if CO2 service is booked.
    """

    cost: bool
    co2: bool

class IstaConsumptionUnit(TypedDict):
    """Represents a consumption unit.

    Attributes
    ----------
    id : str
        The UUID of the consumption unit.
    address : IstaConsumptionUnitAddress
        The address details of the consumption unit.
    booked : IstaConsumptionUnitBookedServices
        The booked services for the consumption unit.
    propertyNumber : str
        The property number associated with the consumption unit.
    """

    id: str # UUID
    address: IstaConsumptionUnitAddress
    booked: IstaConsumptionUnitBookedServices
    propertyNumber: str


class ConsumptionUnitDetailsResponse(TypedDict):
    """Represents the response details for consumption units.

    Attributes
    ----------
    consumptionUnits : list[IstaConsumptionUnit]
        The list of consumption units.
    coBranding : Any
        Co-branding information (data type unknown).
    """

    consumptionUnits: list[IstaConsumptionUnit]
    coBranding: Any # #unknown
