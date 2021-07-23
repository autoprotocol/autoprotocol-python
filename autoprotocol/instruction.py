"""
Contains all the Autoprotocol Instruction objects

    :copyright: 2021 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

"""

# pragma pylint: disable=too-few-public-methods, redefined-builtin
from .builders import *  # pylint: disable=unused-wildcard-import
from .constants import PROVISION_MEASUREMENT_MODES
from .container import Container
from .informatics import AttachCompounds, Informatics


class Instruction(object):
    """Base class for an instruction that is to later be encoded as JSON."""

    builders = InstructionBuilders()

    def __init__(self, op, data, informatics=None):
        super(Instruction, self).__init__()
        # prevent mutable default value by assigning default value inside the method
        if informatics is None:
            informatics = []
        self.op = op
        self.data = self._remove_empty_fields(self._remove_empty_fields(data))
        self.__dict__.update(self.data)
        self.informatics = self._remove_empty_fields(
            self._remove_empty_fields(informatics)
        )

        if len(self.informatics) > 0:
            self._check_informatics()

    def __repr__(self):
        return f"Instruction({self.op}, {self.data}, {self.informatics})"

    def _as_AST(self):
        """generates a Python object representation of Autoprotocol JSON

        Returns
        -------
        dict
            a dict of python objects that have the same structure as the
            Autoprotocol JSON for the Instruction

        Notes
        -----
        Used downstream for JSON serialization of the Instruction

        See Also
        --------
        :meth:`Protocol._refify` : Protocol serialization method

        """
        # informatics is not serialized if empty.
        if self.informatics:
            return dict(op=self.op, **self.data, informatics=self.informatics)
        else:
            return dict(op=self.op, **self.data)

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
            return {
                k: Instruction._remove_empty_fields(v)
                for k, v in data.items()
                if not filter_criteria(v)
            }
        if isinstance(data, list):
            return [
                Instruction._remove_empty_fields(_)
                for _ in data
                if not filter_criteria(_)
            ]
        return data

    def _check_informatics(self):
        """
        Validates each Informatics element in informatics.

        Raises
        ------
        TypeError
            informatics is in a list
        TypeError
            informatics element is Informatics

        """
        if not isinstance(self.informatics, list):
            raise TypeError(
                f"informatics: {self.informatics} must be provided in a list."
            )
        for info in self.informatics:
            if not isinstance(info, Informatics):
                raise TypeError("informatics must be Informatics type.")
            if isinstance(info, AttachCompounds):
                available_wells = self.get_wells(self.data)
                self._check_info_wells(info, available_wells)

    @staticmethod
    def _check_info_wells(info, available_wells):
        """
        validates Informatics wells are included in the wells associated with
        the instruction.

        Raises
        -------
        ValueError
            'wells' has a value in the informatics data
        TypeError
            wells are Well, list of Well or WellGroup
        ValueError
            Informatics wells are part of wells Instruction is operating on
        """
        if not info.wells:
            raise ValueError(
                f"Informatics: {info} must have wells to run this validation."
            )
        info_wells = info.wells
        if not is_valid_well(info_wells):
            raise TypeError(
                f"wells: {info_wells} must be Well, list of Well or WellGroup."
            )
        wells = WellGroup(info_wells)

        for well in wells.wells:
            if well not in available_wells:
                raise ValueError(
                    f"informatics well: {wells} must be one of the wells used in this instruction."
                )

        info.wells = wells.wells

    # pragma pylint: disable=expression-not-assigned
    # pragma pylint: disable=unused-variable
    def get_wells(self, op_data):
        """
        Parameters
        ----------
        op_data: dict
            Instruction data containing all the operational parameters

        Returns
        -------
        list(Well)
            List of all wells associated with the instruction. Note this contains
            all source and destination wells for instructions such as `liquid_handle`.
        """
        all_wells = []
        if type(op_data) is dict:
            for k, v in op_data.items():
                all_wells.append(self.get_wells(v))
        elif type(op_data) is list:
            for i in op_data:
                all_wells.extend([self.get_wells(i)])
        # if container is provided, all wells in the container are included
        elif type(op_data) is Container:
            all_wells.append(op_data.all_wells())
        elif is_valid_well(op_data):
            all_wells.append(WellGroup(op_data))

        flattened_wells = [item for sublist in all_wells for item in sublist]
        # remove any duplicate values in the list
        unique_wells = []
        [unique_wells.append(x) for x in flattened_wells if x not in unique_wells]

        return unique_wells


