from .container import Container, Well, WellGroup
from .container_type import ContainerType, _CONTAINER_TYPES
from .unit import Unit
from .instruction import *


class Ref(object):
    """Protocol objects contain a list of Ref objects which are encoded into
    JSON representing refs in the final protocol generated

    Example
    -------
        Ref("plate_name", {"new": "96-pcr", "store": {"where": "cold_4"}},
            Container(None, "96-pcr"))

    becomes:

        "protocol":{
            "refs":{
                "plate_name":{
                    "new": "96-pcr",
                    "store": {
                        "where": "cold_4",
                        "shaking": false
                    }
                }
            }
            "instructions":[{ ... }]
        }

    Parameters
    ----------
    name : str
        the name or label of the container_type
    opts : dict
        dict containing attributes of the container such as
        storage and container type
    container : Container
        A Container object to be associated with this Ref

    Attributes
    ----------
    name : str
        the name or label of the container_type
    opts : dict
        dict containing attributes of the container such as
        storage and container type
    container : Container
        A Container object to be associated with this Ref
    """
    def __init__(self, name, opts, container):
        assert "/" not in name
        self.name = name
        self.opts = opts
        self.container = container


class Protocol(object):
    """Protocol objects contain lists of Ref objects and Instruction objects

    Parameters
    ----------
    refs : list of Refs
        list of Ref objects which are references to containers associated
        with this particular protocol
    instructions : list of Instructions, optional
        list of Instruction objects

    Attributes
    ----------
    refs : list of Refs
        list of Ref objects which are references to containers associated
        with this particular protocol
    instructions : list of Instructions, optional
        list of Instruction objects
    """

    def __init__(self, refs=[], instructions=None):
        super(Protocol, self).__init__()
        self.refs = {}
        for ref in refs:
            self.refs[ref.name] = ref
        self.instructions = instructions if instructions is not None else []

    def container_type(self, shortname):
        """converts a ContainerType shortname into a ContainerType object

        Parameters
        ----------
        shortname : {"384-flat", "384-pcr", "96-flat", "96-pcr", "96-deep",
                    "micro-2.0", "micro-1.5"}
            string representing one of the ContainerTypes in the _CONTAINER_TYPES
            dictionary

        Returns
        -------
        ContainerType
            Returns a Container type object corresponding to the shortname
            passed to the function.  If a ContainerType object is passed,
            that same ContainerType is returned.

        Raises
        ------
        ValueError
            if an unknown ContainerType shortname is passed as a parameter
        """
        if shortname in _CONTAINER_TYPES:
            return _CONTAINER_TYPES[shortname]
        elif isinstance(shortname, ContainerType):
            return shortname
        else:
            raise ValueError("Unknown container type %s (known types=%s)" %
                             (shortname, str(_CONTAINER_TYPES.keys())))

    def ref(self, name, id=None, cont_type=None, storage=None, discard=None):
        """appends a Ref object to the list of Refs associated with this protocol
        and returns a Container with the id, container type and storage or
        discard conditions specified.

        Example
        -------
        sample_ref = ref("sample_plate", id=None, cont_type="96-pcr", discard=True)

        returns a Container object using Container(None, "96-pcr")

        Parameters
        ----------
        name : str
            name of the container/ref being created
        id : str
            id of the container being created, from your organization's
            inventory on http://secure.transcriptic.com.  Strings representing
            ids begin with "ct"
        cont_type : str, ContainerType
            container type of the Container object that will be generated
        storage : {"ambient", "cold_20", "cold_4", "warm_37"}, optional
            temperature the container being referenced should be stored at after
            a run is completed.  Either a storage condition must be specified or
            discard must be set to True.
        discard : bool, optional
            if no storage condition is specified and discard is set to True,
            the container being referenced will be discarded after a run
        Returns
        -------
        container : Container
            Container object generated from the id and container type provided
        Raises
        ------
        ValueError
            if no container type is provided
        ValueError
            if no discard or storage condition is provided

        """
        assert name not in self.refs
        assert storage or discard
        opts = {}
        cont_type = self.container_type(cont_type)
        if id:
            opts["id"] = id
        else:
            opts["new"] = cont_type.shortname
        if not cont_type:
            raise ValueError("You a container type must always be specified")
        else:
            container = Container(id, cont_type)
        if storage in ["ambient", "cold_20", "cold_4", "warm_37"] and \
                not discard:
            opts["store"] = {"where": storage}
        elif discard and not storage:
            opts["discard"] = discard
        else:
            raise ValueError("You must specify either a valid storage "
                             "temperature or set discard=True for a container")
        self.refs[name] = Ref(name, opts, container)
        return container

    def refify(self, op_data):
        """Used to convert objects or collections of objects into their string
        representations for the purposes of JSON encoding

        Example
        -------
            protocol.refify(Unit(3,"microliter"))
        becomes
            "3:microliter"

            protocol.refify(sample_container.well("A1"))
        becomes
            "sample_container/A1"

        Parameters
        ----------
        op_data : str, dict, list, Well, WellGroup, Unit, Container
            data to be "reffed"

        Returns
        -------
        op_data : str, dict, list, Well, WellGroup, Unit, Container
            original data is returned if it is not of a type that can be
            "refified"
        dict
            if op_data is a dict, a dict is returned with the same keys as
            op_data and values reffified according to their type
        list
            if op_data is a list, a list is returned with each object reffed
            according to its type
        str
            op_data of types Well, WellGroup, Container and Unit is returned
            as a string representation of that object

        """
        if type(op_data) is dict:
            return {k: self.refify(v) for k, v in op_data.items()}
        elif type(op_data) is list:
            return [self.refify(i) for i in op_data]
        elif isinstance(op_data, Well):
            return self._ref_for_well(op_data)
        elif isinstance(op_data, WellGroup):
            return [self._ref_for_well(w) for w in op_data.wells]
        elif isinstance(op_data, Container):
            return self._ref_for_container(op_data)
        elif isinstance(op_data, Unit):
            return str(op_data)
        else:
            return op_data

    def append(self, instructions):
        """appends instruction to the list of Instruction object associated
        with this protocol

        Parameters
        ----------
        instructions : Instruction
            Instruction object to be appended
        """
        if type(instructions) is list:
            self.instructions.extend(instructions)
        else:
            self.instructions.append(instructions)

    def as_dict(self):
        """
        Returns
        -------
        dict
            dict with keys "refs" and "instructions", each of which contain
            the "refified" contents of their corresponding Protocol attribute
        """
        return {
            "refs": dict(map(lambda (k, v): (k, v.opts), self.refs.items())),
            "instructions": map(lambda x: self.refify(x.data),
                                self.instructions)
        }

    def pipette(self, groups):
        """Takes groups to be passed to a Pipette object which is then appended
        to the instructions attribute of this Protocol

        Parameters
        ----------
        groups : list of dicts
            a list of "distribute" and/or "transfer" instructions to be passed to a
            Pipette object, which is then appended to this protocol's
            instructions attribute
        """
        if len(self.instructions) > 0 and \
                self.instructions[-1].op == 'pipette':
            self.instructions[-1].groups += groups
        else:
            self.instructions.append(Pipette(groups))

    def distribute(self, source, dest, volume, allow_carryover=False):
        """Allows encoding of distribute groups representing liquid handling
        from one or multiple wells to one or multiple other wells.

        Parameters
        ----------
        source : Well, WellGroup
            Well or wells to distribute liquid from.  If passed as a WellGroup
            with set_volume() called on it, liquid will be automatically be drawn
            from the wells specified using the fill_wells function
        dest : Well, WellGroup
            Well or wells to distribute liquid to
        volume : str, Unit
            volume of liquid to be distributed to each destination well
        allow_carryover : bool, optional
            specify whether the same pipette tip can be used to aspirate more
            liquid from source wells after the previous volume aspirated has
            been depleted

        Raises
        ------
        RuntimeError
            if volume is not expressed either as a string with the format
            "value:unit" or as a Unit object
        """
        opts = {}
        if isinstance(volume, Unit):
            volume = str(volume)
        elif not isinstance(volume, basestring):
            raise RuntimeError("volume for transfer must be expressed in as a \
                                string with the format 'value:unit' or as a \
                                Unit")
        opts["allow_carryover"] = allow_carryover
        if isinstance(source, WellGroup) and isinstance(dest, WellGroup):
            dists = self.fill_wells(dest, source, volume)
            groups = []
            for d in dists:
                groups.append(
                    {"distribute": {
                        "from": d["from"],
                        "to": d["to"],
                        "allow_carryover": allow_carryover
                    }}
                )
            self.pipette(groups)
        elif isinstance(source, Well) and isinstance(dest, WellGroup):
            opts["from"] = self.refify(source)
            opts["to"] = []
            for well in dest.wells:
                opts["to"].append(
                    {"well": self.refify(well), "volume": volume})
            self.pipette([{"distribute": opts}])
        elif isinstance(source, Well) and isinstance(dest, Well):
            opts["from"] = self.refify(source)
            opts["to"] = []
            opts["to"].append({"well": self.refify(dest), "volume": volume})
            self.pipette([{"distribute": opts}])

    def transfer(self, source, dest, volume, mix_after=False,
                 mix_vol="20:microliter", repetitions=10,
                 flowrate="50:microliter/second"):
        """Allows encoding of transfer groups, each representing liquid handling
        from one specific well to another.  A new pipette tip is used between
        each transfer step.

        Parameters
        ----------
        source : Well, WellGroup
            Well or wells to transfer liquid from.  Expressing both source and
            dest as WellGroups appends transfer steps from each well in the
            source group to the well at the corresponding index in the list of
            destination wells.
        dest : Well, WellGroup
            Well or wells to transfer liquid to.
        volume : str, Unit
            volume of liquid to be transfered from one well to another
        mix_after : bool, optional
            set True to mix destination well using the same pipette tip
        mix_vol : str, optional
            volume to be aspirated and expelled during mixing
        repetitions : int, optional
            mix repititions
        flowrate : str, optional
            liquid flow rate during mixing

        Raises
        ------
        RuntimeError
            if transferring from WellGroup to WellGroup that have different
            number of wells
        RuntimeError
            if volume is passed as anything other than a string in the format
            "value:unit" or as a Unit object
        RuntimeError
            if source and/or destination wells are passed as anything other than
            Well or WellGroup objects
        """
        opts = []
        if isinstance(volume, Unit):
            volume = str(volume)
        elif not isinstance(volume, basestring):
            raise RuntimeError(
                "volume for transfer must be expressed in as a string with "
                "the format \"value:unit\" or as a Unit")
        if isinstance(source, WellGroup) and isinstance(dest, WellGroup):
            if len(source.wells) != len(dest.wells):
                raise RuntimeError(
                    "source and destination WellGroups do not have the same "
                    "number of wells and transfer cannot happen one to one")
            else:
                for s, d in zip(source.wells, dest.wells):
                    xfer = {
                        "from": self.refify(s),
                        "to": self.refify(d),
                        "volume": volume
                    }
                    if mix_after:
                        xfer["mix_after"] = {
                            "volume": mix_vol,
                            "repetitions": repetitions,
                            "speed": flowrate
                        }
                    opts.append(xfer)
        elif isinstance(source, Well) and isinstance(dest, WellGroup):
            for d in dest.wells:
                xfer = {
                    "from": self.refify(source),
                    "to": self.refify(d),
                    "volume": volume
                }
                if mix_after:
                    xfer["mix_after"] = {
                        "volume": mix_vol,
                        "repetitions": repetitions,
                        "speed": flowrate
                    }
                opts.append(xfer)
        elif isinstance(source, Well) and isinstance(dest, Well):
            xfer = {
                "from": self.refify(source),
                "to": self.refify(dest),
                "volume": volume
            }
            if mix_after:
                xfer["mix_after"] = {
                    "volume": mix_vol,
                    "repetitions": repetitions,
                    "speed": flowrate
                }
            opts.append(xfer)
        else:
            raise RuntimeError("transfer function must take Well or WellGroup "
                               "objects")
        self.pipette([{"transfer": opts}])

    def mix(self, well, volume="50:microliter", speed="50:microliter/second",
            repetitions=10):
        """Mix specified well using a new pipette tip

        Parameters
        ----------
        well : str, Well
            well to be mixed
        volume : str, Unit, optional
            volume of liquid to be aspirated and expelled during mixing
        speed : str, Unit, optional
            flowrate of liquid during mixing
        repetitions : int, optional
            number of times to aspirate and expell liquid during mixing
        """
        opts = {
            "well": well,
            "volume": volume,
            "speed": speed,
            "repetitions": repetitions
        }
        self.pipette([{"mix": [opts]}])

    def spin(self, ref, speed, duration):
        """appends a Spin Instruction to the instructions list

        Parameters
        ----------
        ref : str, Ref
        speed: str, Unit
        duration: str, Unit

        Returns
        -------

        Raises
        ------

        """
        self.instructions.append(Spin(ref, speed, duration))

    def thermocycle(self, ref, groups,
                    volume=None,
                    dataref=None,
                    dyes=None,
                    melting=None):
        """

        Parameters
        ----------
        ref : str, Ref
        groups : list of dicts
        volume : str, Unit, optional
        dataref : str, optional
        dyes : list, optional
        melting : str, Unit, optional

        Returns
        -------

        Raises
        ------

        """
        if not isinstance(groups, list):
            raise AttributeError(
                "groups for thermocycling must be a list of cycles in the "
                "form of [{'cycles':___, 'steps': [{'temperature':___,"
                "'duration':___, }]}, { ... }, ...]")
        self.instructions.append(
            Thermocycle(ref, groups, volume, dataref, dyes, melting))

    def thermocycle_ramp(self, ref, start_temp, end_temp, time,
                         step_duration="60:second"):
        """Appends instructions representing a thermocyle ramp-up or ramp-down
        protocol based on start_temp and end_temp

        Parameters
        ----------
        ref : str, Ref
            Plate to be thermocycled
        start_temp : str, Unit
            starting temperature to ramp up or down from
        end_temp : str, Unit
            final temperature to ramp up or down to
        time : str, Unit
            total duration of thermocycle protocol
        step_duration : str, Unit, optional
            individual temperature step duration
        """
        start_temp = int(Unit.fromstring(start_temp).value)
        end_temp = int(Unit.fromstring(end_temp).value)
        time = int(Unit.fromstring(time).value)
        num_steps = time // Unit.fromstring(step_duration).value
        groups = []
        step_size = (end_temp - start_temp) // num_steps
        assert num_steps > 0
        for i in range(0, int(num_steps)):
            groups.append({
                "cycles": 1,
                "steps": [{
                    "temperature": "%d:celsius" % (start_temp + i * step_size),
                    "duration": step_duration,
                }]
            })

        self.instructions.append(Thermocycle(ref, groups))

    def incubate(self, ref, where, duration, shaking=False):
        self.instructions.append(Incubate(ref, where, duration, shaking))

    # mag adapter steps must be followed by pipette instructions
    def plate_to_mag_adapter(self, ref, duration):
        """utilizes the Pipette instruction to transfer a plate to the magnetized
        slot on the liquid handler

        Parameters
        ----------
        ref : str, Ref
            plate to be transferred to magnetic adapter
        duration : str, Unit
            duration for plate to incubate on the magentic adapter (with no
            pipetting occuring)
        """
        sep = Pipette([])
        sep.data["x-magnetic_separate"] = {
            "object": ref,
            "duration": duration
        }
        self.instructions.append(sep)

    def plate_off_mag_adapter(self, ref):
        """This function utilizes the Pipette instruction to transfer a plate
        off of the magnetic block slot on the liquid handler to a normal, non-
        magnetized slot

        Parameters
        ----------
        ref : str, Ref
            plate to be removed from magentic block
        """
        self.instructions.append(Pipette([]))

    def absorbance(self, ref, wells, wavelength, dataref, flashes=25):
        """This step transfers the plate to the plate reader and reads the
        absorbance for the indicated wavelength for the indicated wells.
        Appends an Absorbance instruction to the list of instructions for this
        Protocol object.

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
        if isinstance(wells, WellGroup):
            wells = wells.indices()
        self.instructions.append(
            Absorbance(ref, wells, wavelength, dataref, flashes))

    def fluorescence(self, ref, wells, excitation, emission, dataref,
                     flashes=25):
        """This step transfers the plate to the plate reader and reads the
        fluoresence for the indicated wavelength for the indicated wells.
        Appends an Fluorescence instruction to the list of instructions for this
        Protocol object.

        Parameters
        ----------
        ref : str, Ref
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
        if isinstance(wells, WellGroup):
            wells = wells.indices()
        self.instructions.append(
            Fluorescence(ref, wells, excitation, emission, dataref, flashes))

    def gel_separate(self, ref, matrix, ladder, duration, dataref):
        self.instructions.append(
            GelSeparate(ref, matrix, ladder, duration, dataref))

    def seal(self, ref):
        self.instructions.append(Seal(ref))

    def unseal(self, ref):
        self.instructions.append(Unseal(ref))

    def cover(self, ref, lid='standard'):
        self.instructions.append(Cover(ref, lid))

    def uncover(self, ref):
        self.instructions.append(Uncover(ref))

    def _ref_for_well(self, well):
        return "%s/%d" % (self._ref_for_container(well.container), well.idx)

    def _ref_for_container(self, container):
        for k, v in self.refs.iteritems():
            if v.container is container:
                return k

    def fill_wells(self, dst_group, src_group, volume):
        """This function is used to distribute liquid to a WellGroup, sourcing
        the liquid from a group of wells all containing the same substance.

        Parameters
        ----------
        dst_group : WellGroup
            WellGroup to distribute liquid to
        src_group : WellGroup
            WellGroup containing the substance to be distributed
        volume : str, Unit
            volume of liquid to be distributed to each destination well

        Returns
        -------
        distirbutes : list


        Raises
        ------
        RuntimeError
            if source wells run out of liquid before distributing to all
            designated destination wells

        """
        volume = Unit.fromstring(volume)
        src = None
        distributes = []
        for d in dst_group.wells:
            if len(distributes) == 0 or src.volume < volume:
                # find a src well with enough volume
                src = next(
                    (w for w in src_group.wells if w.volume > volume), None)
                if src is None:
                    raise RuntimeError(
                        "no well in source group has more than %s" %
                        str(volume))
                distributes.append({
                    "from": self.refify(src),
                    "to": []
                })
            distributes[-1]["to"].append({
                "well": self._ref_for_well(d),
                "volume": str(volume)
            })
            src.volume -= volume
            if d.volume:
                d.volume += volume
            else:
                d.volume = volume
        return distributes

    def ref_containers(self, refs):
        containers = {}
        for k, v in refs.items():
            if isinstance(v, Container):
                containers[str(k)] = v
            else:
                containers[str(k)] = \
                    self.ref(k, v["id"], v["type"], storage=v["storage"],
                             discard=v["discard"])
        return containers

    def make_well_references(self, params):
        parameters = {}
        for k, v in params.items():
            if isinstance(v, dict):
                parameters[k] = self.make_well_references(v)
            elif isinstance(v, list) and "/" in str(v[0]):
                parameters[k] = WellGroup([self.refs[i.rsplit("/")[0]].container.well(i.rsplit("/")[1]) for i in v])
            elif "/" in str(v):
                parameters[k] = self.refs[v.rsplit("/")[0]].container.well(v.rsplit("/")[1])
            else:
                parameters[k] = v
        return parameters
