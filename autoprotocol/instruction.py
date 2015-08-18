import json
from .pipette_tools import assign


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
    reagent : str
        Reagent to be dispensed to columns in container.
    columns : list
        Columns to be dispensed to, in the form of a list of dicts specifying
        the column number and the volume to be dispensed to that column.
        Columns are indexed from 0.
        [{"column": <column num>, "volume": <volume>}, ...]

    """
    def __init__(self, ref, reagent, columns, speed):
        disp = {
                "op": "dispense",
                "object": ref,
                "reagent": reagent,
                "columns": columns
        }
        assign(disp, "x_speed_percentage", speed)

        super(Dispense, self).__init__(disp)

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

    To specify a melting curve, all four melting-relevant parameters must have
    a value.

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
    dyes : dict, optional
        Dictionary mapping dye types to the wells they're used in
    melting_start: str, Unit
        Temperature at which to start the melting curve.
    melting_end: str, Unit
        Temperature at which to end the melting curve.
    melting_increment: str, Unit
        Temperature by which to increment the melting curve. Accepted increment
        values are between 0.1 and 9.9 degrees celsius.
    melting_rate: str, Unit
        Specifies the duration of each temperature step in the melting curve.

    Raises
    ------
    ValueError
        If one of dataref and dyes is specified but the other isn't.
    ValueError
        If all melting curve-related parameters are specified but dyes isn't.
    ValueError
        If some melting curve-related parameteres are specified but not all of
        them.
    ValueError
        If invalid dyes are supplied.

    """
    CHANNEL1_DYES  = ["FAM","SYBR"]
    CHANNEL2_DYES  = ["VIC","HEX","TET","CALGOLD540"]
    CHANNEL3_DYES  = ["ROX","TXR","CALRED610"]
    CHANNEL4_DYES  = ["CY5","QUASAR670"]
    CHANNEL5_DYES  = ["QUASAR705"]
    CHANNEL_DYES   = [CHANNEL1_DYES, CHANNEL2_DYES, CHANNEL3_DYES, CHANNEL4_DYES, CHANNEL5_DYES]
    AVAILABLE_DYES = [dye for channel_dye in CHANNEL_DYES for dye in channel_dye]

    def __init__(self, ref, groups, volume="25:microliter", dataref=None,
                 dyes=None, melting_start=None, melting_end=None,
                 melting_increment=None, melting_rate=None):
        instruction = {
            "op": "thermocycle",
            "object": ref,
            "groups": groups,
            "volume": volume
        }

        melting_params = [melting_start, melting_end, melting_increment,
                          melting_rate]
        melting = sum([1 for m in melting_params if not m])

        if (dyes and not dataref) or (dataref and not dyes):
            raise ValueError("You must specify both a dataref name and the dyes"
                             " to use for qPCR")
        if melting == 0:
            if not dyes:
                raise ValueError("A melting step requires a valid dyes object")
            instruction["melting"] = {
                "start": melting_start,
                "end": melting_end,
                "increment": melting_increment,
                "rate": melting_rate
            }
        elif melting < 4 and melting >= 1:
            raise ValueError('To specify a melt curve, you must specify values '
                             'for melting_start, melting_end, '
                             'melting_increment and melting_rate')
        else:
            pass

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
                           [set(well_map[k]) for k in well_map])
        if Thermocycle.find_invalid_dyes(dye_names):
            raise ValueError("thermocycle instruction supplied the following "
                             "invalid dyes: %s" % ", ".join(Thermocycle.find_invalid_dyes(dye_names)))
        dye_map = {dye: [] for dye in dye_names}
        for well in well_map:
            dyes = well_map[well]
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
    WHERE = ["ambient", "warm_30", "warm_37", "cold_4", "cold_20", "cold_80"]

    def __init__(self, ref, where, duration, shaking=False, co2=0):
        if where not in self.WHERE:
            raise ValueError("Specified `where` not contained in: %s" % ", ".join(self.WHERE))
        if where == "ambient" and shaking:
            raise ValueError("Shaking is not possible for ambient incubation")
        super(Incubate, self).__init__({
            "op": "incubate",
            "object": ref,
            "where": where,
            "duration": duration,
            "shaking": shaking,
            "co2_percent": co2
        })


class SangerSeq(Instruction):
    """
    Send the indicated wells of the container specified for Sanger sequencing.
    The specified wells should already contain the appropriate mix for
    sequencing, including primers and DNA according to the instructions
    provided by the vendor.

    Parameters
    ----------
    cont : Container, str
      Container with well(s) that contain material to be sequenced.
    wells : list of str
      Well indices of the container that contain appropriate materials to be
      sent for sequencing.
    dataref : str
      Name of sequencing dataset that will be returned.

    """
    def __init__(self, obj, wells, dataref, type, primer):
        seq = {
            "op": "sanger_sequence",
            "type": type,
            "object": obj,
            "wells": wells,
            "dataref": dataref
        }
        if primer and type == "rca":
            seq["primer"] = primer
        super(SangerSeq, self).__init__(seq)


