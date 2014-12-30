import json

class Instruction(object):
    def __init__(self, data):
        super(Instruction, self).__init__()
        self.data = data
        self.__dict__.update(data)

    def json(self):
        return json.dumps(self.data, indent = 2)

class Pipette(Instruction):
    def __init__(self, groups):
        super(Pipette, self).__init__({
            "op": "pipette",
            "groups": groups
        })

    @staticmethod
    def _transferGroup(src, dest, vol, mix_after=False,
                 mix_vol="20:microliter", repetitions=10,
                 flowrate="100:microliter/second"):
        group = {
            "from": src,
            "to": dest,
            "volume": vol,
        }
        if mix_after:
            group["mix_after"] = {
                    "volume": mix_vol,
                    "repetitions": repetitions,
                    "speed": flowrate
            }
        return group

    @staticmethod
    def transfers(srcs, dests, vols, mix_after=False,
                 mix_vol="20:microliter", repetitions=10,
                 flowrate="100:microliter/second"):
        """
        Returns a valid list of pipette transfer groups.  This can be passed
        directly to the Pipette constructor as the "groups" argument.

        srcs  - [str] - List of ":ref/:well" to use as the transfer sources
        dests - [str] - List of ":ref/:well" to use as the transfer destinations
        vols  - [float] - List of volumes in microliters.  These should be bare numbers.
        """

        return [{
                "transfer": [Pipette._transferGroup(s, d, v, mix_after, mix_vol,
                            repetitions, flowrate) for (s, d, v) in
                            zip(srcs, dests, vols)],
        }]

class Spin(Instruction):
    def __init__(self, ref, speed, duration):
        super(Spin, self).__init__({
            "op": "spin",
            "object": ref,
            "speed": speed,
            "duration": duration
        })

class Thermocycle(Instruction):
    CHANNEL1_DYES  = ["FAM","SYBR"]
    CHANNEL2_DYES  = ["VIC","HEX","TET","CALGOLD540"]
    CHANNEL3_DYES  = ["ROX","TXR","CALRED610"]
    CHANNEL4_DYES  = ["CY5","QUASAR670"]
    CHANNEL5_DYES  = ["QUASAR705"]
    CHANNEL_DYES   = [CHANNEL1_DYES, CHANNEL2_DYES, CHANNEL3_DYES, CHANNEL4_DYES, CHANNEL5_DYES]
    AVAILABLE_DYES = [dye for channel_dye in CHANNEL_DYES for dye in channel_dye]

    def __init__(self, ref, groups, volume=None, dataref=None, dyes=None, melting=None):
        if dyes:
            keys = dyes.keys()
            if Thermocycle.find_invalid_dyes(keys):
                dyes = Thermocycle.convert_well_map_to_dye_map(dyes)
        if bool(dataref) != bool(dyes):
            raise ValueError("thermocycle instruction supplied `%s` without `%s`" % ("dataref" if bool(dataref) else "dyes", "dyes" if bool(dataref) else "dataref"))
        if melting and not dyes:
            raise ValueError("thermocycle instruction supplied `melting` without `dyes`: %s")
        super(Thermocycle, self).__init__({
            "op": "thermocycle",
            "object": ref,
            "groups": groups,
            "dataref": dataref,
            "volume": volume,
            "dyes": dyes,
            "melting": melting
        })

    @staticmethod
    def find_invalid_dyes(dyes):
        """
        Takes a set or list of dye names and returns the set that are not valid.

        dyes - [list or set]
        """

        return set(dyes).difference(set(Thermocycle.AVAILABLE_DYES))

    @staticmethod
    def convert_well_map_to_dye_map(well_map):
        """
        Takes a map of wells to the dyes it contains and returns a map of dyes to the list of wells that contain it.

        well_map - [{well:str}]
        """

        dye_names = reduce(lambda x,y: x.union(y), [set(v) for v in well_map.itervalues()])
        if Thermocycle.find_invalid_dyes(dye_names):
            raise ValueError("thermocycle instruction supplied the following invalid dyes: %s" % ", ".join(Thermocycle.find_invalid_dyes(dye_names)))
        dye_map = {dye:[] for dye in dye_names}
        for well,dyes in well_map.iteritems():
            for dye in dyes: dye_map[dye] += [well]
        return dye_map

class Incubate(Instruction):
    WHERE = ["ambient", "warm_37", "cold_4", "cold_20", "cold_80"]

    def __init__(self, ref, where, duration, shaking = False):
        if where not in self.WHERE:
            raise ValueError("specified `where` not contained in: %s" % ", ".join(self.WHERE))
        super(Incubate, self).__init__({
            "op": "incubate",
            "object": ref,
            "where": where,
            "duration": duration,
            "shaking": shaking
        })

class SangerSeq(Instruction):
    def __init__(self, ref, dataref):
        super(SangerSeq, self).__init__({
            "op": "sangerseq",
            "object": ref,
            "dataref": dataref
        })

class GelSeparate(Instruction):
    MATRICES = ['agarose(96,2.0%)', 'agarose(48,4.0%)', 'agarose(48,2.0%)', 'agarose(12,1.2%)', 'agarose(8,0.8%)']
    LADDERS = ['ladder1', 'ladder2']

    def __init__(self, ref, matrix, ladder, duration, dataref):
        if matrix not in self.MATRICES:
            raise ValueError("specified `matrix` not contained in: %s" % ", ".join(self.MATRICES))
        if ladder not in self.LADDERS:
            raise ValueError("specified `ladder` not contained in: %s" % ", ".join(self.LADDERS))
        super(GelSeparate, self).__init__({
            "op": "gel_separate",
            "ref": ref,
            "matrix": matrix,
            "ladder": ladder,
            "duration": duration,
            "dataref": dataref
        })

class Absorbance(Instruction):
    def __init__(self, ref, wells, wavelength, dataref, flashes = 25):
        super(Absorbance, self).__init__({
            "op": "absorbance",
            "object": ref,
            "wells": wells,
            "wavelength": wavelength,
            "num_flashes": flashes,
            "dataref": dataref
        })

class Fluorescence(Instruction):
    def __init__(self, ref, wells, excitation, emission, dataref, flashes = 25):
        super(Fluorescence, self).__init__({
            "op": "fluorescence",
            "object": ref,
            "wells": wells,
            "excitation": excitation,
            "emission": emission,
            "num_flashes": flashes,
            "dataref": dataref
        })

class Seal(Instruction):
    def __init__(self, ref):
        super(Seal, self).__init__({
            "op": "seal",
            "object": ref
        })

class Unseal(Instruction):
    def __init__(self, ref):
        super(Unseal, self).__init__({
            "op": "unseal",
            "object": ref
        })

class Cover(Instruction):
    def __init__(self, ref, lid):
        super(Cover, self).__init__({
            "op": "cover",
            "object": ref,
            "lid": lid
        })

class Uncover(Instruction):
    def __init__(self, ref):
        super(Uncover, self).__init__({
            "op": "uncover",
            "object": ref
        })
