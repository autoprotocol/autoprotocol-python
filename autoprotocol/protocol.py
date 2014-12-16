from .container import Container, Well, WellGroup
from .container_type import ContainerType, _CONTAINER_TYPES
from .unit import Unit
from .instruction import *

class Ref(object):
    """Protocol objects contain a list of Ref objects which are encoded into
    JSON representing refs in the final protocol generated

    Example
    -------
        Ref("plate_name", {"new": "96-pcr", "store": {"where": "cold_4"}}, Container(None, "96-pcr"))

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
        if storage and storage in ["ambient", "cold_20", "cold_4", "warm_37"] and not discard:
            opts["store"] = {"where": storage}
        elif discard and not storage:
            opts["discard"] = discard
        else:
            raise ValueError("You must specify either a valid storage \
                            temperature or set discard=True for a container")
        self.refs[name] = Ref(name, opts, container)
        return container

    def refify(self, op_data):
        """Used to convert strings into their proper objects or vice versa

        Parameters
        ----------
        op_data : str, dict, list, Well, WellGroup, Unit, Container
            data to be "reffed"
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

        Raises
        ------

        """
        return {
            "refs": dict(map(lambda (k, v): (k, v.opts), self.refs.items())),
            "instructions": map(lambda x: self.refify(x.data),
                                self.instructions)
        }

    def pipette(self, groups):
        """

        Parameters
        ----------
        groups : list of dicts

        Returns
        -------

        Raises
        ------

        """
        if len(self.instructions) > 0 and self.instructions[-1].op == 'pipette':
            self.instructions[-1].groups += groups
        else:
            self.instructions.append(Pipette(groups))

    def distribute(self, source, dest, volume, allow_carryover=False):
        """

        Parameters
        ----------
        source : Well, WellGroup
        dest : Well, WellGroup
        volume : str, Unit
        allow_carryover : bool, optional

        Returns
        -------

        Raises
        ------

        """
        opts = {}
        if isinstance(volume, Unit):
            volume = str(volume)
        elif type(volume) != str:
            raise RuntimeError("volume for transfer must be expressed in as a \
                                string with the format 'value:unit' or as a \
                                Unit")
        opts["allow_carryover"] = allow_carryover
        if isinstance(source, WellGroup) and isinstance(dest, WellGroup):
            dists = self.fill_wells(dest, source, volume)
            groups = []
            for d in dists:
                groups.append(
                    {"distribute": {"from": d["from"],
                                    "to": d["to"],
                                    "allow_carryover": allow_carryover
                                    }
                    }
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
        """

        Parameters
        ----------
        source : Well, WellGroup
        dest : Well, WellGroup
        volume : str, Unit
        mix_after : bool, optional
        mix_vol : str, optional
        repetitions : int, optional
        flowrate : str, optional

        Returns
        -------

        Raises
        ------
        RuntimeError
            if transferring from WellGroup to WellGroup that have different
            number of wells
        RuntimeError
            if

        """
        opts = []
        if isinstance(volume, Unit):
            volume = str(volume)
        elif not isinstance(volume, basestring):
            raise RuntimeError('volume for transfer must be expressed in as a \
                               string with the format "value:unit" or as a \
                               Unit')
        if isinstance(source, WellGroup) and isinstance(dest, WellGroup):
            if len(source.wells) != len(dest.wells):
                raise RuntimeError("source and destination WellGroups do not \
                                    have the same number of wells and transfer \
                                    cannot happen one to one")
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
        """

        Parameters
        ----------
        well : str, Well
        volume : str, Unit, optional
        speed : str, Unit, optional
        repetitions : int, optional


        Returns
        -------

        Raises
        ------

        """
        if isinstance(well, Well):
            well = self.refify(well)
        elif isinstance(well, WellGroup):
            for w in well.wells:
                self.mix(w, volume, speed, repetitions)
        if isinstance(volume, Unit):
            volume = self.refify(volume)
        opts = {
            "well": well,
            "volume": volume,
            "speed": speed,
            "repetitions": repetitions
        }
        self.pipette([{"mix": [opts]}])

    def spin(self, ref, speed, duration):
        """

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

    def thermocycle(self, ref, groups, volume=None, dataref=None, dyes=None, melting=None):
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
            raise AttributeError("groups for thermocycling "
                "must be a list of cycles in the form of "
                "[{'cycles':___, 'steps': [{'temperature':___,"
                "'duration':___, }]}, { ... }, ...]")
        self.instructions.append(Thermocycle(ref, groups, volume, dataref, dyes, melting))

    def thermocycle_ramp(self, ref, start_temp, end_temp, time,
                         step_duration="60:second"):
        """

        Parameters
        ----------
        ref : str, Ref
        start_temp : str, Unit
        end_temp : str, Unit
        time : str, Unit
        step_duration : str, Unit, optional

        Returns
        -------

        Raises
        ------

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
        """

        Parameters
        ----------
        ref : str, Ref
        where : str
        duration : str, Unit
        shaking : bool, optional

        Returns
        -------

        Raises
        ------

        """
        self.instructions.append(Incubate(ref, where, duration, shaking))

    # mag adapter steps must be followed by pipette instructions
    def plate_to_mag_adapter(self, ref, duration):
        """utilizes the Pipette instruction to transfer a plate to the magnetized
        slot on the liquid handler

        Parameters
        ----------
        ref : str, Ref
        duration : str, Unit
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

    def fluorescence(self, ref, wells, excitation, emission, dataref, flashes=25):
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
                    raise RuntimeError("no well in source group has more than %s"
                                        % str(volume))
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
        for k,v in refs.items():
            if isinstance(v, Container):
                containers[k] = v
            else:
                containers[k] = self.ref(k, v["id"], v["type"], storage=v["storage"],
                                        discard=v["discard"])
        return containers

    def make_well_references(self, params):
        parameters = {}
        for k,v in params.items():
            if "/" in str(v):
                parameters[k] = self.refs[v.rsplit("/")[0]].container.well(v.rsplit("/")[1])
            else:
                parameters[k] = v
        return parameters