class GelSeparate(Instruction):
    """
    Separate nucleic acids on an agarose gel.

    Parameters
    ----------
    ref : Ref, str
        Container containing samples to gel Separate
    matrix : str
        Agarose concentration and number of wells on gel used for separation
    ladder : str
        Size range of ladder to be used to compare band size to
    duration : Unit, str
        Length of time to run gel separation
    dataref : str
        Name of dataset containing fragment sizes returned

    """

    def __init__(self, wells, volume, matrix, ladder, duration, dataref):
        super(GelSeparate, self).__init__({
            "op": "gel_separate",
            "objects": wells,
            "volume": volume,
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
    def __init__(self, ref, type="ultra-clear"):
        super(Seal, self).__init__({
            "op": "seal",
            "object": ref,
            "type": type
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
    lid : {"standard", "universal", "low_evaporation"}, optional
        Type of lid to cover container with

    """
    LIDS = ["standard", "universal", "low_evaporation"]

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


class FlowAnalyze(Instruction):
    """
    Perform flow cytometry.The instruction will be executed within the voltage
    range specified for each channel, optimized for the best sample
    separation/distribution that can be achieved within these limits. The
    vendor will specify the device that this instruction is executed on and
    which excitation and emission spectra are available. At least one negative
    control is required, which will be used to define data acquisition
    parameters as well as to determine any autofluorescent properties for the
    sample set. Additional negative positive control samples are optional.
    Positive control samples will be used to optimize single color signals and,
    if desired, to minimize bleed into other channels.


    For each sample this instruction asks you to specify the `volume` and/or
    `captured_events`. Vendors might also require `captured_events` in case
    their device does not support volumetric sample intake. If both conditions
    are supported, the vendor will specify if data will be collected only until
    the first one is met or until both conditions are fulfilled.

    Example Usage:


    Autoprotocol Output:

    Parameters
    ----------
    dataref : str
        Name of flow analysis dataset generated.
    FSC : dict
        Dictionary containing FSC channel parameters in the form of:

        .. code-block:: json

            {
              "voltage_range": {
                "low": "230:volt",
                "high": "280:volt"
                },
              "area": true,             //default: true
              "height": true,           //default: true
              "weight": false           //default: false
            }

    SSC : dict
        Dictionary of SSC channel parameters in the form of:

        .. code-block:: json

            {
              "voltage_range": {
                "low": <voltage>,
                "high": <voltage>"
                },
              "area": true,             //default: true
              "height": true,           //default: false
              "weight": false           //default: false
            }

    neg_controls : list of dicts
        List of negative control wells in the form of:

        .. code-block:: json

            {
                "well": well,
                "volume": volume,
                "captured_events": integer,     // optional, default infinity
                "channel": [channel_name]
            }

        at least one negative control is required.
    samples : list of dicts
        List of samples in the form of:

        .. code-block:: json

            {
                "well": well,
                "volume": volume,
                "captured_events": integer,     // optional, default infinity
            }

        at least one sample is required
    colors : list of dicts, optional
        Optional list of colors in the form of:

        .. code-block:: json

        [{
          "name": "FitC",
          "emission_wavelength": "495:nanometer",
          "excitation_wavelength": "519:nanometer",
          "voltage_range": {
            "low": <voltage>,
            "high": <voltage>
          },
          "area": true,             //default: true
          "height": false,          //default: false
          "weight": false           //default: false
        }, ... ]


    pos_controls : list of dicts, optional
        Optional list of positive control wells in the form of:

        .. code-block:: json

            [{
                "well": well,
                "volume": volume,
                "captured_events": integer,     // optional, default infinity
                "channel": [channel_name],
                "minimize_bleed": [{            // optional
                  "from": color,
                  "to": [color]
                }, ...
            ]

    """
    def __init__(self,
                 dataref,
                 FSC,
                 SSC,
                 neg_controls,
                 samples,
                 colors=None,
                 pos_controls=None):
        flow_instr = {
                "op": "flow_analyze",
                "dataref": dataref,
                "channels": {}
            }
        assert FSC and SSC, "You must include parameters for FSC and SSC channels."
        flow_instr["channels"]["FSC"] = FSC
        flow_instr["channels"]["SSC"] = SSC
        flow_instr["negative_controls"] = neg_controls
        flow_instr["samples"] = samples
        if colors:
            flow_instr["channels"]["colors"] = colors
        if pos_controls:
            flow_instr["positive_controls"] = pos_controls

        super(FlowAnalyze, self).__init__(flow_instr)


class Oligosynthesize(Instruction):
    """
    Parameters
    ----------
    oligos : list of dicts
        List of oligonucleotides to synthesize.  Each dictionary should
        contain the oligo's sequence, destination, scale and purification

        .. code-block:: json

            [
                {
                  "destination": "my_plate/A1",
                  "sequence": "GATCRYMKSWHBVDN",
                    // - standard IUPAC base codes
                    // - IDT also allows rX (RNA), mX (2' O-methyl RNA), and
                    //   X*/rX*/mX* (phosphorothioated)
                    // - they also allow inline annotations for modifications,
                    //   eg "GCGACTC/3Phos/" for a 3' phosphorylation
                    //   eg "aggg/iAzideN/cgcgc" for an internal modification
                  "scale": "25nm" | "100nm" | "250nm" | "1um",
                  "purification": "standard" | "page" | "hplc",
                    // default: standard
                },
                ...
            ]
    """
    def __init__(self, oligos):
        super(Oligosynthesize, self).__init__({
                "op": "oligosynthesize",
                "oligos": oligos
            })


class Spread(Instruction):
    """
    Spread the specified volume of the source aliquot across the surace of the
    agar contained in the object container

    Parameters
    ----------
    source : str, Well
        Source of material to spread on agar
    dest : str, Well
        Reference to destination location (plate containing agar)
    volume : str, Unit
        Volume of source material to spread on agar

    """
    def __init__(self, source, dest, volume):
        super(Spread, self).__init__({
            "op": "spread",
            "from": source,
            "to": dest,
            "volume": volume
        })


class Autopick(Instruction):
    """
    Pick at least `min_count` colonies from the location specified in "from" to
    the location(s) specified in "to" in the order that they are specified
    until there are no more colonies available. If there are fewer than
    `min_count` colonies detected, the instruction will fail.

    Parameters
    ----------
    source : str, Well
        Reference to plate containing agar and colonies to pick
    dests : list of str, list of Well
        List of destination(s) for picked colonies
    min_count : int, optional
        Minimum number of colonies to detect in order to continue with
        autopicking

    """
    def __init__(self, source, dests, min_count, criteria, dataref):
        pick = {
            "op": "autopick",
            "from": source,
            "to": dests,
            "min_colony_count": min_count,
            "dataref": dataref
        }
        if criteria:
            pick["criteria"] = criteria

        super(Autopick, self).__init__(pick)

class ImagePlate(Instruction):
    """
    Capture an image of the specified container.

    Parameters
    ----------
    ref : str
        Container to take image of
    mode : str
        Imaging mode (currently supported: "top")
    dataref : str
        Name of data reference of resulting image

    """
    def __init__(self, ref, mode, dataref):
        super(ImagePlate, self).__init__({
            "op": "image_plate",
            "object": ref,
            "mode": mode,
            "dataref": dataref
            })

class Provision(Instruction):
    """
    Provision a commercial resource from a catalog into the specified
    destination well(s).  A new tip is used for each destination well
    specified to avoid contamination.

    Parameters
    ----------
    resource_id : str
      Resource ID from catalog.
    dests : Well, WellGroup
      Destination(s) for specified resource.
    volumes : str, Unit, list of str, list of Unit
      Volume(s) to transfer of the resource to each destination well.  If
      one volume of specified, each destination well recieve that volume of
      the resource.  If destinations should recieve different volumes, each
      one should be specified explicitly in a list matching the order of the
      specified destinations.

    Raises
    ------
    TypeError
      If resource_id is not a string.
    RuntimeError
      If length of the list of volumes specified does not match the number of
      destination wells specified.
    TypeError
      If volume is not specified as a string or Unit (or a list of either)

    """
    def __init__(self, resource_id, dests):
        super(Provision, self).__init__({
            "op": "provision",
            "resource_id": resource_id,
            "to": dests
            })

class FlashFreeze(Instruction):
    """
    Flash freeze the contents of the specified container by submerging it in
    liquid nitrogen for the specified amount of time.

    Parameters
    ----------
    container : Container, str
        Container to be flash frozen.
    duration : str, Unit
        Duration to submerge specified container in liquid nitrogen.

    """

    def __init__(self, container, duration):
        super(FlashFreeze, self).__init__({
            "op": "flash_freeze",
            "object": container,
            "duration": duration
        })

class Stamp(Instruction):
    def __init__(self, transfers):
        super(Stamp, self).__init__({
            "op": "stamp",
            "transfers": transfers
         })