class MagneticTransfer(Instruction):
    """
    A magnetic_transfer instruction is constructed as a list of lists of
    groups, executed in order, where each group is a collect, release, dry,
    incubate, or mix sub-operation.  These sub-operations control the behavior
    of tips which can be magnetized, and a heating platform. Groups in the same
    list of groups use the same tips.

    Parameters
    ----------
    groups: list(list(dict))
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
    magnetic_head: str
        Head-type used for this instruction
    """

    builders = MagneticTransferBuilders()

    max_objects = 8
    heads = {
        "96-deep": ["96-v-kf", "96-deep-kf", "96-deep"],
        "96-pcr": ["96-pcr", "96-v-kf", "96-flat", "96-flat-uv"],
    }

    def __init__(self, groups, magnetic_head):
        sub_ops = [subgroup for group in groups for subgroup in group]

        if not all(len(_) == 1 for _ in sub_ops):
            raise ValueError(
                f"Not all sub-operations in groups {groups} contain a single "
                f"sub-operation."
            )

        containers = {list(_.values()).pop()["object"] for _ in sub_ops}
        valid_container_types = all(
            _.container_type.shortname in self.heads[magnetic_head] for _ in containers
        )
        if not valid_container_types:
            raise ValueError(
                f"Not all containers: {containers} are in the allowed "
                f"container_types: {self.heads[magnetic_head]} for head_type: "
                f"{magnetic_head}"
            )

        # a new tip is used for each group
        if len(groups) + len(containers) > self.max_objects:
            raise RuntimeError(
                f"Only {self.max_objects} total objects can be used within the "
                f"same instruction and {len(containers)} "
                f"containers: {containers} were specified in addition to "
                f"{len(groups)} groups where each group requires a new "
                f"tip object."
            )

        magnetic_transfer = {"groups": groups, "magnetic_head": magnetic_head}

        super(MagneticTransfer, self).__init__(
            op="magnetic_transfer", data=magnetic_transfer
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

    def __init__(
        self,
        object,
        columns,
        reagent=None,
        resource_id=None,
        reagent_source=None,
        step_size=None,
        flowrate=None,
        nozzle_position=None,
        pre_dispense=None,
        shape=None,
        shake_after=None,
    ):

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
            "shake_after": shake_after,
        }

        source_fields = ["reagent", "resource_id", "reagent_source"]
        sources = {_: disp[_] for _ in source_fields}
        if sum([_ is not None for _ in sources.values()]) != 1:
            raise ValueError(
                f"Exactly one of `reagent`, `resource_id`, and "
                f"`reagent_source` must be specified for Dispense, but got "
                f"{sources}."
            )

        disp = {k: v for k, v in disp.items() if v is not None}

        super(Dispense, self).__init__(op="dispense", data=disp)


