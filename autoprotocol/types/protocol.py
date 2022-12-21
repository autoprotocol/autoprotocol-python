import enum

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from ..builders import (
    FlowCytometryChannel,
    FlowCytometryCollectionConditionStopCriteria,
    GelPurifyBand,
)
from ..container import Container, Well, WellGroup
from ..unit import Unit


WellParam = Union[Well, List[Well], WellGroup]


@dataclass
class AutopickGroup:
    source: WellParam
    destination: WellParam
    min_abort: int = 0


@dataclass
class DispenseColumn:
    column: int
    volume: Union[str, Unit]


@dataclass
class IncubateShakingParams:
    path: Union[str, Unit]
    frequency: Union[str, Unit]


class TimeConstraintOptimizationCost(enum.Enum):
    linear = enum.auto()
    squared = enum.auto()
    exponential = enum.auto()


@dataclass(frozen=False)
class TimeConstraint:
    from_: Union[int, Container]
    to: Union[int, Container] = None
    less_than: Optional[Unit] = None
    more_than: Optional[Unit] = None
    ideal: Optional[Union[str, Unit]] = None
    optimization_cost: TimeConstraintOptimizationCost = None


class TimeConstraintState:
    start = enum.auto()
    end = enum.auto()


@dataclass
class TimeConstraintFromToDict:
    mark: Dict[str, Union[Container, str, int]]
    state: TimeConstraintState


class OligosynthesizeOligoPurification(enum.Enum):
    standard = enum.auto()
    page = enum.auto()
    hplc = enum.auto()


@dataclass
class OligosynthesizeOligo:
    destination: Well
    sequence: str
    scale: str
    purification: OligosynthesizeOligoPurification = "standard"

    def __post_init__(self):
        allowable_scales = ["25nm", "100nm", "250nm", "1um"]
        if self.scale not in allowable_scales:
            raise ValueError(f"Scale entered {self.scale} not in {allowable_scales}")


@dataclass
class IlluminaSeqLane:
    object: Well
    library_concentration: float


@dataclass
class AgitateModeParams:
    wells: Union[List[Well], WellGroup]
    bar_shape: str
    bar_length: Union[str, Unit]


@dataclass
class ThermocycleTemperature:
    duration: Union[str, Unit]
    temperature: Union[str, Unit]
    read: bool = field(default=False)


@dataclass
class TemperatureGradient:
    top: Union[str, Unit]
    bottom: Union[str, Unit]


@dataclass
class ThermocycleTemperatureGradient:
    duration: Union[str, Unit]
    gradient: TemperatureGradient
    read: bool = field(default=False)


@dataclass
class PlateReaderIncubateBeforeShaking:
    amplitude: Union[str, Unit]
    orbital: Union[str, Unit]


@dataclass
class PlateReaderIncubateBefore:
    duration: Unit
    shake_amplitude: Optional[Union[str, Unit]]
    shake_orbital: Optional[bool]
    shaking: Optional[IncubateShakingParams] = None


@dataclass
class PlateReaderPositionZManual:
    manual: Unit


@dataclass
class PlateReaderPositionZCalculated:
    calculated_from_wells: List[Well]


@dataclass
class GelPurifyExtract:
    source: Well
    band_list: List[GelPurifyBand]
    lane: Optional[int] = None
    gel: Optional[int] = None


@dataclass
class FlowCytometryLaser:
    channels: List[FlowCytometryChannel]
    excitation: Union[str, Unit] = None
    power: Union[str, Unit] = None
    area_scaling_factor: Optional[int] = None


@dataclass
class FlowCytometryCollectionCondition:
    acquisition_volume: Union[str, Unit]
    flowrate: Union[str, Unit]
    wait_time: Union[str, Unit]
    mix_cycles: int
    mix_volume: Union[str, Unit]
    rinse_cycles: int
    stop_criteria: Optional[FlowCytometryCollectionConditionStopCriteria]


@dataclass
class FlowAnalyzeChannelVoltageRange:
    low: Union[str, Unit]
    high: Union[str, Unit]


@dataclass
class FlowAnalyzeChannel:
    voltage_range: FlowAnalyzeChannelVoltageRange
    area: bool
    height: bool
    weight: bool


@dataclass
class FlowAnalyzeNegControls:
    well: Well
    volume: Union[str, Unit]
    channel: str
    captured_events: Optional[int] = None


@dataclass
class FlowAnalyzeSample:
    well: Well
    volume: Union[str, Unit]
    captured_events: int


@dataclass
class FlowAnalyzeColors:
    name: str
    emission_wavelength: Union[str, Unit]
    excitation_wavelength: Union[str, Unit]
    voltage_range: FlowAnalyzeChannelVoltageRange
    area: bool = field(default=True)
    height: bool = field(default=False)
    weight: bool = field(default=False)


@dataclass
class FlowAnalyzePosControlsMinimizeBleed:
    from_: FlowAnalyzeColors
    to: FlowAnalyzeColors


@dataclass
class FlowAnalyzePosControls:
    well: Well
    volume: Union[str, Unit]
    channel: str
    minimize_bleed: List[FlowAnalyzePosControlsMinimizeBleed]
    captured_events: Optional[int] = None


@dataclass
class SpectrophotometryShakeBefore:
    duration: Union[str, Unit]
    frequency: Optional[Union[str, Unit]] = None
    path: Optional[str] = None
    amplitude: Optional[Union[str, Unit]] = None


class EvaporateModeParamsGas(enum.Enum):
    nitrogen = enum.auto()
    argon = enum.auto()
    helium = enum.auto()


@dataclass
class EvaporateModeParams:
    gas: EvaporateModeParamsGas
    vortex_speed: Union[str, Unit]
    blow_rate: Union[str, Unit]


class EvaporateMode(enum.Enum):
    rotary = enum.auto()
    centrifugal = enum.auto()
    vortex = enum.auto()
    blowdown = enum.auto()


@dataclass
class SpeElute:
    loading_flowrate: Union[str, Unit]
    resource_id: str
    settle_time: Union[str, Unit]
    volume: Union[str, Unit]
    flow_pressure: Union[str, Unit]
    destination_well: Well
    processing_time: Union[str, Unit]


@dataclass
class SpeLoadSample:
    volume: Union[str, Unit]
    loading_flowrate: Union[str, Unit]
    settle_time: Optional[bool]
    processing_time: Union[str, Unit]
    flow_pressure: Union[str, Unit]
    resource_id: Optional[str] = None
    destination_well: Optional[Well] = None
    is_elute: bool = field(default=False)


@dataclass
class SpeParams:
    volume: Union[str, Unit]
    loading_flowrate: Union[str, Unit]
    settle_time: Optional[bool]
    processing_time: Union[str, Unit]
    flow_pressure: Union[str, Unit]
    resource_id: Optional[str] = None
    is_sample: bool = field(default=False)
    destination_well: Optional[Well] = None


class ImageMode(enum.Enum):
    top = enum.auto()
    bottom = enum.auto()
    side = enum.auto()


@dataclass
class ImageExposure:
    shutter_speed: Optional[Unit] = None
    iso: Optional[float] = None
    aperture: Optional[float] = None


@dataclass
class DispenseNozzlePosition:
    position_x: Unit
    position_y: Unit
    position_z: Unit


@dataclass
class DispenseShape:
    rows: int
    columns: int
    format: str


@dataclass
class DispenseShakeAfter:
    duration: Optional[Union[Unit, str]] = None
    frequency: Optional[Union[Unit, str]] = None
    path: Optional[str] = None
    amplitude: Optional[Union[Unit, str]] = None
