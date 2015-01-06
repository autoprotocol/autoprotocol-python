import json
from autoprotocol.util import make_dottable_dict

def gibson(protocol, params):
    '''
    Template for gibson_config.json config file
    (change or add to defaults for your run):
    {
        "parameters":{
            "resources": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_20",
                "discard": false
            },
            "destination_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_4",
                "discard": false
            },
            "backbone_loc":"resources/A1",
            "insert1_loc": "resources/A2",
            "insert2_loc": "resources/A3",
            "gibson_mix_loc": "resources/A4",
            "final_mix_loc": "resources/A5",
            "destination_well" : "destination_plate/A1",
            "backbone_volume": "5:microliter",
            "insert1_volume": "2.5:microliter",
            "insert2_volume": "2.5:microliter",
            "gibson_mix_volume": "10:microliter",
            "gibson_reaction_time": "40:minute"
        }
    }
    '''
    params = make_dottable_dict(params)

        #transfer components of gibson to destination well on other PCR plate (which will later be sealed and thermocycled)
    protocol.transfer(params["backbone_loc"],params["destination_well"],params["backbone_volume"])
    protocol.transfer(params["insert1_loc"],params["destination_well"],params["insert1_volume"])
    protocol.transfer(params["insert2_loc"],params["destination_well"],params["insert2_volume"])
    protocol.transfer(params["gibson_mix_loc"],params["destination_well"],params["gibson_mix_volume"], mix_after=True)

    #plate must be sealed before thermocycling step
    protocol.seal("destination_plate")

    #gibson reaction
    protocol.thermocycle("destination_plate", [
        {"cycles": 1, "steps": [
            {"temperature": "50:celsius", "duration": params["gibson_reaction_time"]},
        ]},
        {"cycles": 1, "steps": [
            {"temperature": "8:celsius", "duration": "300:second"},

        ]},
    ])

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(gibson)