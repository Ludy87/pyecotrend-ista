"""Dataclasses."""

from __future__ import annotations

from dataclasses import dataclass

from dataclasses_json import DataClassJsonMixin, dataclass_json


@dataclass_json
@dataclass
class AverageConsumption(DataClassJsonMixin):
    """Represents average consumption data.

    Attributes
    ----------
    averageConsumptionValue : float
        Average consumption value.
    residentConsumptionValue : float
        Resident consumption value.
    averageConsumptionPercentage : int
        Percentage of average consumption.
    residentConsumptionPercentage : int
        Percentage of resident consumption.
    additionalAverageConsumptionValue : float
        Additional average consumption value.
    additionalResidentConsumptionValue : float
        Additional resident consumption value.
    additionalAverageConsumptionPercentage : int
        Percentage of additional average consumption.
    additionalResidentConsumptionPercentage : int
        Percentage of additional resident consumption.
    """

    averageConsumptionValue: float  # noqa: N815
    residentConsumptionValue: float  # noqa: N815
    averageConsumptionPercentage: int  # noqa: N815
    residentConsumptionPercentage: int  # noqa: N815
    additionalAverageConsumptionValue: float  # noqa: N815
    additionalResidentConsumptionValue: float  # noqa: N815
    additionalAverageConsumptionPercentage: int  # noqa: N815
    additionalResidentConsumptionPercentage: int  # noqa: N815

    def replace_point(self):
        """Replace commas with periods in specific attributes."""

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
        """Post-initialization processing."""

        self.replace_point()


@dataclass_json
@dataclass
class ComparedConsumption(DataClassJsonMixin):
    """
    Represents compared consumption data.

    Attributes
    ----------
    lastYearValue : float, optional
        Last year's consumption value.
    period : Date, optional
        Period represented by month and year.
    smiley : str, optional
        Smiley indicator representing satisfaction level.
    comparedPercentage : int, optional
        Percentage comparison with another consumption value.
    comparedValue : float, optional
        Value comparison with another consumption.
    """

    lastYearValue: float | None = None  # noqa: N815
    period: Date | None = None
    smiley: str | None = None
    comparedPercentage: int | None = None  # noqa: N815
    comparedValue: float | None = None  # noqa: N815

    def replace_point(self):
        """Replace commas with periods in specific attributes."""

        for _field in self.__dataclass_fields__.values():
            if _field.name in ["lastYearValue", "comparedValue"]:
                if isinstance(getattr(self, _field.name), str):
                    setattr(self, _field.name, float(getattr(self, _field.name).replace(",", ".")))
                else:
                    setattr(self, _field.name, float(getattr(self, _field.name)))

    def __post_init__(self):
        """Post-initialization processing."""
        self.replace_point()


@dataclass_json
@dataclass
class Consumption(DataClassJsonMixin):
    """Data class representing consumption.

    Parameters
    ----------
    type : str
        Type of consumption.
    value : float
        Value of the consumption.
    unit : str
        Unit of measurement for the consumption value.
    additionalValue : float
        Additional value associated with the consumption.
    additionalUnit : str
        Unit of measurement for the additional value.
    estimated : bool
        Flag indicating if the consumption is estimated.
    comparedConsumption : ComparedConsumption, optional
        Optional comparison with another consumption instance.
    comparedCost : ComparedConsumption, optional
        Optional comparison with another cost related to consumption.
    averageConsumption : AverageConsumption, optional
        Optional average consumption data.
    """

    type: str
    value: float
    unit: str
    additionalValue: float  # noqa: N815
    additionalUnit: str  # noqa: N815
    estimated: bool
    comparedConsumption: ComparedConsumption | None  # noqa: N815
    comparedCost: ComparedConsumption | None  # noqa: N815
    averageConsumption: AverageConsumption | None  # field(default_factory=AverageConsumption)  # noqa: N815

    def replace_point(self):
        """Replace commas with periods in specific attributes."""

        for _field in self.__dataclass_fields__.values():
            if _field.name in ["value", "additionalValue"]:
                if isinstance(getattr(self, _field.name), str):
                    setattr(self, _field.name, float(getattr(self, _field.name).replace(",", ".")))

    def __post_init__(self):
        """Post-initialization processing."""

        self.replace_point()


@dataclass_json
@dataclass
class Cost(DataClassJsonMixin):
    """Data class representing cost information.

    Attributes
    ----------
    type : str
        The type of cost.
    value : int
        The numerical value of the cost.
    unit : str
        The monetary unit for the cost value.
    estimated : bool
        Indicates whether the cost is estimated or not.
    comparedCost : ComparedConsumption, optional
        Object containing compared consumption data, if available.
    """

    type: str
    value: int
    unit: str
    estimated: bool
    comparedCost: ComparedConsumption | None  # noqa: N815


@dataclass_json
@dataclass
class Date(DataClassJsonMixin):
    """Data class representing a date with month and year.

    Attributes
    ----------
    month : int
        The month of the date.
    year : int
        The year of the date.
    """

    month: int
    year: int


@dataclass_json
@dataclass
class LastValue(DataClassJsonMixin):
    """Data class representing last values.

    Attributes
    ----------
    heating : float, optional
        The last recorded heating value.
    warmwater : float, optional
        The last recorded warm water value.
    water : float, optional
        The last recorded water value.
    month : int, optional
        The month of the last recorded values.
    year : int, optional
        The year of the last recorded values.
    ww : str, optional
        Additional attribute description related to warm water.
    w : str, optional
        Additional attribute description related to water.
    h : str, optional
        Additional attribute description related to heating.
    """

    heating: float | None = None
    warmwater: float | None = None
    water: float | None = None
    month: int | None = None
    year: int | None = None
    ww: str | None = None
    w: str | None = None
    h: str | None = None


