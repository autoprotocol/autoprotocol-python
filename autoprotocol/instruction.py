"""
Contains all the Autoprotocol Instruction objects

    :copyright: 2018 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

# pragma pylint: disable=too-few-public-methods, redefined-builtin
import json
from .builders import *  # pylint: disable=unused-wildcard-import
from functools import reduce


class Instruction(object):
    """Base class for an instruction that is to later be encoded as JSON.

    """

    def __init__(self, op, data):
        super(Instruction, self).__init__()
        self.op = op
        self.data = self._remove_empty_fields(data)
        self.__dict__.update(self.data)

    def json(self):
        """Return instruction object properly encoded as JSON for Autoprotocol.

        """
        return json.dumps(dict(op=self.op, **self.data), indent=2)

    @staticmethod
    def _remove_empty_fields(data):
        """
        Helper function to recursively search through and pop items containing
        empty dictionaries/lists or dictionaries containing fields with None
        values

        Parameters
        ----------
        data : dict or list
            Data dictionary or list to remove empty fields from

        Returns
        -------
        dict or list
            Dictionary or list without fields with None values

        """
        # We're not checking against the generic not since there are values
        # such as `0` or False which are valid.
        def filter_criteria(item):
            # Workaround for Unit equality comparison issues
            if isinstance(item, Unit):
                return False
            return item is None or item == [] or item == {}

        if isinstance(data, dict):
            return {k: Instruction._remove_empty_fields(v) for k, v in
                    data.items() if not filter_criteria(v)}
        if isinstance(data, list):
            return [Instruction._remove_empty_fields(_) for _ in data
                    if not filter_criteria(_)]
        return data


class MagneticTransfer(Instruction):
    """
    A magnetic_transfer instruction is constructed as a list of lists of
    groups, executed in order, where each group is a collect, release, dry,
    incubate, or mix sub-operation.  These sub-operations control the behavior
    of tips which can be magnetized, and a heating platform. Groups in the same
    list of groups use the same tips.

    Parameters
    ----------
    groups: list(dict)
        dict in the groups should belong to one of the following categories:

        collect:
            Collects beads from the specified "object" by raising and lowering
            magnetized tips repeatedly with an optional pause at well bottom.
        release:
            Release beads from unmagnetized tips by oscillating the tips
            vertically into and out of the "object".
        dry:
            Dry beads on magnetized tips above and outside the "object".
        incubate:
            Incubate the "object".
        mix:
            Oscillate the tips into and out of the "object"
    head_type: str
        Head-type used for this instruction

    """
    HEAD_TYPE = ["96-deep", "96-pcr"]

    def __init__(self, groups, head_type):
        if head_type not in self.HEAD_TYPE:
            raise ValueError(
                "Specified `head_type` not: %s" % ", ".join(self.HEAD_TYPE))
        super(MagneticTransfer, self).__init__(
            op="magnetic_transfer",
            data={"groups": groups, "magnetic_head": head_type}
        )


class Dispense(Instruction):

    """
    Dispense specified reagent to specified columns. Only one of reagent,
    resource_id, and reagent_source can be specified for a given instruction.

    Parameters
    ----------
    object : Container or str
        Container for reagent to be dispensed to.
    columns : list
        Columns to be dispensed to, in the form of a list of dicts specifying
        the column number and the volume to be dispensed to that column.
        Columns are indexed from 0.
        [{"column": <column num>, "volume": <volume>}, ...]
    reagent : str, optional
        Reagent to be dispensed.
    resource_id : str, optional
        Resource to be dispensed.
    reagent_source : Well, optional
        Aliquot to be dispensed from.
    step_size : str or Unit, optional
        Specifies that the dispense operation must be executed
        using a pump that has a dispensing resolution of step_size.
    flowrate : str or Unit, optional
        The rate at which the peristaltic pump should dispense in Units of
        flow rate, e.g. microliter/second.
    nozzle_position : dict, optional
        A dict represent nozzle offsets from the center of the bottom of the
        plate's well. see Dispense.builders.nozzle_position; specified as
        {"position_x": Unit, "position_y": Unit, "position_z": Unit}.
    pre_dispense : str or Unit, optional
        The volume of reagent to be dispensed per-nozzle into waste
        immediately prior to dispensing into the ref.
    shape: dict, optional
        The shape of the dispensing head to be used for the dispense.
        See liquid_handle_builders.shape_builder; specified as
        {"rows": int, "columns": int, "format": str} with format being a
        valid SBS format.
    shake_after: dict, optional
        Parameters that specify how a plate should be shaken at the very end
        of the instruction execution.
        {"duration": Unit, "frequency": Unit, "path": str, "amplitude": Unit}
    """

    builders = DispenseBuilders()

    def __init__(self, object, columns, reagent=None, resource_id=None,
                 reagent_source=None, step_size=None, flowrate=None,
                 nozzle_position=None, pre_dispense=None, shape=None,
                 shake_after=None):

        disp = {
            "object": object,
            "columns": columns,
            "reagent": reagent,
            "resource_id": resource_id,
            "reagent_source": reagent_source,
            "step_size": step_size,
            "pre_dispense": pre_dispense,
            "flowrate": flowrate,
            "nozzle_position": nozzle_position,
            "shape": shape,
            "shake_after": shake_after
        }

        source_fields = ["reagent", "resource_id", "reagent_source"]
        sources = {_: disp[_] for _ in source_fields}
        if sum([_ is not None for _ in sources.values()]) != 1:
            raise ValueError(
                "Exactly one of `reagent`, `resource_id`, and "
                "`reagent_source` must be specified for Dispense, "
                "but got {}.".format(sources))

        disp = {k: v for k, v in disp.items() if v is not None}

        super(Dispense, self).__init__(op="dispense", data=disp)


class AcousticTransfer(Instruction):
    """
    Specify source and destination wells for transfering liquid via an acoustic
    liquid handler.  Droplet size is usually device-specific.

    Parameters
    ----------
    groups : list(dict)
        List of `transfer` groups in the form of:

        .. code-block:: json

        {
            "transfer": [
                {
                    "to": well,
                    "from": well,
                    "volume": volume
                }
            ]
        }

    droplet_size : str or Unit
        Volume representing a droplet_size.  The volume of each transfer should
        be a multiple of this volume.

    """

    def __init__(self, groups, droplet_size):
        super(AcousticTransfer, self).__init__(
            op="acoustic_transfer",
            data={
                "groups": groups,
                "droplet_size": droplet_size
            })


class Spin(Instruction):
    """
    Apply the specified amount of acceleration to a plate using a centrifuge.

    Parameters
    ----------
    object : Ref or str
        Container to be centrifuged.
    acceleration : str
        Amount of acceleration to be applied to the container, expressed in
        units of "g" or "meter/second^2"
    duration : str or Unit
        Amount of time to apply acceleration.
    flow_direction : str
        Specifies the direction contents will tend toward with respect to
        the container. Valid directions are "inward" and "outward", default
        value is "inward".
    spin_direction : list(str)
        A list of "cw" (clockwise), "cww" (counterclockwise). For each
        element in the list, the container will be spun in the stated
        direction for the set "acceleration" and "duration". Default values
        are derived from the "flow_direction". If "flow_direction" is
        "outward", then "spin_direction" defaults to ["cw", "ccw"]. If
        "flow_direction" is "inward", then "spin_direction" defaults to
        ["cw"].

    """

    def __init__(self, object, acceleration, duration, flow_direction=None,
                 spin_direction=None):
        spin_json = {
            "object": object,
            "acceleration": acceleration,
            "duration": duration,
            "flow_direction": flow_direction,
            "spin_direction": spin_direction
        }

        super(Spin, self).__init__(op="spin", data=spin_json)


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
    object : str or Ref
        Container to be thermocycled
    groups : list(dict)
        List of thermocycling instructions formatted as above
    volume : str or Unit, optional
        Volume contained in wells being thermocycled
    dataref : str, optional
        Name of dataref representing read data if performing qPCR
    dyes : dict, optional
        Dictionary mapping dye types to the wells they're used in
    melting_start: str or Unit
        Temperature at which to start the melting curve.
    melting_end: str or Unit
        Temperature at which to end the melting curve.
    melting_increment: str or Unit
        Temperature by which to increment the melting curve. Accepted increment
        values are between 0.1 and 9.9 degrees celsius.
    melting_rate: str or Unit
        Specifies the duration of each temperature step in the melting curve.
    lid_temperature: str or Unit
        Specifies the lid temperature throughout the duration of the instruction

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
    CHANNEL1_DYES = ["FAM", "SYBR"]
    CHANNEL2_DYES = ["VIC", "HEX", "TET", "CALGOLD540"]
    CHANNEL3_DYES = ["ROX", "TXR", "CALRED610"]
    CHANNEL4_DYES = ["CY5", "QUASAR670"]
    CHANNEL5_DYES = ["QUASAR705"]
    CHANNEL6_DYES = ["FRET"]
    CHANNEL_DYES = [CHANNEL1_DYES, CHANNEL2_DYES,
                    CHANNEL3_DYES, CHANNEL4_DYES, CHANNEL5_DYES, CHANNEL6_DYES]
    AVAILABLE_DYES = [
        dye for channel_dye in CHANNEL_DYES for dye in channel_dye]

    builders = ThermocycleBuilders()

    def __init__(self, object, groups, volume="25:microliter", dataref=None,
                 dyes=None, melting_start=None, melting_end=None,
                 melting_increment=None, melting_rate=None,
                 lid_temperature=None):
        instruction = {
            "object": object,
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
        instruction['lid_temperature'] = lid_temperature
        super(Thermocycle, self).__init__(op="thermocycle", data=instruction)

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
            invalid_dyes = ", ".join(Thermocycle.find_invalid_dyes(dye_names))
            raise ValueError(
                "thermocycle instruction supplied the following invalid dyes: "
                "{}".format(invalid_dyes))

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
    object : Ref or str
        The container to be incubated
    where : Enum({"ambient", "warm_37", "cold_4", "cold_20", "cold_80"})
        Temperature at which to incubate specified container
    duration : Unit or str
        Length of time to incubate container
    shaking : bool, optional
        Specify whether or not to shake container if available at the specified
        temperature
    target_temperature : Unit or str, optional
        Specify a target temperature for a device (eg. an incubating block)
        to reach during the specified duration.
    shaking_params: dict, optional
        Specify "path" and "frequency" of shaking parameters to be used
        with compatible devices (eg. thermoshakes)
    co2 : int, optional
        Carbon dioxide percentage

    """
    WHERE = ["ambient", "warm_30", "warm_37", "cold_4", "cold_20", "cold_80"]

    def __init__(self, object, where, duration, shaking=False, co2=0,
                 target_temperature=None, shaking_params=None):
        if where not in self.WHERE:
            raise ValueError("Specified `where` not contained in: %s" % ", "
                             "".join(self.WHERE))
        if where == "ambient" and shaking and not shaking_params:
            raise ValueError("Shaking is only possible for ambient incubation "
                             "if 'shaking_params' are specified.")

        incubate_json = {
            "object": object,
            "where": where,
            "duration": duration,
            "shaking": shaking,
            "co2_percent": co2
        }
        if target_temperature:
            incubate_json["target_temperature"] = target_temperature
        if shaking_params:
            incubate_json["shaking_params"] = shaking_params
        super(Incubate, self).__init__(op="incubate", data=incubate_json)


