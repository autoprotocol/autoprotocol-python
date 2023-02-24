import enum

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from ..container import Container, Well, WellGroup
from ..unit import Unit


WellParam = Union[Well, List[Well], WellGroup]
ACCELERATION = Union[str, Unit]
AMOUNT_CONCENTRATION = Union[str, Unit]
CONCENTRATION = Union[str, Unit]
FLOW_RATE = Union[str, Unit]
FREQUENCY = Union[str, Unit]
LENGTH = Union[str, Unit]
MASS = Union[str, Unit]
MOLES = Union[str, Unit]
TEMPERATURE = Union[str, Unit]
TIME = Union[str, Unit]
VELOCITY = Union[str, Unit]
VOLUME = Union[str, Unit]
WAVELENGTH = Union[str, Unit]
DENSITY = Union[str, Unit]
POWER = Union[str, Unit]
VOLTAGE = Union[str, Unit]


class HashableMixin:
    """Allows class to be accessed like a dictionary"""

    def __getitem__(self, item):
        return getattr(self, item)


@dataclass
class AutopickGroup(HashableMixin):
    source: WellParam
    destination: WellParam
    min_abort: int = 0


@dataclass
class DispenseColumn(HashableMixin):
    column: int
    volume: VOLUME


@dataclass
class IncubateShakingParams(HashableMixin):
    path: Union[str, Unit]
    frequency: FREQUENCY


class TimeConstraintOptimizationCost(enum.Enum):
    linear = enum.auto()
    squared = enum.auto()
    exponential = enum.auto()


@dataclass
class TimeConstraint(HashableMixin):
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
class TimeConstraintFromToDict(HashableMixin):
    mark: Dict[str, Union[Container, str, int]]
    state: TimeConstraintState


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
class OligosynthesizeOligo(HashableMixin):
    destination: Well
    sequence: str
    scale: OligosynthesizeOligoScale
    purification: OligosynthesizeOligoPurification = "standard"

    def __post_init__(self):
        allowable_scales = [
            allowable.name.strip("_") for allowable in OligosynthesizeOligoScale
        ]
        if self.scale not in allowable_scales:
            raise ValueError(f"Scale entered {self.scale} not in {allowable_scales}")
        allowable_purification = [
            option.name for option in OligosynthesizeOligoPurification
        ]
        if self.purification not in allowable_purification:
            raise ValueError(
                f"Purification entered {self.purification} not in {allowable_purification}"
            )


@dataclass
class IlluminaSeqLane(HashableMixin):
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
class AgitateModeParams(HashableMixin):
    wells: Union[List[Well], WellGroup]
    bar_shape: AgitateModeParamsBarShape
    bar_length: LENGTH

    def __post_init__(self):
        allowable_bar_shape = [option.name for option in AgitateModeParamsBarShape]
        if self.bar_shape not in allowable_bar_shape:
            raise ValueError(
                f"bar_shape entered {self.bar_shape} not in {allowable_bar_shape}"
            )


@dataclass
class ThermocycleTemperature(HashableMixin):
    duration: TIME
    temperature: TEMPERATURE
    read: bool = field(default=False)


@dataclass
class TemperatureGradient(HashableMixin):
    top: TEMPERATURE
    bottom: TEMPERATURE


@dataclass
class ThermocycleTemperatureGradient(HashableMixin):
    duration: TIME
    gradient: TemperatureGradient
    read: bool = field(default=False)


@dataclass
class PlateReaderIncubateBefore(HashableMixin):
    duration: TIME
    shake_amplitude: Optional[LENGTH] = field(default=None)
    shake_orbital: Optional[bool] = field(default=None)
    shaking: Optional[IncubateShakingParams] = field(default=None)


@dataclass
class PlateReaderPositionZManual(HashableMixin):
    manual: LENGTH


@dataclass
class PlateReaderPositionZCalculated(HashableMixin):
    calculated_from_wells: List[Well]


@dataclass
class GelPurifyBandSizeRange(HashableMixin):
    min_bp: int
    max_bp: int


@dataclass
class GelPurifyBand(HashableMixin):
    elution_buffer: str
    elution_volume: Union[str, Unit]
    destination: Well
    min_bp: Optional[int]
    max_bp: Optional[int]
    band_size_range: Optional[GelPurifyBandSizeRange]


@dataclass
class GelPurifyExtract(HashableMixin):
    source: Well
    band_list: List[GelPurifyBand]
    lane: Optional[int] = field(default=None)
    gel: Optional[int] = field(default=None)


class FlowCytometryChannelTriggerLogicEnum(enum.Enum):
    and_ = enum.auto()
    or_ = enum.auto()


@dataclass
class FlowCytometryChannelTriggerLogic(HashableMixin):
    value: FlowCytometryChannelTriggerLogicEnum

    def __post_init__(self):
        trigger_modes = ("and_", "or_")
        if self.value is not None and self.value not in trigger_modes:
            raise ValueError(f"trigger_logic must be one of {trigger_modes}.")


@dataclass
class FlowCytometryChannelMeasurements(HashableMixin):
    area: Optional[bool] = None
    height: Optional[bool] = None
    width: Optional[bool] = None


@dataclass
class FlowCytometryChannelEmissionFilter(HashableMixin):
    channel_name: str
    shortpass: WAVELENGTH = None
    longpass: WAVELENGTH = None


@dataclass
class FlowCytometryChannel(HashableMixin):
    emission_filter: FlowCytometryChannelEmissionFilter
    detector_gain: VOLTAGE
    measurements: Optional[FlowCytometryChannelMeasurements] = None
    trigger_threshold: Optional[int] = None
    trigger_logic: Optional[FlowCytometryChannelTriggerLogic] = None


