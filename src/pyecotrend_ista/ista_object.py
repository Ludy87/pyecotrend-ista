from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class Resident(DataClassJsonMixin):
    movedOut: bool
    moveOutDate: Any
    invalid: bool
    invalidDate: Any


@dataclass_json
@dataclass
class Date(DataClassJsonMixin):
    month: int
    year: int

    def __str__(self) -> str:
        return self.schema().dumps(self.to_dict())


@dataclass_json
@dataclass
class AcerageConsumption(DataClassJsonMixin):
    averageConsumptionValue: float
    residentConsumptionValue: float
    averageConsumptionPercentage: float
    residentConsumptionPercentage: float
    additionalAverageConsumptionValue: float
    additionalResidentConsumptionValue: float
    additionalAverageConsumptionPercentage: float
    additionalResidentConsumptionPercentage: float

    def replace_point(self):
        for _field in self.__dataclass_fields__.values():
            if isinstance(getattr(self, _field.name), str):
                setattr(self, _field.name, float(getattr(self, _field.name).replace(",", ".")))

    def __post_init__(self):
        self.replace_point()


@dataclass_json
@dataclass
class Readings(DataClassJsonMixin):
    type: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    additionalValue: Optional[float] = None
    additionalUnit: Optional[str] = None
    averageConsumption: Optional[AcerageConsumption] = None

    def replace_point(self):
        if isinstance(self.additionalValue, str):
            self.additionalValue = float(self.additionalValue.replace(",", "."))
        if isinstance(self.value, str):
            self.value = float(self.value.replace(",", "."))

    def __post_init__(self):
        self.replace_point()


@dataclass_json
@dataclass
class Consumptions(DataClassJsonMixin):
    date: Optional[Date]
    readings: Optional[list[Readings]]
    exception: Optional[str]


@dataclass_json
@dataclass
class CostsByEnergyType(DataClassJsonMixin):
    type: Optional[str]
    value: Optional[int]
    unit: Optional[str]

    def replace_point(self):
        if isinstance(self.value, int):
            self.value = float(self.value)
        elif isinstance(self.value, str):
            self.value = float(self.value.replace(",", "."))

    def __post_init__(self):
        self.replace_point()


@dataclass_json
@dataclass
class Costs(DataClassJsonMixin):
    date: Date
    costsByEnergyType: Optional[list[CostsByEnergyType]]
    exception: Optional[str]


@dataclass_json
@dataclass
class Co2EmissionsBillingPeriods(DataClassJsonMixin):
    currentBillingPeriod: Any
    previousBillingPeriod: Any


@dataclass_json
@dataclass
class IstaResult(DataClassJsonMixin):
    consumptionUnitId: Optional[str] = None
    resident: Optional[Resident] = None
    co2Emissions: Optional[str] = None
    co2EmissionsBillingPeriods: Optional[Co2EmissionsBillingPeriods] = None
    costs: Optional[list[Costs]] = field(default_factory=list)
    consumptions: Optional[list[Consumptions]] = field(default_factory=list)


@dataclass_json
@dataclass
class CostConsumptions(DataClassJsonMixin):
    supportCode: str
    consumptionUnitId: str
    entity_id: str
    date: Date
    type: str
    consumption_additionalUnit: str
    consumption_additionalValue: float
    consumption_unit: str
    consumption_value: float
    hasCost: bool = False
    cost_unit: Optional[str] = None
    cost_value: Optional[int] = None


@dataclass_json
@dataclass
class ResultAccount(DataClassJsonMixin):
    firstName: str
    lastName: str
    email: str
    keycloakId: Optional[str]
    country: str
    locale: str
    authcode: Optional[str]
    tos: str
    tosUpdated: str
    privacy: Optional[str]
    mobileNumber: str
    transitionMobileNumber: str
    unconfirmedPhoneNumber: str
    password: Optional[str]
    enabled: bool
    consumptionUnitUuids: Optional[list[str]]
    residentTimeRangeUuids: Optional[list[str]]
    ads: bool
    marketing: bool
    fcmToken: str
    betaPhase: Optional[str]
    notificationMethod: str
    emailConfirmed: bool
    isDemo: bool
    userGroup: str
    mobileLoginStatus: str
    residentAndConsumptionUuidsMap: dict
    activeConsumptionUnit: str
    supportCode: str
    notificationMethodEmailConfirmed: bool