class IlluminaSeq(Instruction):
    """
    Load aliquots into specified lanes for Illumina sequencing.
    The specified aliquots should already contain the appropriate mix for
    sequencing and require a library concentration reported in
    ng/uL.

    Parameters
    ----------
    flowcell : str
      Flowcell designation: "SR" or " "PE"
    lanes : list(dict)

        .. code-block:: json

          "lanes": [{
                "object": aliquot, Well,
                "library_concentration": decimal, // ng/uL
              },
              {...}]

    sequencer : str
      Sequencer designation: "miseq", "hiseq" or "nextseq"
    mode : str
      Mode designation: "rapid", "mid" or "high"
    index : str
      Index designation: "single", "dual" or "none"
    library_size: integer
        Library size expressed as an integer of basepairs
    dataref : str
        Name of sequencing dataset that will be returned.
    cycles : Enum({"read_1", "read_2", "index_1", "index_2"})
        Parameter specific to Illuminaseq read-length or number of
        sequenced bases. Refer to the ASC for more details

    """

    def __init__(self, flowcell, lanes, sequencer, mode, index, library_size,
                 dataref, cycles):
        seq = {
            "flowcell": flowcell,
            "lanes": lanes,
            "sequencer": sequencer,
            "mode": mode,
            "index": index,
            "library_size": library_size,
            "dataref": dataref,
            "cycles": cycles
        }

        super(IlluminaSeq, self).__init__(op="illumina_sequence", data=seq)