@dataclass()
class FlowCytometryCollectionConditionStopCriteria(HashableMixin):
    volume: Optional[VOLUME] = None
    events: Optional[int] = None
    time: Optional[TIME] = None


@dataclass
class FlowCytometryLaser(HashableMixin):
    channels: List[FlowCytometryChannel]
    excitation: Optional[WAVELENGTH] = field(default=None)
    power: Optional[POWER] = field(default=None)
    area_scaling_factor: Optional[int] = field(default=None)


@dataclass
class FlowCytometryCollectionCondition(HashableMixin):
    acquisition_volume: Union[str, Unit]
    flowrate: Union[str, Unit]
    wait_time: Union[str, Unit]
    mix_cycles: int
    mix_volume: Union[str, Unit]
    rinse_cycles: int
    stop_criteria: Optional[FlowCytometryCollectionConditionStopCriteria]


@dataclass
class FlowAnalyzeChannelVoltageRange(HashableMixin):
    low: Union[str, Unit]
    high: Union[str, Unit]


@dataclass
class FlowAnalyzeChannel(HashableMixin):
    voltage_range: FlowAnalyzeChannelVoltageRange
    area: bool
    height: bool
    weight: bool


@dataclass
class FlowAnalyzeNegControls(HashableMixin):
    well: Well
    volume: Union[str, Unit]
    channel: str
    captured_events: Optional[int] = field(default=None)


@dataclass
class FlowAnalyzeSample(HashableMixin):
    well: Well
    volume: Union[str, Unit]
    captured_events: int


@dataclass
class FlowAnalyzeColors(HashableMixin):
    name: str
    emission_wavelength: Union[str, Unit]
    excitation_wavelength: Union[str, Unit]
    voltage_range: FlowAnalyzeChannelVoltageRange
    area: bool = field(default=True)
    height: bool = field(default=False)
    weight: bool = field(default=False)


@dataclass(frozen=True)
class FlowAnalyzePosControlsMinimizeBleed(HashableMixin):
    from_: FlowAnalyzeColors
    to: FlowAnalyzeColors


@dataclass
class FlowAnalyzePosControls(HashableMixin):
    well: Well
    volume: Union[str, Unit]
    channel: str
    minimize_bleed: List[FlowAnalyzePosControlsMinimizeBleed]
    captured_events: Optional[int] = field(default=None)


@dataclass
class SpectrophotometryShakeBefore(HashableMixin):
    duration: TIME
    frequency: Optional[Union[str, Unit]] = field(default=None)
    path: Optional[str] = field(default=None)
    amplitude: Optional[Union[str, Unit]] = field(default=None)


class EvaporateModeParamsGas(enum.Enum):
    nitrogen = enum.auto()
    argon = enum.auto()
    helium = enum.auto()


@dataclass
class EvaporateModeParams(HashableMixin):
    gas: EvaporateModeParamsGas
    vortex_speed: Union[str, Unit]
    blow_rate: Union[str, Unit]


class EvaporateMode(enum.Enum):
    rotary = enum.auto()
    centrifugal = enum.auto()
    vortex = enum.auto()
    blowdown = enum.auto()


@dataclass
class SpeElute(HashableMixin):
    loading_flowrate: Union[str, Unit]
    resource_id: str
    settle_time: Union[str, Unit]
    volume: Union[str, Unit]
    flow_pressure: Union[str, Unit]
    destination_well: Well
    processing_time: Union[str, Unit]


@dataclass
class SpeLoadSample(HashableMixin):
    volume: Union[str, Unit]
    loading_flowrate: Union[str, Unit]
    settle_time: Optional[bool]
    processing_time: Union[str, Unit]
    flow_pressure: Union[str, Unit]
    resource_id: Optional[str] = field(default=None)
    destination_well: Optional[Well] = field(default=None)
    is_elute: bool = field(default=False)


@dataclass
class SpeParams(HashableMixin):
    volume: Union[str, Unit]
    loading_flowrate: Union[str, Unit]
    settle_time: Optional[bool]
    processing_time: Union[str, Unit]
    flow_pressure: Union[str, Unit]
    resource_id: Optional[str] = field(default=None)
    is_sample: bool = field(default=False)
    destination_well: Optional[Well] = field(default=None)


class ImageMode(enum.Enum):
    top = enum.auto()
    bottom = enum.auto()
    side = enum.auto()


@dataclass
class ImageExposure(HashableMixin):
    shutter_speed: Optional[Unit] = field(default=None)
    iso: Optional[float] = field(default=None)
    aperture: Optional[float] = field(default=None)


@dataclass
class DispenseNozzlePosition(HashableMixin):
    position_x: LENGTH
    position_y: LENGTH
    position_z: LENGTH


@dataclass
class DispenseShape(HashableMixin):
    rows: int
    columns: int
    format: str


@dataclass
class DispenseShakeAfter(HashableMixin):
    duration: Optional[TIME] = field(default=None)
    frequency: Optional[FREQUENCY] = field(default=None)
    path: Optional[str] = field(default=None)
    amplitude: Optional[LENGTH] = field(default=None)


class SonicateModeParamsBathSampleHolder(enum.Enum):
    suspender = enum.auto()
    perforated_container = enum.auto()
    solid_container = enum.auto()


@dataclass
class SonicateModeParamsBath(HashableMixin):
    sample_holder: SonicateModeParamsBathSampleHolder
    power: POWER


@dataclass
class SonicateModeParamsHorn(HashableMixin):
    duty_cycle: float
    power: LENGTH


class SonicateMode(enum.Enum):
    bath = enum.auto()
    horn = enum.auto()
