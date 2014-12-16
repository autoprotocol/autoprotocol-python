import json
from autoprotocol.util import make_dottable_dict
from autoprotocol.unit import Unit

def restriction_digest(protocol, refs, params):
    params = make_dottable_dict(params)
    refs = make_dottable_dict(refs)

    protocol.transfer(refs.backbone.well(0), params.cut_backbone, params.source_DNA_vol)
    protocol.transfer(refs.insert.well(0), params.cut_insert, params.source_DNA_vol)

    protocol.transfer(refs.dig_buffer.well(0), params.cut_insert, params.buffer_vol)
    protocol.transfer(refs.dig_buffer.well(0), params.cut_backbone, params.buffer_vol)

    protocol.transfer(refs.water.well(0), params.cut_backbone, params.water_vol)
    protocol.transfer(refs.water.well(0), params.cut_insert, params.water_vol)

    protocol.transfer(params.XhoI, params.cut_backbone, params.enzyme_vol)
    protocol.transfer(params.EcoRI, params.cut_backbone, params.enzyme_vol,
        mix_after=True, mix_vol="5:microliter")
    protocol.transfer(params.MluI, params.cut_insert, params.enzyme_vol,
        mix_after=True, mix_vol="5:microliter")
    protocol.transfer(params.NheI, params.cut_insert, params.enzyme_vol,
        mix_after=True, mix_vol="5:microliter")


    protocol.seal("destination_plate")

    protocol.thermocycle("destination_plate", [
        {"cycles": 1, "steps": [
            {"temperature": params.digestion_temp, "duration": params.digestion_time},
        ]},
        {"cycles": 1, "steps": [
            {"temperature": params.deactivation_temp, "duration": params.deactivation_time},

        ]},
    ])

    print json.dumps(protocol.as_dict(), indent=4)

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(restriction_digest)