class SangerSeq(Instruction):
    """
    Send the indicated wells of the container specified for Sanger sequencing.
    The specified wells should already contain the appropriate mix for
    sequencing, including primers and DNA according to the instructions
    provided by the vendor.

    Parameters
    ----------
    object : Container or str
      Container with well(s) that contain material to be sequenced.
    wells : list(str)
      Well indices of the container that contain appropriate materials to be
      sent for sequencing.
    dataref : str
      Name of sequencing dataset that will be returned.
    type: Enum({"standard", "rca"})
        Sanger sequencing type
    primer : Container, optional
        Tube containing sufficient primer for all RCA reactions.  This field
        will be ignored if you specify the sequencing type as "standard".
        Tube containing sufficient primer for all RCA reactions

    """

    def __init__(self, object, wells, dataref, type, primer=None):
        seq = {
            "type": type,
            "object": object,
            "wells": wells,
            "dataref": dataref
        }
        if primer and type == "rca":
            seq["primer"] = primer
        super(SangerSeq, self).__init__(op="sanger_sequence", data=seq)


class GelSeparate(Instruction):
    """
    Separate nucleic acids on an agarose gel.

    Parameters
    ----------
    objects: list or WellGroup or Well
        List of wells or WellGroup containing wells to be
        separated on gel.
    volume : str or Unit
        Volume of liquid to be transferred from each well specified to a
        lane of the gel.
    matrix : str
        Matrix (gel) in which to gel separate samples
    ladder : str
        Ladder by which to measure separated fragment size
    duration : str or Unit
        Length of time to run current through gel.
    dataref : str
        Name of this set of gel separation results.

    """

    def __init__(self, objects, volume, matrix, ladder, duration, dataref):
        super(GelSeparate, self).__init__(op="gel_separate", data={
            "objects": objects,
            "volume": volume,
            "matrix": matrix,
            "ladder": ladder,
            "duration": duration,
            "dataref": dataref
        })


