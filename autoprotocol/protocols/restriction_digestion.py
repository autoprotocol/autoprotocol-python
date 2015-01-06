import json
from autoprotocol.util import make_dottable_dict

def restriction_digest(protocol, params):
    '''
    Template for restriction_digest_config.json file
    (change or add to defaults for your run):
    {
        "parameters":{
            "enzymes": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_20",
                "discard": false
            },
            "backbone": {
                "id": null,
                "type": "micro-1.5",
                "storage": "cold_20",
                "discard": false
            },
            "insert": {
                "id": null,
                "type": "micro-1.5",
                "storage": "cold_20",
                "discard": false
            },
            "dig_buffer": {
                "id": null,
                "type": "micro-1.5",
                "storage": "cold_20",
                "discard": false
            },
            "water": {
                "id": null,
                "type": "micro-1.5",
                "storage": "cold_4",
                "discard": false
            },
            "destination_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_4",
                "discard": false
            },
            "enzyme_1": "enzymes/H12",
            "enzyme_2": "enzymes/C10",
            "enzyme_3": "enzymes/A3",
            "enzyme_4": "enzymes/D7",
            "cut_backbone": "destination_plate/A1",
            "cut_insert": "destination_plate/A2",
            "enzyme_vol": "3:microliter",
            "source_DNA_vol": "5:microliter",
            "buffer_vol": "1:microliter",
            "water_vol": "2:microliter",
            "digestion_time": "10:minute",
            "digestion_temp": "37:celsius",
            "deactivation_time": "5:minute",
            "deactivation_temp": "80:celsius"
        }
    }
    '''
    params = make_dottable_dict(params)
    refs = make_dottable_dict(params.refs)

    protocol.transfer(refs.backbone.well(0), params.cut_backbone, params.source_DNA_vol)
    protocol.transfer(refs.insert.well(0), params.cut_insert, params.source_DNA_vol)

    protocol.transfer(refs.dig_buffer.well(0), params.cut_insert, params.buffer_vol)
    protocol.transfer(refs.dig_buffer.well(0), params.cut_backbone, params.buffer_vol)

    protocol.transfer(refs.water.well(0), params.cut_backbone, params.water_vol)
    protocol.transfer(refs.water.well(0), params.cut_insert, params.water_vol)

    protocol.transfer(params.enzyme_1, params.cut_backbone, params.enzyme_vol)
    protocol.transfer(params.enzyme_2, params.cut_backbone, params.enzyme_vol,
        mix_after=True, mix_vol="5:microliter")
    protocol.transfer(params.enzyme_3, params.cut_insert, params.enzyme_vol,
        mix_after=True, mix_vol="5:microliter")
    protocol.transfer(params.enzyme_4, params.cut_insert, params.enzyme_vol,
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

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(restriction_digest)