import json

'''
    :copyright: 2015 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''

class Instruction(object):
    """Base class for an instruction that is to later be encoded as JSON.

    """
    def __init__(self, data):
        super(Instruction, self).__init__()
        self.data = data
        self.__dict__.update(data)

    def json(self):
        """Return instruction object properly encoded as JSON for Autoprotocol.

        """
        return json.dumps(self.data, indent=2)


class Pipette(Instruction):
    '''
    A pipette instruction is constructed as a list of groups, executed in
    order, where each group is a transfer, distribute or mix group.  One
    disposable tip is used for each group.

    transfer:

        For each element in the transfer list, in order, aspirates the specifed
        volume from the source well and dispenses the same volume into the
        target well.

    distribute:

        Aspirates sufficient volume from the source well, then dispenses into
        each target well the volume requested, in the order specified.
        If the total volume to be dispensed exceeds the maximum tip volume
        (900 uL), you must either specify allow_carryover to allow the pipette
        to return to the source and aspirate another load, or break your group
        up into multiple distributes each of less than the maximum tip volume.
        Specifying allow_carryover means that the source well could become
        contaminated with material from the target wells, so take care to use it
        only when you're sure that contamination won't be an issue=for example,
        if the target plate is empty.

    mix:
        Mixes the specified wells, in order, by repeated aspiration and
        dispensing of the specified volume. The default mixing speed is
        50 uL/second, but you may specify a slower or faster speed.

    Well positions are given using the format :ref/:index

    '''
    def __init__(self, groups):
        super(Pipette, self).__init__({
            "op": "pipette",
            "groups": groups
        })

class Dispense(Instruction):
    """
    Dispense specified reagent to specified columns.

    Parameters
    ----------
    ref : Ref, str
        Container for reagent to be dispensed to.
    reagent : {"water", "LB", "LB-amp", "LB-kan", "SOC", "PBS"}
        Reagent to be dispensed to columns in container.
    columns : list
        Columns to be dispensed to, in the form of a list of dicts specifying
        the column number and the volume to be dispensed to that column.
        Columns are indexed from 0.
        [{"column": <column num>, "volume": <volume>}, ...]

    """
    def __init__(self, ref, reagent, columns):
        super(Dispense, self).__init__({
            "op": "dispense",
            "object": ref,
            "reagent": reagent,
            "columns": columns
        })

class Spin(Instruction):
    """
    Apply the specified amount of acceleration to a plate using a centrifuge.

    Parameters
    ----------
    ref : Ref, str
        Container to be centrifuged.
    acceleration : str
        Amount of acceleration to be applied to the container, expressed in
        units of "g" or "meter/second^2"
    duration : str
        Amount of time to apply acceleration.

    """
    def __init__(self, ref, acceleration, duration):
        super(Spin, self).__init__({
            "op": "spin",
            "object": ref,
            "acceleration": acceleration,
            "duration": duration
        })


class Thermocycle(Instruction):
    """
    Append a Thermocycle instruction to the list of instructions, with
    groups being a list of dicts in the form of:

    .. code-block:: python

        "groups": [{
            "cycles": integer,
            "steps": [{
              "duration": duration,
              "temperature": temperature,
              "read": boolean // optional (default true)
            },{
              "duration": duration,
              "gradient": {
                "top": temperature,
                "bottom": temperature
              },
              "read": boolean // optional (default true)
            }]
        }],

    Parameters
    ----------
    ref : str, Ref
        Container to be thermocycled
    groups : list of dicts
        List of thermocycling instructions formatted as above
    volume : str, Unit, optional
        Volume contained in wells being thermocycled
    dataref : str, optional
        Name of dataref representing read data if performing qPCR
    dyes : list, optional
        Dye to utilize for qPCR reading
    melting : str, Unit, optional
        Temperature at which to perform a melting curve

    Raises
    ------
    AttributeError
        if groups are not properly formatted

    """
    CHANNEL1_DYES  = ["FAM","SYBR"]
    CHANNEL2_DYES  = ["VIC","HEX","TET","CALGOLD540"]
    CHANNEL3_DYES  = ["ROX","TXR","CALRED610"]
    CHANNEL4_DYES  = ["CY5","QUASAR670"]
    CHANNEL5_DYES  = ["QUASAR705"]
    CHANNEL_DYES   = [CHANNEL1_DYES, CHANNEL2_DYES, CHANNEL3_DYES, CHANNEL4_DYES, CHANNEL5_DYES]
    AVAILABLE_DYES = [dye for channel_dye in CHANNEL_DYES for dye in channel_dye]

    def __init__(self, ref, groups, volume="25:microliter", dataref=None,
                 dyes=None, melting=None):
        instruction = {
            "op": "thermocycle",
            "object": ref,
            "groups": groups,
            "volume": volume
        }

        if (dyes and not dataref) or (dataref and not dyes):
            raise ValueError("You must specify both a dataref name and the dyes"
                             " to use for qPCR")
        elif melting and not dyes:
            raise ValueError("A melting step requires a valid dyes object")

        if melting:
            instruction["melting"] = melting
        if dyes:
            keys = dyes.keys()
            if Thermocycle.find_invalid_dyes(keys):
                dyes = Thermocycle.convert_well_map_to_dye_map(dyes)
            else:
                instruction["dyes"] = dyes

        instruction["dataref"] = dataref
        super(Thermocycle, self).__init__(instruction)

    @staticmethod
    def find_invalid_dyes(dyes):
        """
        Take a set or list of dye names and returns the set that are not valid.

        dyes - [list or set]
        """

        return set(dyes).difference(set(Thermocycle.AVAILABLE_DYES))

    @staticmethod
    def convert_well_map_to_dye_map(well_map):
        """
        Take a map of wells to the dyes it contains and returns a map of dyes to
        the list of wells that contain it.

        well_map - [{well:str}]
        """

        dye_names = reduce(lambda x, y: x.union(y),
                           [set(v) for v in well_map.itervalues()])
        if Thermocycle.find_invalid_dyes(dye_names):
            raise ValueError("thermocycle instruction supplied the following "
                             "invalid dyes: %s" % ", ".join(Thermocycle.find_invalid_dyes(dye_names)))
        dye_map = {dye: [] for dye in dye_names}
        for well, dyes in well_map.iteritems():
            for dye in dyes:
                dye_map[dye] += [well]
        return dye_map


class Incubate(Instruction):
    """
    Store a sample in a specific environment for a given duration. Once the
    duration has elapsed, the sample will be returned to the ambient environment
    until it is next used in an instruction.

    Parameters
    ----------
    ref : Ref, str
        The container to be incubated
    where : {"ambient", "warm_37", "cold_4", "cold_20", "cold_80"}
        Temperature at which to incubate specified container
    duration : Unit, str
        Length of time to incubate container
    shaking : bool, optional
        Specify whether or not to shake container if available at the specified
        temperature

    """
    WHERE = ["ambient", "warm_37", "cold_4", "cold_20", "cold_80"]

    def __init__(self, ref, where, duration, shaking=False):
        if where not in self.WHERE:
            raise ValueError("Specified `where` not contained in: %s" % ", ".join(self.WHERE))
        if where == "ambient" and shaking:
            raise ValueError("Shaking is not possible for ambient incubation")
        super(Incubate, self).__init__({
            "op": "incubate",
            "object": ref,
            "where": where,
            "duration": duration,
            "shaking": shaking
        })


class SangerSeq(Instruction):
    """
    Sequence specified object

    Parameters
    ----------
    ref : Ref, str
        Container containing samples to sequence
    dataref : str
        Name for set of sequencing data to be returned

    """
    def __init__(self, ref, dataref):
        super(SangerSeq, self).__init__({
            "op": "sangerseq",
            "object": ref,
            "dataref": dataref
        })


class GelSeparate(Instruction):
    """
    Separate nucleic acids on an agarose gel.

    Parameters
    ----------
    ref : Ref, str
        Container containing samples to gel Separate
    matrix : {'agarose(96,2.0%)', 'agarose(48,4.0%)', 'agarose(48,2.0%)', 'agarose(12,1.2%)', 'agarose(8,0.8%)'}
        Agarose concentration and number of wells on gel used for separation
    ladder : {"ladder1", "ladder2"}
        Size range of ladder to be used to compare band size to
    duration : Unit, str
        Length of time to run gel separation
    dataref : str
        Name of dataset containing fragment sizes returned

    """
    MATRICES = ['agarose(96,2.0%)', 'agarose(48,4.0%)', 'agarose(48,2.0%)',
                'agarose(12,1.2%)', 'agarose(8,0.8%)']
    LADDERS = ['ladder1', 'ladder2']

    def __init__(self, wells, matrix, ladder, duration, dataref):
        if matrix not in self.MATRICES:
            raise ValueError("specified `matrix` not contained in: %s" % ", ".join(self.MATRICES))
        if ladder not in self.LADDERS:
            raise ValueError("specified `ladder` not contained in: %s" % ", ".join(self.LADDERS))
        super(GelSeparate, self).__init__({
            "op": "gel_separate",
            "objects": wells,
            "matrix": matrix,
            "ladder": ladder,
            "duration": duration,
            "dataref": dataref
        })


class Absorbance(Instruction):
    """
    Read the absorbance for the indicated wavelength for the indicated
    wells. Append an Absorbance instruction to the list of instructions for
    this Protocol object.

    Parameters
    ----------
    ref : str, Ref
    wells : list, WellGroup
        WellGroup of wells to be measured or a list of well references in
        the form of ["A1", "B1", "C5", ...]
    wavelength : str, Unit
        wavelength of light absorbance to be read for the indicated wells
    dataref : str
        name of this specific dataset of measured absorbances
    flashes : int, optional

    """
    def __init__(self, ref, wells, wavelength, dataref, flashes=25):
        super(Absorbance, self).__init__({
            "op": "absorbance",
            "object": ref,
            "wells": wells,
            "wavelength": wavelength,
            "num_flashes": flashes,
            "dataref": dataref
        })


class Fluorescence(Instruction):
    """
    Read the fluoresence for the indicated wavelength for the indicated
    wells.  Append a Fluorescence instruction to the list of instructions
    for this Protocol object.

    Parameters
    ----------
    ref : str, Container
    wells : list, WellGroup
        WellGroup of wells to be measured or a list of well references in
        the form of ["A1", "B1", "C5", ...]
    excitation : str, Unit
        wavelength of light used to excite the wells indicated
    emission : str, Unit
        wavelength of light to be measured for the indicated wells
    dataref : str
        name of this specific dataset of measured absorbances
    flashes : int, optional

    """
    def __init__(self, ref, wells, excitation, emission, dataref, flashes=25):
        super(Fluorescence, self).__init__({
            "op": "fluorescence",
            "object": ref,
            "wells": wells,
            "excitation": excitation,
            "emission": emission,
            "num_flashes": flashes,
            "dataref": dataref
        })


class Luminescence(Instruction):
    """
    Read luminesence of indicated wells

    Parameters
    ----------
    ref : str, Container
    wells : list, WellGroup
        WellGroup or list of wells to be measured
    dataref : str

    """
    def __init__(self, ref, wells, dataref):
        super(Luminescence, self).__init__({
            "op": "luminescence",
            "object": ref,
            "wells": wells,
            "dataref": dataref
            })


class Seal(Instruction):
    """
    Seal indicated container using the automated plate sealer.

    Parameters
    ----------
    ref : Ref, str
        Container to be sealed

    """
    def __init__(self, ref):
        super(Seal, self).__init__({
            "op": "seal",
            "object": ref
        })


class Unseal(Instruction):
    """
    Remove seal from indicated container using the automated plate unsealer.

    Parameters
    ----------
    ref : Ref, str
        Container to be unsealed

    """
    def __init__(self, ref):
        super(Unseal, self).__init__({
            "op": "unseal",
            "object": ref
        })


class Cover(Instruction):
    """
    Place specified lid type on specified container

    Parameters
    ----------
    ref : str
        Container to be convered
    lid : {"standard", "universal", "low-evaporation"}, optional
        Type of lid to cover container with

    """
    LIDS = ["standard", "universal", "low-evaporation"]

    def __init__(self, ref, lid="standard"):
        if lid and lid not in self.LIDS:
            raise ValueError("%s is not a valid lid type" % lid)
        super(Cover, self).__init__({
            "op": "cover",
            "object": ref,
            "lid": lid
        })


class Uncover(Instruction):
    """
    Remove lid from specified container

    Parameters
    ----------
    ref : str
        Container to remove lid from

    """
    def __init__(self, ref):
        super(Uncover, self).__init__({
            "op": "uncover",
            "object": ref
        })