@dataclass_json
@dataclass
class LastCustomValue(DataClassJsonMixin):
    """Data class representing last custom values.

    Attributes
    ----------
    heating : float, optional
        The last recorded custom heating value.
    warmwater : float, optional
        The last recorded custom warm water value.
    water : float, optional
        The last recorded custom water value.
    month : int, optional
        The month of the last recorded custom values.
    year : int, optional
        The year of the last recorded custom values.
    ww : str, optional
        Additional warm water attribute description.
    w : str, optional
        Additional water attribute description.
    h : str, optional
        Additional heating attribute description.
    """

    heating: float | None = None
    warmwater: float | None = None
    water: float | None = None
    month: int | None = None
    year: int | None = None
    ww: str | None = None
    w: str | None = None
    h: str | None = None


@dataclass_json
@dataclass
class LastCosts(DataClassJsonMixin):
    """Data class representing last costs.

    Attributes
    ----------
    heating : float, optional
        The last recorded heating cost.
    warmwater : float, optional
        The last recorded warm water cost.
    water : float, optional
        The last recorded water cost.
    month : int, optional
        The month of the last recorded costs.
    year : int, optional
        The year of the last recorded costs.
    unit : str, optional
        The monetary unit for the costs.
    """

    heating: float | None = None
    warmwater: float | None = None
    water: float | None = None
    month: int | None = None
    year: int | None = None
    unit: str | None = None


@dataclass_json
@dataclass
class CombinedData(DataClassJsonMixin):
    """Data class representing combined data.

    Attributes
    ----------
    date : Date
        The date associated with the combined data.
    consumptions : list of Consumption
        List of consumptions associated with the combined data.
    costs : list of Cost
        List of costs associated with the combined data.
    """

    date: Date
    consumptions: list[Consumption]
    costs: list[Cost]


@dataclass_json
@dataclass
class TotalAdditionalValues(DataClassJsonMixin):
    """Data class for representing total additional values.

    Attributes
    ----------
    heating : float or None, optional
        Total additional value for heating, or None if not available. Default is None.
    warmwater : float or None, optional
        Total additional value for warm water, or None if not available. Default is None.
    water : float or None, optional
        Total additional value for water, or None if not available. Default is None.
    ww : str or None, optional
        A string representation for warm water, or None if not available. Default is None.
    w : str or None, optional
        A string representation for water, or None if not available. Default is None.
    h : str or None, optional
        A string representation for heating, or None if not available. Default is None.
    """

    heating: float | None = None
    warmwater: float | None = None
    water: float | None = None
    ww: str | None = None
    w: str | None = None
    h: str | None = None


@dataclass_json
@dataclass
class TotalAdditionalCustomValues(DataClassJsonMixin):
    """Data class for representing total additional custom values.

    Attributes
    ----------
    heating : float or None, optional
        Total additional custom value for heating, or None if not available. Default is None.
    warmwater : float or None, optional
        Total additional custom value for warm water, or None if not available. Default is None.
    water : float or None, optional
        Total additional custom value for water, or None if not available. Default is None.
    ww : str or None, optional
        A string representation for warm water, or None if not available. Default is None.
    w : str or None, optional
        A string representation for water, or None if not available. Default is None.
    h : str or None, optional
        A string representation for heating, or None if not available. Default is None.
    """

    heating: float | None = None
    warmwater: float | None = None
    water: float | None = None
    ww: str | None = None
    w: str | None = None
    h: str | None = None


@dataclass_json
@dataclass
class SumByYear(DataClassJsonMixin):
    """Data class for representing the sum of values grouped by year.

    Attributes
    ----------
    heating : dict of int to float or None, optional
        A dictionary mapping years to heating values, or None if not available. Default is None.
    warmwater : dict of int to float or None, optional
        A dictionary mapping years to warm water values, or None if not available. Default is None.
    water : dict of int to float or None, optional
        A dictionary mapping years to water values, or None if not available. Default is None.
    ww : str or None, optional
        A string representation for warm water, or None if not available. Default is None.
    w : str or None, optional
        A string representation for water, or None if not available. Default is None.
    h : str or None, optional
        A string representation for heating, or None if not available. Default is None.
    """

    heating: dict[int, float] | None = None
    warmwater: dict[int, float] | None = None
    water: dict[int, float] | None = None
    ww: str | None = None
    w: str | None = None
    h: str | None = None


@dataclass_json
@dataclass
class CustomRaw(DataClassJsonMixin):
    """Data class for representing custom raw data.

    Attributes
    ----------
    consum_types : list of str or None
        A list of consumption types or None if not available.
    combined_data : list of CombinedData or None
        A list of combined data entries or None if not available.
    total_additional_values : TotalAdditionalValues
        The total for additional values.
    total_additional_custom_values : TotalAdditionalCustomValues
        The total for additional custom values.
    last_value : LastValue or None
        The last value recorded or None if not available.
    last_custom_value : LastCustomValue or None
        The last custom value recorded or None if not available.
    all_dates : list of Date or None
        A list of all relevant dates or None if not available.
    sum_by_year : SumByYear
        The sum of values grouped by year.
    last_costs : LastCosts or None
        The last recorded costs or None if not available.
    last_year_compared_consumption : dict of str to ComparedConsumption or None
        A dictionary with last year's compared consumption values or None if not available.
    """

    consum_types: list[str] | None
    combined_data: list[CombinedData] | None
    total_additional_values: TotalAdditionalValues
    total_additional_custom_values: TotalAdditionalCustomValues
    last_value: LastValue | None
    last_custom_value: LastCustomValue | None
    all_dates: list[Date] | None
    sum_by_year: SumByYear
    last_costs: LastCosts | None
    last_year_compared_consumption: dict[str, ComparedConsumption] | None
