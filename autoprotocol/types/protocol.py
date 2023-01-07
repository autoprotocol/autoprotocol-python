import enum

from dataclasses import dataclass, field
from typing import List, Optional, Union

from ..builders import (
    FlowCytometryChannel,
    FlowCytometryCollectionConditionStopCriteria,
    GelPurifyBand,
)
from ..container import Container, Well, WellGroup
from ..unit import Unit


WellParam = Union[Well, List[Well], WellGroup]
ACCELERATION = Union[str, Unit]
AMOUNT_CONCENTRATION = Union[str, Unit]
CONCENTRATION = Union[str, Unit]
FLOW_RATE = Union[str, Unit]
FREQUENCY = Union[str, Unit]  # hertz, rpm
LENGTH = Union[str, Unit]  # mm
MASS = Union[str, Unit]
MOLES = Union[str, Unit]
TEMPERATURE = Union[str, Unit]
TIME = Union[str, Unit]
VELOCITY = Union[str, Unit]
VOLUME = Union[str, Unit]
WAVELENGTH = Union[str, Unit]  # nanometer
DENSITY = Union[str, Unit]
POWER = Union[str, Unit]
PRESSURE = Union[str, Unit]  # bar
VOLTAGE = Union[str, Unit]  # voltage


@dataclass
class AutopickGroup:
    source: WellParam
    destination: WellParam
    min_abort: int = 0


@dataclass
class DispenseColumn:
    column: int
    volume: VOLUME


@dataclass
class IncubateShakingParams:
    path: Union[str, Unit]
    frequency: FREQUENCY


class TimeConstraintOptimizationCost(enum.Enum):
    linear = enum.auto()
    squared = enum.auto()
    exponential = enum.auto()


@dataclass(frozen=False)
class TimeConstraint:
    from_: Union[int, Container]
    to: Union[int, Container] = field(default=None)
    less_than: Optional[TIME] = field(default=None)
    more_than: Optional[TIME] = field(default=None)
    ideal: Optional[TIME] = field(default=None)
    optimization_cost: TimeConstraintOptimizationCost = field(default=None)


class TimeConstraintState(enum.Enum):
    start = enum.auto()
    end = enum.auto()


@dataclass
class TimeConstraintFromToDict:
    mark: Union[int, Container]
    state: TimeConstraintState

    def asdict(self):
        return {"mark": self.mark, "state": self.state}


class OligosynthesizeOligoPurification(enum.Enum):
    standard = enum.auto()
    page = enum.auto()
    hplc = enum.auto()


class OligosynthesizeOligoScale(enum.Enum):
    _25nm = enum.auto()
    _100nm = enum.auto()
    _250nm = enum.auto()
    _1um = enum.auto()


@dataclass
class OligosynthesizeOligo:
    destination: Well
    sequence: str
    scale: OligosynthesizeOligoScale
    purification: OligosynthesizeOligoPurification = "standard"

    def __post_init__(self):
        allowable_scales = [
            allowable.strip("_")
            for allowable in OligosynthesizeOligoScale.__dict__.get("_member_names_")
        ]
        if self.scale not in allowable_scales:
            raise ValueError(f"Scale entered {self.scale} not in {allowable_scales}")
        allowable_purification = OligosynthesizeOligoPurification.__dict__.get(
            "_member_names_"
        )
        if self.purification not in allowable_purification:
            raise ValueError(
                f"Purification entered {self.purification} not in {allowable_purification}"
            )


@dataclass
class IlluminaSeqLane:
    object: Well
    library_concentration: float


class AgitateMode(enum.Enum):
    vortex = enum.auto()
    invert = enum.auto()
    roll = enum.auto()
    stir_bar = enum.auto()


class AgitateModeParamsBarShape(enum.Enum):
    bar = enum.auto()
    cross = enum.auto()


@dataclass
class AgitateModeParams:
    wells: Union[List[Well], WellGroup]
    bar_shape: AgitateModeParamsBarShape
    bar_length: LENGTH

    def __post_init__(self):
        allowable_bar_shape = AgitateModeParamsBarShape.__dict__.get("_member_names_")
        if self.bar_shape not in allowable_bar_shape:
            raise ValueError(
                f"bar_shape entered {self.bar_shape} not in {allowable_bar_shape}"
            )


@dataclass
class ThermocycleTemperature:
    duration: TIME
    temperature: TEMPERATURE
    read: bool = field(default=False)


@dataclass
class TemperatureGradient:
    top: TEMPERATURE
    bottom: TEMPERATURE


@dataclass
class ThermocycleTemperatureGradient:
    duration: TIME
    gradient: TemperatureGradient
    read: bool = field(default=False)


@dataclass
class PlateReaderIncubateBefore:
    duration: TIME
    shake_amplitude: Optional[LENGTH] = field(default=None)
    shake_orbital: Optional[bool] = field(default=None)
    shaking: Optional[IncubateShakingParams] = field(default=None)


@dataclass
class PlateReaderPositionZManual:
    manual: LENGTH


