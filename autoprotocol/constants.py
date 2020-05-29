"""
Constants used in protocol design, specification, and checking

    :copyright: 2020 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""
from .unit import Unit

SBS_FORMAT_SHAPES = {
    "SBS24": {"rows": 4, "columns": 6},
    "SBS96": {"rows": 8, "columns": 12},
    "SBS384": {"rows": 16, "columns": 24},
}

AGAR_CLLD_THRESHOLD = Unit("0.009740:picofarad") * 15

# Golden ratio spiral that defines x, y positions for spreading
SPREAD_PATH = [
    (0.0, 0.0),
    (0.10000000000000135, -4.483913240704851e-15),
    (0.17369776655924885, 0.11903209316893543),
    (0.09345745464575225, 0.2801577967175178),
    (-0.1256054634972831, 0.3004417286504315),
    (-0.2822713900063183, 0.09294284318097315),
    (-0.17386673790740076, -0.18678636767001222),
    (0.16035272968830555, -0.24921510688558246),
    (0.4163118827546255, 0.031649472514483606),
    (0.30129913903129757, 0.4355950985351607),
    (-0.14116669150904404, 0.5613885355827714),
    (-0.5105937071014001, 0.22445578242491684),
    (-0.41123474922617687, -0.3063245841015375),
    (0.12965691965919526, -0.5156955527920548),
    (0.6243159222654036, -0.14191423819668741),
    (0.563207308766221, 0.5152506858187523),
]

MEASUREMENT_MODES = ["mass", "volume"]

VOLUMETRIC_UNITS = ["liter", "milliliter", "microliter"]

MASS_UNITS = ["gram", "milligram", "microgram"]