class GelPurify(Instruction):

    """
    Separate nucleic acids on an agarose gel and purify.

    Parameters
    ----------
    objects: list or WellGroup
        WellGroup of wells to be purified
    volume : str or Unit
        Volume of sample required for analysis
    dataref : str
        Name of this specific dataset of measurements
    matrix : str
        Agarose concentration and number of wells on gel used for separation
    ladder : str
        Size range of ladder to be used to compare band size to
    dataref : str
        Name of dataset containing fragment sizes returned
    extract: list(dict)

        .. code-block:: json

          "extract": [{
                "elution_volume": volume,
                "elution_buffer": string, "water" | "TE",
                "lane": int,
                "band_size_range": {
                  "min_bp": int,
                  "max_bp": int,
                },
                "destination": well
              },
              {...}]

    """

    def __init__(self, objects, volume, matrix, ladder, dataref, extract):
        super(GelPurify, self).__init__(op="gel_purify", data={
            "objects": objects,
            "volume": volume,
            "matrix": matrix,
            "ladder": ladder,
            "dataref": dataref,
            "extract": extract
        })


class Absorbance(Instruction):

    """
    Read the absorbance for the indicated wavelength for the indicated
    wells. Append an Absorbance instruction to the list of instructions for
    this Protocol object.

    Parameters
    ----------
    object : str or Ref
        Object to execute the absorbance read on
    wells : list(Well) or WellGroup
        WellGroup of wells to be measured or a list of well references in
        the form of ["A1", "B1", "C5", ...]
    wavelength : str or Unit
        wavelength of light absorbance to be read for the indicated wells
    dataref : str
        name of this specific dataset of measured absorbances
    flashes : int, optional
        number of flashes for the read
    incubate_before: dict, optional
        incubation prior to reading if desired
        shaking: dict, optional
            shake parameters if desired
                amplitude: str or Unit
                    amplitude of shaking between 1 and 6:millimeter
                orbital: bool
                    True for oribital and False for linear shaking
        duration: str, Unit, optional
            time prior to plate reading
    temperature: str or Unit, optional
        set temperature to heat plate reading chamber
    settle_time: str or Unit, optional
        time to pause before each well read

    """

    def __init__(self, object, wells, wavelength, dataref, flashes=25,
                 incubate_before=None, temperature=None,
                 settle_time=None):
        json_dict = {"object": object,
                     "wells": wells,
                     "wavelength": wavelength,
                     "num_flashes": flashes,
                     "dataref": dataref,
                     "incubate_before": incubate_before,
                     "temperature": temperature,
                     "settle_time": settle_time}

        super(Absorbance, self).__init__(op="absorbance", data=json_dict)