@dataclass
class PlateReaderPositionZCalculated:
    calculated_from_wells: List[Well]


@dataclass
class GelPurifyExtract:
    source: Well
    band_list: List[GelPurifyBand]
    lane: Optional[int] = field(default=None)
    gel: Optional[int] = field(default=None)


@dataclass
class FlowCytometryLaser:
    channels: List[FlowCytometryChannel]
    excitation: WAVELENGTH = field(default=None)
    power: POWER = field(default=None)
    area_scaling_factor: Optional[int] = field(default=None)


@dataclass
class FlowCytometryCollectionCondition:
    acquisition_volume: VOLUME
    flowrate: FLOW_RATE
    wait_time: TIME
    mix_cycles: int
    mix_volume: VOLUME
    rinse_cycles: int
    stop_criteria: Optional[FlowCytometryCollectionConditionStopCriteria]


@dataclass
class FlowAnalyzeChannelVoltageRange:
    low: VOLTAGE
    high: VOLTAGE


@dataclass
class FlowAnalyzeChannel:
    voltage_range: FlowAnalyzeChannelVoltageRange
    area: bool
    height: bool
    weight: bool


@dataclass
class FlowAnalyzeNegControls:
    well: Well
    volume: VOLUME
    channel: str
    captured_events: Optional[int] = field(default=None)


@dataclass
class FlowAnalyzeSample:
    well: Well
    volume: VOLUME
    captured_events: int


@dataclass
class FlowAnalyzeColors:
    name: str
    emission_wavelength: WAVELENGTH
    excitation_wavelength: WAVELENGTH
    voltage_range: FlowAnalyzeChannelVoltageRange
    area: bool = field(default=True)
    height: bool = field(default=False)
    weight: bool = field(default=False)


@dataclass(frozen=True)
class FlowAnalyzePosControlsMinimizeBleed:
    from_: FlowAnalyzeColors
    to: FlowAnalyzeColors


@dataclass
class FlowAnalyzePosControls:
    well: Well
    volume: VOLUME
    channel: str
    minimize_bleed: List[FlowAnalyzePosControlsMinimizeBleed]
    captured_events: Optional[int] = field(default=None)


@dataclass
class SpectrophotometryShakeBefore:
    duration: TIME
    frequency: Optional[FREQUENCY] = field(default=None)
    path: Optional[str] = field(default=None)
    amplitude: Optional[LENGTH] = field(default=None)


class EvaporateModeParamsGas(enum.Enum):
    nitrogen = enum.auto()
    argon = enum.auto()
    helium = enum.auto()


@dataclass
class EvaporateModeParams:
    gas: EvaporateModeParamsGas
    vortex_speed: FREQUENCY
    blow_rate: FLOW_RATE


class EvaporateMode(enum.Enum):
    rotary = enum.auto()
    centrifugal = enum.auto()
    vortex = enum.auto()
    blowdown = enum.auto()


@dataclass
class SpeElute:
    loading_flowrate: FLOW_RATE
    resource_id: str
    settle_time: TIME
    volume: VOLUME
    flow_pressure: PRESSURE
    destination_well: Well
    processing_time: TIME


@dataclass
class SpeLoadSample:
    volume: VOLUME
    loading_flowrate: FLOW_RATE
    settle_time: TIME
    processing_time: TIME
    flow_pressure: PRESSURE
    resource_id: Optional[str] = field(default=None)
    destination_well: Optional[Well] = field(default=None)
    is_elute: bool = field(default=False)


@dataclass
class SpeParams:
    volume: VOLUME
    loading_flowrate: FLOW_RATE
    settle_time: TIME
    processing_time: TIME
    flow_pressure: PRESSURE
    resource_id: Optional[str] = field(default=None)
    is_sample: bool = field(default=False)
    destination_well: Optional[Well] = field(default=None)


class ImageMode(enum.Enum):
    top = enum.auto()
    bottom = enum.auto()
    side = enum.auto()


@dataclass
class ImageExposure:
    shutter_speed: Optional[TIME] = field(default=None)
    iso: Optional[float] = field(default=None)
    aperture: Optional[float] = field(default=None)


@dataclass
class DispenseNozzlePosition:
    position_x: LENGTH
    position_y: LENGTH
    position_z: LENGTH


@dataclass
class DispenseShape:
    rows: int
    columns: int
    format: str


@dataclass
class DispenseShakeAfter:
    duration: Optional[TIME] = field(default=None)
    frequency: Optional[FREQUENCY] = field(default=None)
    path: Optional[str] = field(default=None)
    amplitude: Optional[LENGTH] = field(default=None)


class SonicateModeParamsBathSampleHolder(enum.Enum):
    suspender = enum.auto()
    perforated_container = enum.auto()
    solid_container = enum.auto()


@dataclass
class SonicateModeParamsBath:
    sample_holder: SonicateModeParamsBathSampleHolder
    power: POWER


@dataclass
class SonicateModeParamsHorn:
    duty_cycle: float
    power: LENGTH


class SonicateMode(enum.Enum):
    bath = enum.auto()
    horn = enum.auto()