class AcousticTransfer(Instruction):
    """
    Specify source and destination wells for transferring liquid via an acoustic
    liquid handler.  Droplet size is usually device-specific.

    Parameters
    ----------
    groups : list(dict)
        List of `transfer` groups in the form of:

        .. code-block:: json

            {
                "transfer": [
                    {
                        "to": "foo/A1",
                        "from": "bar/A1",
                        "volume": "1:nl"
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
            data={"groups": groups, "droplet_size": droplet_size},
        )


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

    def __init__(
        self, object, acceleration, duration, flow_direction=None, spin_direction=None
    ):
        spin_json = {
            "object": object,
            "acceleration": acceleration,
            "duration": duration,
            "flow_direction": flow_direction,
            "spin_direction": spin_direction,
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
    melting : dict
        Melting parameters
        See Also :meth:`Thermocycle.builders.melting`
    lid_temperature: str or Unit
        Specifies the lid temperature throughout the duration of the instruction

    Raises
    ------
    ValueError
        If one of dataref and dyes is specified but the other isn't
    ValueError
        If melting curve parameters are specified but dyes isn't
    """

    builders = ThermocycleBuilders()

    def __init__(
        self,
        object,
        groups,
        volume="25:microliter",
        dataref=None,
        dyes=None,
        melting=None,
        lid_temperature=None,
    ):

        qpcr_params = [dyes, dataref]
        if any(qpcr_params) and not all(qpcr_params):
            raise ValueError(
                f"either dyes {dyes} or dataref {dataref} was specified, but "
                f"both are required for qPCR"
            )

        if melting and any(melting.values()) and not dyes:
            raise ValueError(f"melting: {melting} was specified, but dyes was not")

        thermocycle = {
            "object": object,
            "groups": groups,
            "volume": volume,
            "dataref": dataref,
            "dyes": dyes,
            "melting": melting,
            "lid_temperature": lid_temperature,
        }

        super(Thermocycle, self).__init__(op="thermocycle", data=thermocycle)


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
    co2 : Number, optional
        Carbon dioxide percentage

    """

    WHERE = [
        "ambient",
        "warm_30",
        "warm_35",
        "warm_37",
        "cold_4",
        "cold_20",
        "cold_80",
        "cold_196",
    ]

    def __init__(
        self,
        object,
        where,
        duration,
        shaking=False,
        co2=0,
        target_temperature=None,
        shaking_params=None,
    ):
        if where not in self.WHERE:
            raise ValueError(
                "Specified `where` not contained in: " f"{', '.join(self.WHERE)}"
            )
        if where == "ambient" and shaking and not shaking_params:
            raise ValueError(
                "Shaking is only possible for ambient incubation "
                "if 'shaking_params' are specified."
            )

        incubate_json = {
            "object": object,
            "where": where,
            "duration": duration,
            "shaking": shaking,
            "co2_percent": co2,
        }
        if target_temperature:
            incubate_json["target_temperature"] = target_temperature
        if shaking_params:
            incubate_json["shaking_params"] = shaking_params
        super(Incubate, self).__init__(op="incubate", data=incubate_json)


class Agitate(Instruction):
    """
    Agitate sample(s) in a container in a specific condition for a given
    duration. Once the duration has elapsed, sample(s) will be returned
    to specified storage condition until it is used in the next
    instruction.

    Parameters
    ----------
    object : ref or str
        The container to be agitated
    mode : Enum(["vortex", "invert", "roll", "stir_bar"])
        Specifies the mode of agitation
    speed : Unit or str
        Speed to agitate container at
    duration : Unit or str
        Length of time to agitate container
    temperature : Unit or str
        Temperature to agitate container at
    mode_params : dict, optional
        Dictionary containing mode params for agitation modes
    """

    def __init__(
        self, object, mode, speed, duration, temperature=None, mode_params=None
    ):
        agitate_json = {
            "object": object,
            "mode": mode,
            "duration": duration,
            "speed": speed,
        }
        if mode_params:
            agitate_json["mode_params"] = mode_params
        if temperature:
            agitate_json["temperature"] = temperature
        super(Agitate, self).__init__(op="agitate", data=agitate_json)


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

        .. code-block:: none

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

    def __init__(
        self, flowcell, lanes, sequencer, mode, index, library_size, dataref, cycles
    ):
        seq = {
            "flowcell": flowcell,
            "lanes": lanes,
            "sequencer": sequencer,
            "mode": mode,
            "index": index,
            "library_size": library_size,
            "dataref": dataref,
            "cycles": cycles,
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
        seq = {"type": type, "object": object, "wells": wells, "dataref": dataref}
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
        super(GelSeparate, self).__init__(
            op="gel_separate",
            data={
                "objects": objects,
                "volume": volume,
                "matrix": matrix,
                "ladder": ladder,
                "duration": duration,
                "dataref": dataref,
            },
        )


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

        .. code-block:: none

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

    builders = GelPurifyBuilders()

    def __init__(self, objects, volume, matrix, ladder, dataref, extract):
        super(GelPurify, self).__init__(
            op="gel_purify",
            data={
                "objects": objects,
                "volume": volume,
                "matrix": matrix,
                "ladder": ladder,
                "dataref": dataref,
                "extract": extract,
            },
        )


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

    builders = PlateReaderBuilders()

    def __init__(
        self,
        object,
        wells,
        wavelength,
        dataref,
        flashes=25,
        incubate_before=None,
        temperature=None,
        settle_time=None,
    ):
        json_dict = {
            "object": object,
            "wells": wells,
            "wavelength": wavelength,
            "num_flashes": flashes,
            "dataref": dataref,
            "incubate_before": incubate_before,
            "temperature": temperature,
            "settle_time": settle_time,
        }

        super(Absorbance, self).__init__(op="absorbance", data=json_dict)


class Fluorescence(Instruction):

    """
    Read the fluorescence for the indicated wavelength for the indicated
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
        a WellGroup - "calculated_from_wells". Only one position_z
        determination may be specified

        .. code-block:: none

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

    builders = PlateReaderBuilders()

    def __init__(
        self,
        object,
        wells,
        excitation,
        emission,
        dataref,
        flashes=25,
        incubate_before=None,
        temperature=None,
        gain=None,
        detection_mode=None,
        position_z=None,
        settle_time=None,
        lag_time=None,
        integration_time=None,
    ):
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
            "position_z": position_z,
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

    builders = PlateReaderBuilders()

    def __init__(
        self,
        object,
        wells,
        dataref,
        incubate_before=None,
        temperature=None,
        settle_time=None,
        integration_time=None,
    ):
        json_dict = {
            "object": object,
            "wells": wells,
            "dataref": dataref,
            "incubate_before": incubate_before,
            "temperature": temperature,
            "settle_time": settle_time,
            "integration_time": integration_time,
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
            "mode_params": mode_params,
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
            raise ValueError(f"{lid} is not a valid lid type")
        cover = {"object": object, "lid": lid, "retrieve_lid": retrieve_lid}

        super(Cover, self).__init__(op="cover", data=cover)


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
            op="uncover", data={"object": object, "store_lid": store_lid}
        )


