from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class ServicesComp(DataClassJsonMixin):
    Id: int
    DecPos: int
    TotalNow: int
    CurMeters: list[CurMeters]


@dataclass_json
@dataclass
class UserVauluesServicesComp(ServicesComp):
    TotalPrevious: int
    TotalDiffperc: int


@dataclass_json
@dataclass
class BillingPeriods(DataClassJsonMixin):
    y: str
    s: str
    e: str


@dataclass_json
@dataclass
class Billingservices(DataClassJsonMixin):
    Id: int
    Description: str
    Unit: str
    MeterType: str


@dataclass_json
@dataclass
class CurConsumption(DataClassJsonMixin):
    CurStart: str
    CurEnd: str
    CompStart: str
    CompEnd: str
    Billingservices: list[Billingservices]
    BillingPeriods: list[BillingPeriods]
    ServicesComp: list[UserVauluesServicesComp]


@dataclass_json
@dataclass
class Cus(DataClassJsonMixin):
    Cuid: str
    Adress: str
    Zip: str
    City: str
    DateStart: str
    curConsumption: CurConsumption


@dataclass_json
@dataclass
class UserValues(DataClassJsonMixin):
    DisplayName: str
    JWT: str
    Cus: list[Cus]


#########################


@dataclass_json
@dataclass
class CurMeters(DataClassJsonMixin):
    MeterId: int
    serviceId: int
    BillingPeriodId: int
    RadNr: int
    Order: int
    Position: Optional[str]
    ArtNr: int
    MeterNr: Optional[int]
    TransferLoss: float
    cFactor: Optional[int]
    CalcFactor: Optional[int]
    Multiply: Optional[int]
    Reduction: Optional[float]
    BsDate: str
    BeginValue: float
    EsDate: str
    EndValue: float
    CValue: float
    CCValue: float
    CCDValue: int
    DecPos: int


@dataclass_json
@dataclass
class ConsumptionValues(DataClassJsonMixin):
    CurStart: str
    CurEnd: str
    JWT: str
    ServicesComp: list[ServicesComp]