class Fluorescence(Instruction):

    """
    Read the fluoresence for the indicated wavelength for the indicated
    wells.  Append a Fluorescence instruction to the list of instructions
    for this Protocol object.

    Parameters
    ----------
    object : str or Container
        object to execute the fluorescence read on
    wells : list(Well) or WellGroup
        WellGroup of wells to be measured or a list of well references in
        the form of ["A1", "B1", "C5", ...]
    excitation : str or Unit
        wavelength of light used to excite the wells indicated
    emission : str or Unit
        wavelength of light to be measured for the indicated wells
    dataref : str
        name of this specific dataset of measured absorbances
    flashes : int, optional
        number of flashes for this read
    incubate_before: dict, optional
        incubation prior to reading if desired
        shaking: dict, optional
            shake parameters if desired
                amplitude: str or Unit
                    amplitude of shaking between 1 and 6:millimeter
                orbital: bool
                    True for oribital and False for linear shaking
        duration: str, Unit, optional
            time prior to plate reading
    temperature: str or Unit, optional
        set temperature to heat plate reading chamber
    gain: float, optional
            float between 0 and 1, multiplier of maximum signal amplification
    detection_mode: str, optional
        set the detection mode of the optics, ["top", "bottom"],
        defaults to vendor specified defaults.
    position_z: dict, optional
        distance from the optics to the surface of the plate transport,
        only valid for "top" detection_mode and vendor capabilities.
        Specified as either a set distance - "manual", OR calculated from
        a WellGroup - "calculated_from_wells".   Only one position_z
        determination may be specified
        position_z = {
            "manual": Unit
            - OR -
            "calculated_from_wells": []
        }
    manual: str, Unit, optional
        parameter available within "position_z" to set the distance from
        the optics to the plate transport.
    calculated_from_wells: list, WellGroup, Well, optional
        parameter available within "position_z" to set the distance from
        the optics to the plate transport.  If specified, the average
        optimal (maximal signal) distance will be chosen from the list
        of wells and applied to all measurements.
    settle_time: Unit, optional
        the time before the start of the measurement, defaults
        to vendor specifications
    lag_time: Unit, optional
        time between flashes and the start of the signal integration,
        defaults to vendor specifications
    integration_time: Unit, optional
        duration of the signal recording, per Well, defaults to vendor
        specifications

    """

    def __init__(self, object, wells, excitation, emission, dataref, flashes=25,
                 incubate_before=None, temperature=None, gain=None,
                 detection_mode=None, position_z=None, settle_time=None,
                 lag_time=None, integration_time=None):
        json_dict = {
            "object": object,
            "wells": wells,
            "excitation": excitation,
            "emission": emission,
            "num_flashes": flashes,
            "dataref": dataref,
            "incubate_before": incubate_before,
            "temperature": temperature,
            "gain": gain,
            "settle_time": settle_time,
            "lag_time": lag_time,
            "integration_time": integration_time,
            "detection_mode": detection_mode,
            "position_z": position_z
        }

        super(Fluorescence, self).__init__(op="fluorescence", data=json_dict)


class Luminescence(Instruction):

    """
    Read luminesence of indicated wells

    Parameters
    ----------
    object: str or Container
        object to execute the luminescence read on
    wells : list or WellGroup
        WellGroup or list of wells to be measured
    dataref : str
        name which dataset will be saved under
    incubate_before: dict, optional
        incubation prior to reading if desired
        shaking: dict, optional
            shake parameters if desired
                amplitude: str or Unit
                    amplitude of shaking between 1 and 6:millimeter
                orbital: bool
                    True for oribital and False for linear shaking
        duration: str, Unit, optional
            time prior to plate reading
    temperature: str or Unit, optional
        set temperature to heat plate reading chamber
    settle_time: str or Unit, optional
        time to pause before each well read
    integration_time: Unit, optional
        duration of the signal recording, per Well, defaults to vendor
        specifications

    """

    def __init__(self, object, wells, dataref, incubate_before=None,
                 temperature=None, settle_time=None, integration_time=None):
        json_dict = {
            "object": object,
            "wells": wells,
            "dataref": dataref,
            "incubate_before": incubate_before,
            "temperature": temperature,
            "settle_time": settle_time,
            "integration_time": integration_time
        }

        super(Luminescence, self).__init__(op="luminescence", data=json_dict)


