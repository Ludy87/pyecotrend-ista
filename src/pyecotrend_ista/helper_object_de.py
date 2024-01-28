"""Dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class AverageConsumption(DataClassJsonMixin):
    averageConsumptionValue: float
    residentConsumptionValue: float
    averageConsumptionPercentage: int
    residentConsumptionPercentage: int
    additionalAverageConsumptionValue: float
    additionalResidentConsumptionValue: float
    additionalAverageConsumptionPercentage: int
    additionalResidentConsumptionPercentage: int

    def replace_point(self):
        for _field in self.__dataclass_fields__.values():
            if _field.name in [
                "averageConsumptionValue",
                "residentConsumptionValue",
                "additionalAverageConsumptionValue",
                "additionalResidentConsumptionValue",
            ]:
                if isinstance(getattr(self, _field.name), str):
                    setattr(self, _field.name, float(getattr(self, _field.name).replace(",", ".")))

    def __post_init__(self):
        self.replace_point()


@dataclass_json
@dataclass
class ComparedConsumption(DataClassJsonMixin):
    lastYearValue: Optional[float] = None
    period: Optional[Date] = None
    smiley: Optional[str] = None
    comparedPercentage: Optional[int] = None
    comparedValue: Optional[float] = None

    def replace_point(self):
        for _field in self.__dataclass_fields__.values():
            if _field.name in ["lastYearValue", "comparedValue"]:
                if isinstance(getattr(self, _field.name), str):
                    setattr(self, _field.name, float(getattr(self, _field.name).replace(",", ".")))
                else:
                    setattr(self, _field.name, float(getattr(self, _field.name)))

    def __post_init__(self):
        self.replace_point()


@dataclass_json
@dataclass
class Consumption(DataClassJsonMixin):
    type: str
    value: float
    unit: str
    additionalValue: float
    additionalUnit: str
    estimated: bool
    comparedConsumption: Optional[ComparedConsumption]
    comparedCost: Optional[ComparedConsumption]
    averageConsumption: Optional[AverageConsumption]  # field(default_factory=AverageConsumption)

    def replace_point(self):
        for _field in self.__dataclass_fields__.values():
            if _field.name in ["value", "additionalValue"]:
                if isinstance(getattr(self, _field.name), str):
                    setattr(self, _field.name, float(getattr(self, _field.name).replace(",", ".")))

    def __post_init__(self):
        self.replace_point()


@dataclass_json
@dataclass
class Cost(DataClassJsonMixin):
    type: str
    value: int
    unit: str
    estimated: bool
    comparedCost: Optional[ComparedConsumption]


@dataclass_json
@dataclass
class Date(DataClassJsonMixin):
    month: int
    year: int


@dataclass_json
@dataclass
class LastValue(DataClassJsonMixin):
    heating: Optional[float] = None
    warmwater: Optional[float] = None
    water: Optional[float] = None
    month: Optional[int] = None
    year: Optional[int] = None
    ww: Optional[str] = None
    w: Optional[str] = None
    h: Optional[str] = None


@dataclass_json
@dataclass
class LastCustomValue(DataClassJsonMixin):
    heating: Optional[float] = None
    warmwater: Optional[float] = None
    water: Optional[float] = None
    month: Optional[int] = None
    year: Optional[int] = None
    ww: Optional[str] = None
    w: Optional[str] = None
    h: Optional[str] = None


@dataclass_json
@dataclass
class LastCosts(DataClassJsonMixin):
    heating: Optional[float] = None
    warmwater: Optional[float] = None
    water: Optional[float] = None
    month: Optional[int] = None
    year: Optional[int] = None
    unit: Optional[str] = None


@dataclass_json
@dataclass
class CombinedData(DataClassJsonMixin):
    date: Date
    consumptions: list[Consumption]
    costs: list[Cost]


@dataclass_json
@dataclass
class TotalAdditionalValues(DataClassJsonMixin):
    heating: Optional[float] = None
    warmwater: Optional[float] = None
    water: Optional[float] = None
    ww: Optional[str] = None
    w: Optional[str] = None
    h: Optional[str] = None


@dataclass_json
@dataclass
class TotalAdditionalCustomValues(DataClassJsonMixin):
    heating: Optional[float] = None
    warmwater: Optional[float] = None
    water: Optional[float] = None
    ww: Optional[str] = None
    w: Optional[str] = None
    h: Optional[str] = None


@dataclass_json
@dataclass
class SumByYear(DataClassJsonMixin):
    heating: Optional[dict[int, float]] = None
    warmwater: Optional[dict[int, float]] = None
    water: Optional[dict[int, float]] = None
    ww: Optional[str] = None
    w: Optional[str] = None
    h: Optional[str] = None


@dataclass_json
@dataclass
class CustomRaw(DataClassJsonMixin):
    consum_types: Optional[list[str]]
    combined_data: Optional[list[CombinedData]]
    total_additional_values: TotalAdditionalValues
    total_additional_custom_values: TotalAdditionalCustomValues
    last_value: Optional[LastValue]
    last_custom_value: Optional[LastCustomValue]
    all_dates: Optional[list[Date]]
    sum_by_year: SumByYear
    last_costs: Optional[LastCosts]
    last_year_compared_consumption: Optional[dict[str, ComparedConsumption]]