class FlowCytometry(Instruction):
    """
    This instruction provides a non-ambiguous set of parameters for the
    performance of flow cytometry.

    Parameters
    ----------
    dataref : str
        Name of dataset that will be returned.
    samples : list(Well) or Well or WellGroup
        Wells to be analyzed
    lasers : list(dict)
        See FlowCytometryBuilders.laser.
    collection_conditions : dict
        See FlowCytometryBuilders.collection_conditions.
    width_threshold : int or float, optional
        Threshold to determine width measurement.
    window_extension : int or float, optional
        Front and rear window extension.
    remove_coincident_events : bool, optional
        Remove coincident events. Defaults to false.
    """

    builders = FlowCytometryBuilders()

    def __init__(
        self,
        dataref,
        samples,
        lasers,
        collection_conditions,
        width_threshold=None,
        window_extension=None,
        remove_coincident_events=None,
    ):

        instruction = {
            "dataref": dataref,
            "samples": samples,
            "lasers": lasers,
            "collection_conditions": collection_conditions,
            "width_threshold": width_threshold,
            "window_extension": window_extension,
            "remove_coincident_events": remove_coincident_events,
        }

        super(FlowCytometry, self).__init__(op="flow_cytometry", data=instruction)


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

        .. code-block:: none

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

        .. code-block:: none

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

        .. code-block:: none

            {
                "well": well,
                "volume": volume,
                "captured_events": integer,     // optional, default infinity
                "channel": [channel_name]
            }

        at least one negative control is required.
    samples : list(dict)
        List of samples in the form of:

        .. code-block:: none

            {
                "well": well,
                "volume": volume,
                "captured_events": integer,     // optional, default infinity
            }

        at least one sample is required
    colors : list(dict), optional
        Optional list of colors in the form of:

        .. code-block:: none

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
            }]


    positive_controls : list(dict), optional
        Optional list of positive control wells in the form of:

        .. code-block:: none

            [{
                "well": well,
                "volume": volume,
                "captured_events": integer,     // optional, default infinity
                "channel": [channel_name],
                "minimize_bleed": [{            // optional
                  "from": color,
                  "to": [color]
                }]
            }]

    """

    def __init__(
        self,
        dataref,
        FSC,
        SSC,
        negative_controls,
        samples,
        colors=None,
        positive_controls=None,
    ):
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

        .. code-block:: none

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
        super(Oligosynthesize, self).__init__(
            op="oligosynthesize", data={"oligos": oligos}
        )


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
        pick = {"groups": groups, "dataref": dataref, "criteria": criteria}

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
        super(ImagePlate, self).__init__(
            op="image_plate", data={"object": object, "mode": mode, "dataref": dataref}
        )


class Image(Instruction):
    """
    Capture an image of the specified container.

    Parameters
    ----------
    ref : Container
        Container of which to take image.
    mode : str
        Angle of image, one of "top", "bottom", "side"
    num_images : int
        Number of images taken of the container. Defaults to 1.
    dataref : str
        Name of data reference of resulting image
    backlighting : Bool, optional
        Whether back-lighting is desired.
    magnification : float
        Ratio of sizes of the image projected on the camera
        sensor compared to the actual size of the object
        captured. Defaults to 1.0.
    exposure : dict, optional
        Parameters to control exposure: "aperture", "iso",
        and "shutter_speed".

        shutter_speed: Unit, optional
            Duration that the imaging sensor is exposed.
        iso : Float, optional
            Light sensitivity of the imaging sensor.
        aperture: Float, optional
            Diameter of the lens opening.

    """

    def __init__(
        self, ref, mode, dataref, num_images, backlighting, exposure, magnification
    ):
        json_dict = {
            "object": ref,
            "mode": mode,
            "dataref": dataref,
            "num_images": num_images,
            "magnification": magnification,
            "back_lighting": backlighting,
            "exposure": exposure,
        }

        super(Image, self).__init__(op="image", data=json_dict)


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
    measurement_mode : str
      Measurement mode. Possible values are :py:class:`autoprotocol.constants.MEASUREMENT_MODES`
    informatics : list(Informatics)
      List of expected aliquot effects at the completion of this instruction

    Raises
    ------
    TypeError
      If resource_id is not a string.
    RuntimeError
      If length of the list of volumes specified does not match the number of
      destination wells specified.
    RuntimeError
      If the measurement mode is not supported.
    TypeError
      If volume is not specified as a string or Unit (or a list of either)

    """

    def __init__(self, resource_id, dests, measurement_mode="volume", informatics=None):
        if measurement_mode not in PROVISION_MEASUREMENT_MODES:
            raise RuntimeError(
                f"{measurement_mode} is not a valid measurement mode for provisioning"
            )

        super(Provision, self).__init__(
            op="provision",
            data={
                "resource_id": resource_id,
                "measurement_mode": measurement_mode,
                "to": dests,
            },
            informatics=informatics,
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
        super(FlashFreeze, self).__init__(
            op="flash_freeze", data={"object": object, "duration": duration}
        )


class Evaporate(Instruction):
    """
    Removes liquid or moisture from sample.

    Parameters
    ----------
    ref : Container
        Sample container
    mode : str
        Mode of evaporation
    duration : Unit or str
        Duration object is processed
    evaporator_temperature : Unit or str
        Temperature object is exposed to
    mode_params : dict
        Dictionary of parameters for evaporation mode
    """

    builders = EvaporateBuilders()

    def __init__(self, ref, mode, duration, evaporator_temperature, mode_params):
        json_dict = {
            "object": ref,
            "mode": mode,
            "duration": duration,
            "evaporator_temperature": evaporator_temperature,
            "mode_params": mode_params,
        }
        super(Evaporate, self).__init__(op="evaporate", data=json_dict)


class SPE(Instruction):

    """
    Apply a solid phase extraction (spe) technique to a sample.

    Parameters
    ----------
    well : Well
        Well to solid phase extract.
    cartridge : str
        Cartridge to use for solid phase extraction.
    pressure_mode : str
        The direction of pressure applied to the cartridge to force
        liquid flow. One of "positive", "negative".
    load_sample: dict
        Parameters for applying the sample to the cartridge.
        Single 'mobile_phase_param'.
    elute: list(dict)
        Parameters for applying a mobile phase to the cartridge
        with one or more solvents. List of 'mobile_phase_params'.
        Requires `destination_well`.
    condition: list(dict), optional
        Parameters for applying a mobile phase to the cartridge
        with one or more solvents. List of 'mobile_phase_params'.
    equilibrate: list(dict), optional
        Parameters for applying a mobile phase to the cartridge
        with one or more solvents. List of 'mobile_phase_params'.
    rinse: list(dict), optional
        Parameters for applying a mobile phase to the cartridge
        with one or more solvents. List of 'mobile_phase_params'.

        mobile_phase_params:
            resource_id: str
                Resource ID of desired solvent.
            volume: volume
                Volume added to the cartridge.
            loading_flowrate: Unit
                Speed at which volume is added to cartridge.
            settle_time: Unit
                Duration for which the solvent remains on the cartridge
                before a pressure mode is applied.
            processing_time: Unit
                Duration for which pressure is applied to the cartridge
                after `settle_time` has elapsed.
            flow_pressure: Unit
                Pressure applied to the column.
            destination_well: Well
                Destination well for eluate.  Required parameter for
                each `elute` mobile phase parameter

    """

    builders = SPEBuilders()

    def __init__(
        self,
        well,
        cartridge,
        pressure_mode,
        load_sample,
        elute,
        condition,
        equilibrate,
        rinse,
    ):
        json_dict = {
            "object": well,
            "cartridge": cartridge,
            "pressure_mode": pressure_mode,
            "condition": condition,
            "load_sample": load_sample,
            "rinse": rinse,
            "elute": elute,
            "equilibrate": equilibrate,
        }

        super(SPE, self).__init__(op="spe", data=json_dict)


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
        json_dict = {
            "object": object,
            "volume": volume,
            "dataref": dataref,
            "measurement": measurement,
        }
        super(MeasureConcentration, self).__init__(
            op="measure_concentration", data=json_dict
        )


class Sonicate(Instruction):
    """
    Sonicate wells using high intensity ultrasonic vibrations.

    Parameters
    ----------
    wells : Well or WellGroup or list(Well)
       Wells to be sonicated
    duration : Unit or str
        Duration for which to sonicate wells
    mode: Enum({"bath", "horn"})
        Sonicating method to be used, must be "horn" or "bath". Sonicate
        mode "horn" uses metal probe to create a localized shear force
        directly in the sample media; "bath" mode applies ultrasound to
        wells held inside a bath.
    temperature: Unit or str, optional
        Temperature at which the sample is kept during sonication. Optional,
        defaults to ambient
    frequency: Unit or str, optional
        Frequency of the ultrasonic wave, usually indicated in kHz.
        Optional; defaults to the most commonly used frequency for each
        mode: 20 kHz for `horn`, and 40 kHz for `bath` mode
    mode_params: Dict
        Dictionary containing mode parameters for the specified mode.

    """

    def __init__(self, wells, duration, mode, mode_params, frequency, temperature):
        json_dict = {
            "wells": wells,
            "duration": duration,
            "frequency": frequency,
            "mode": mode,
            "mode_params": mode_params,
        }
        if temperature:
            json_dict["temperature"] = temperature
        super(Sonicate, self).__init__(op="sonicate", data=json_dict)


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
            "labels": labels,
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

    def __init__(
        self,
        dataref,
        object,
        groups,
        interval=None,
        num_intervals=None,
        temperature=None,
        shake_before=None,
    ):
        spec = {
            "dataref": dataref,
            "object": object,
            "groups": groups,
            "interval": interval,
            "num_intervals": num_intervals,
            "temperature": temperature,
            "shake_before": shake_before,
        }

        super(Spectrophotometry, self).__init__(op="spectrophotometry", data=spec)


class LiquidHandle(Instruction):
    """Manipulates liquids within locations

    A liquid handle instruction is constructed as a list of locations, where
    each location consists of the well location and the tip transports carried
    out within the well.

    Each liquid handle instruction corresponds to a single tip or set of tips.

    Parameters
    ----------
    locations : list(dict)
        See Also :meth:`LiquidHandle.builders.location`
    shape : dict, optional
        See Also :meth:`LiquidHandle.builders.shape`
    mode : str, optional
        the liquid handling mode
    mode_params : dict, optional
        See Also :meth:`LiquidHandle.builders.instruction_mode_params`
    informatics : list(Informatics), optional
        List of Informatics describing the intended aliquot effects upon
        completion of this instruction.
    """

    builders = LiquidHandleBuilders()

    def __init__(
        self, locations, shape=None, mode=None, mode_params=None, informatics=None
    ):
        data = {
            "locations": locations,
            "shape": shape,
            "mode": mode,
            "mode_params": mode_params,
        }

        super(LiquidHandle, self).__init__(
            op="liquid_handle", data=data, informatics=informatics
        )