class Seal(Instruction):

    """
    Seal indicated container using the automated plate sealer.

    Parameters
    ----------
    object : Ref or str
        Container to be sealed
    type : str, optional
        Seal type to be used (optional)
    mode : str, optional
        Method used to seal plate (optional). "thermal" or "adhesive"
    mode_params : dict, optional
        Thermal sealing parameters
        temperature : str, optional
            Temperature to seal plate at
        duration : str, optional
            Duration for which to apply heated sealing plate onto ref
    """

    def __init__(self, object, type="ultra-clear", mode=None, mode_params=None):
        seal_dict = {
            "object": object,
            "type": type,
            "mode": mode,
            "mode_params": mode_params
        }

        super(Seal, self).__init__(op="seal", data=seal_dict)


class Unseal(Instruction):
    """
    Remove seal from indicated container using the automated plate unsealer.

    Parameters
    ----------
    object : Ref or str
        Container to be unsealed

    """

    def __init__(self, object):
        super(Unseal, self).__init__(op="unseal", data={"object": object})


class Cover(Instruction):

    """
    Place specified lid type on specified container

    Parameters
    ----------
    object : str
        Container to be covered
    lid : Enum({'standard', 'universal', 'low_evaporation'}), optional
        Type of lid to cover container with
    retrieve_lid : bool
        Flag to retrieve lid from stored location

    """
    LIDS = ["standard", "universal", "low_evaporation"]

    def __init__(self, object, lid="standard", retrieve_lid=None):
        if lid and lid not in self.LIDS:
            raise ValueError("%s is not a valid lid type" % lid)
        cover = {
            "object": object,
            "lid": lid,
            "retrieve_lid": retrieve_lid
        }

        super(Cover, self).__init__(op='cover', data=cover)


class Uncover(Instruction):
    """
    Remove lid from specified container

    Parameters
    ----------
    object : str
        Container to remove lid from
    store_lid : bool
        Flag to store the uncovered lid

    """

    def __init__(self, object, store_lid=None):
        super(Uncover, self).__init__(
            op="uncover",
            data={
                "object": object,
                "store_lid": store_lid
            }
        )


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

    negative_controls : list(dict)
        List of negative control wells in the form of:

        .. code-block:: json

            {
                "well": well,
                "volume": volume,
                "captured_events": integer,     // optional, default infinity
                "channel": [channel_name]
            }

        at least one negative control is required.
    samples : list(dict)
        List of samples in the form of:

        .. code-block:: json

            {
                "well": well,
                "volume": volume,
                "captured_events": integer,     // optional, default infinity
            }

        at least one sample is required
    colors : list(dict), optional
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


    positive_controls : list(dict), optional
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
                 negative_controls,
                 samples,
                 colors=None,
                 positive_controls=None):
        flow_instr = {"dataref": dataref, "channels": {}}
        flow_instr["channels"]["FSC"] = FSC
        flow_instr["channels"]["SSC"] = SSC
        flow_instr["negative_controls"] = negative_controls
        flow_instr["samples"] = samples
        if colors:
            flow_instr["channels"]["colors"] = colors
        if positive_controls:
            flow_instr["positive_controls"] = positive_controls

        super(FlowAnalyze, self).__init__(op="flow_analyze", data=flow_instr)


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
        super(Oligosynthesize, self).__init__(op="oligosynthesize", data={
            "oligos": oligos
        })


class Autopick(Instruction):
    """
    Pick colonies from the agar-containing location(s) specified in `sources`
    to the location(s) specified in `dests` in highest to lowest rank order
    until there are no more colonies available.  If fewer than min_abort
    pickable colonies have been identified from the location(s) specified in
    `sources`, the run will stop and no further instructions will be executed.

    Parameters
    ----------
    groups : list(dict)
        Groups of colonies to pick and where to transport them to
    criteria : dict
        Dictionary of autopicking criteria.
    dataref: str
        Name of dataset to save the picked colonies to

    """

    def __init__(self, groups, criteria, dataref):
        pick = {
            "groups": groups,
            "dataref": dataref,
            "criteria": criteria
        }

        super(Autopick, self).__init__(op="autopick", data=pick)


