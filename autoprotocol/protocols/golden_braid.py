from autoprotocol.util import make_dottable_dict
from autoprotocol.unit import Unit

def golden_braid(protocol, params):
    '''
    Template for golden_braid_config.json file

    {
        "parameters": {
            "resources": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_4",
                "discard": false
            },
            "destination_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_4",
                "discard": false
            },
            "reaction_start": "destination_plate/A1",
            "MM_loc": "resources/A3",
            "T4_ligase": "resources/C1",
            "enzyme": "resources/C2",
            "backbone": "resources/A1",
            "buffer": "resources/D1",
            "fragment_1": "resources/B1",
            "fragment_2": "resources/B2",
            "fragment_3": "resources/B3",
            "fragment_4": "resources/B4",
            "fragment_5": "resources/B5",
            "reaction_number": 10,
            "backbone_vol": "1:microliter",
            "enzyme_vol": "0.3:microliter",
            "ligase_vol": "0.6:microliter",
            "buffer_vol": "1:microliter",
            "fragment_vol": "3:microliter",
            "water_vol": "2:microliter",
            "ligation_time": "10:minute",
            "deactivation_time": "5:minute",
            "deactivation_temp": "65:celsius",
        }
    }
    '''

    params = make_dottable_dict(params)
    refs = make_dottable_dict(params.refs)

    MM_vol = Unit.fromstring(params.backbone_vol) + Unit.fromstring(params.enzyme_vol) + Unit.fromstring(params.buffer_vol) + Unit.fromstring(params.ligase_vol) + Unit.fromstring(params.fragment_vol) + Unit.fromstring(params.water_vol)
    # make master mix
    protocol.transfer(params.backbone, params.MM_loc, Unit.fromstring(params.backbone_vol) * Unit((params.reaction_number + 2),"microliter"))
    protocol.transfer(params.T4_ligase, params.MM_loc, Unit.fromstring(params.ligase_vol) * Unit((params.reaction_number + 2),"microliter"))
    protocol.transfer(params.enzyme, params.MM_loc, Unit.fromstring(params.enzyme_vol) * Unit((params.reaction_number + 2),"microliter"))
    protocol.transfer(params.buffer, params.MM_loc, Unit.fromstring(params.buffer_vol) * Unit((params.reaction_number + 2),"microliter"))

    # distribute master mix
    protocol.distribute(params.MM_loc,
        refs.destination_plate.wells_from(params.reaction_start,
        params.reaction_number), MM_vol )

    protocol.seal("destination_plate")

    protocol.thermocycle("destination_plate", [
        {"cycles": 1, "steps": [
            {"temperature": "37:celsius", "duration": "2:minute"},
        ]},
        {"cycles": 1, "steps":[
            {"temperature": "16:celsius", "duration": "5:minute"},
        ]},
        {"cycles": 49, "steps": [
            {"temperature": "50:celsius", "duration": "10:minute"},
            {"temperature": "80:celsius", "duration": "5:minute"},
        ]},
        {"cycles": 1, "steps": [
            {"temperature": "12:celsius", "duration": "10:minute"},
        ]},
    ])

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(golden_braid)