import enum


class EvaporateBuildersValidModes(enum.Enum):
    rotate = enum.auto()
    centrifuge = enum.auto()
    vortex = enum.auto()
    blowdown = enum.auto()


class EvaporateBuildersValidGases(enum.Enum):
    nitrogen = enum.auto()
    argon = enum.auto()
    helium = enum.auto()


class EvaporateBuildersRotateParams(enum.Enum):
    flask_volume = enum.auto()
    rotation_speed = enum.auto()
    vacuum_pressure = enum.auto()
    condenser_temperature = enum.auto()


class EvaporateBuildersCentrifugeParams(enum.Enum):
    spin_acceleration = enum.auto()
    vacuum_pressure = enum.auto()
    condenser_temperature = enum.auto()


class EvaporateBuildersVortexParams(enum.Enum):
    vortex_speed = enum.auto()
    vacuum_pressure = enum.auto()
    condenser_temperature = enum.auto()


class EvaporateBuildersBlowdownParams(enum.Enum):
    gas = enum.auto()
    blow_rate = enum.auto()
    vortex_speed = enum.auto()


class LiquidHandleBuildersLiquidClasses(enum.Enum):
    air = enum.auto()
    default = enum.auto()
    viscous = enum.auto()
    protein_buffer = enum.auto()


class LiquidHandleBuildersZReferences(enum.Enum):
    well_top = enum.auto()
    well_bottom = enum.auto()
    liquid_surface = enum.auto()
    preceding_position = enum.auto()


class LiquidHandleBuildersZDetectionMethods(enum.Enum):
    capacitance = enum.auto()
    pressure = enum.auto()
    tracked = enum.auto()


class LiquidHandleBuildersDispenseModes(enum.Enum):
    air_displacement = enum.auto()
    positive_displacement = enum.auto()


class ThermocycleBuildersValidDyes(enum.Enum):
    FAM = enum.auto()
    SYBR = enum.auto()  # channel 1
    VIC = enum.auto()
    HEX = enum.auto()
    TET = enum.auto()
    CALGOLD540 = enum.auto()  # channel 2
    ROX = enum.auto()
    TXR = enum.auto()
    CALRED610 = enum.auto()  # channel 3
    CY5 = enum.auto()
    QUASAR670 = enum.auto()  # channel 4
    QUASAR705 = enum.auto()  # channel 5
    FRET = enum.auto()  # channel 6


class DispenseBuildersShakePaths(enum.Enum):
    landscape_linear = enum.auto()


class SpectrophotometryBuildersReadPositions(enum.Enum):
    top = enum.auto()
    bottom = enum.auto()


class SpectrophotometryBuildersZHeuristics(enum.Enum):
    max_mean_read_without_saturation = enum.auto()
    closest_distance_without_saturation = enum.auto()


class SpectrophotometryBuildersZReferences(enum.Enum):
    plate_bottom = enum.auto()
    plate_top = enum.auto()
    well_bottom = enum.auto()
    well_top = enum.auto()


class SpectrophotometryBuildersShakePaths(enum.Enum):
    portrait_linear = enum.auto()
    landscape_linear = enum.auto()
    cw_orbital = enum.auto()
    ccw_orbital = enum.auto()
    portrait_down_double_orbital = enum.auto()
    landscape_down_double_orbital = enum.auto()
    portrait_up_double_orbital = enum.auto()
    landscape_up_double_orbital = enum.auto()
    cw_diamond = enum.auto()
    ccw_diamond = enum.auto()