class ImagePlate(Instruction):
    """
    Capture an image of the specified container.

    Parameters
    ----------
    object : str
        Container to take image of
    mode : str
        Imaging mode (currently supported: "top")
    dataref : str
        Name of data reference of resulting image

    """

    def __init__(self, object, mode, dataref):
        super(ImagePlate, self).__init__(op="image_plate", data={
            "object": object,
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
    dests : list(dict)
      Destination(s) for specified resource, together with volume information

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
        super(Provision, self).__init__(
            op="provision",
            data={"resource_id": resource_id, "to": dests}
        )


class FlashFreeze(Instruction):
    """
    Flash freeze the contents of the specified container by submerging it in
    liquid nitrogen for the specified amount of time.

    Parameters
    ----------
    object : Container or str
        Container to be flash frozen.
    duration : str or Unit
        Duration to submerge specified container in liquid nitrogen.

    """

    def __init__(self, object, duration):
        super(FlashFreeze, self).__init__(op="flash_freeze", data={
            "object": object,
            "duration": duration
        })


class MeasureConcentration(Instruction):
    """
    Measure the concentration of DNA, ssDNA, RNA or Protein in the specified
    volume of the source aliquots.

    Parameters
    ----------
    object : list or WellGroup
        WellGroup of wells to be measured
    volume : str or Unit
        Volume of sample required for analysis
    dataref : str
        Name of this specific dataset of measurements
    measurement : str
        Class of material to be measured. One of ["DNA", "ssDNA", "RNA",
        "protein"].

    """

    def __init__(self, object, volume, dataref, measurement):
        json_dict = {"object": object,
                     "volume": volume,
                     "dataref": dataref,
                     "measurement": measurement}
        super(MeasureConcentration, self).__init__(op="measure_concentration",
                                                   data=json_dict)


class MeasureMass(Instruction):
    """
    Measure the mass of containers

    Parameters
    ----------
    object : Container
        Container ref
    dataref: str
        Name of the data for the measurement
    """

    def __init__(self, object, dataref):
        json_dict = {"object": object, "dataref": dataref}
        super(MeasureMass, self).__init__(op="measure_mass", data=json_dict)


class MeasureVolume(Instruction):
    """
    Measure the mass of containers

    Parameters
    ----------
    object: list(Container)
        list of containers
    dataref: str
        Name of the data for the measurement
    """

    def __init__(self, object, dataref):
        json_dict = {"object": object, "dataref": dataref}
        super(MeasureVolume, self).__init__(op="measure_volume", data=json_dict)


class CountCells(Instruction):
    """
    Count the number of cells in a sample that are positive/negative
    for a given set of labels.

    Parameters
    ----------
    wells: WellGroup
        List of wells that will be used for cell counting.
    volume: Unit
        Volume that should be consumed from each well for the purpose
        of cell counting.
    dataref: str
        Name of dataset that will be returned.
    labels: list(string), optional
        Cells will be scored for presence or absence of each label
        in this list. If staining is required to visualize these labels,
        they must be added before execution of this instruction.

    """

    def __init__(self, wells, volume, dataref, labels=None):
        json_dict = {
            "wells": wells,
            "volume": volume,
            "dataref": dataref,
            "labels": labels
        }

        super(CountCells, self).__init__(op="count_cells", data=json_dict)


class Spectrophotometry(Instruction):
    """
    Execute a Spectrophotometry plate read on the obj.

    Parameters
    ----------
    dataref : str
        Name of the resultant dataset to be returned.
    object : Container or str
        Container to be read.
    groups : list
        A list of groups generated by SpectrophotometryBuilders groups builders,
        any of absorbance_mode_params, fluorescence_mode_params,
        luminescence_mode_params, or shake_mode_params.
    interval : Unit or str, optional
        The time between each of the read intervals.
    num_intervals : int, optional
        The number of times that the groups should be executed.
    temperature : Unit or str, optional
        The temperature that the entire instruction should be executed at.
    shake_before : dict, optional
        A dict of params generated by SpectrophotometryBuilders.shake_before
        that dictates how the obj should be incubated with shaking before any of
        the groups are executed.
    """
    builders = SpectrophotometryBuilders()

    def __init__(self, dataref, object, groups, interval=None,
                 num_intervals=None, temperature=None, shake_before=None):
        spec = {
            "dataref": dataref,
            "object": object,
            "groups": groups,
            "interval": interval,
            "num_intervals": num_intervals,
            "temperature": temperature,
            "shake_before": shake_before
        }

        super(Spectrophotometry, self).__init__(op="spectrophotometry",
                                                data=spec)
