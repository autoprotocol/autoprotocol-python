import json
from autoprotocol.util import make_dottable_dict

def gibson(protocol, refs, params):
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