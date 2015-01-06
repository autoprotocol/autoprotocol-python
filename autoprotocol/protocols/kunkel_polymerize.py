import json
from autoprotocol.util import make_dottable_dict

def kunkel_polymerize(protocol, params):
    '''
    Template for kunkel_polymerize_config.json config file
    (change or add to defaults for your run):
    {
        "parameters":{
            "resource_plate": {
                "id": null,
                "type": "384-pcr",
                "storage": "cold_20",
                "discard": false
            },
            "reaction_plate": {
                "id": null,
                "type": "384-pcr",
                "storage": "ambient",
                "discard": false
            },
            "polymerize_MM_vol": "2.2:microliter",
            "polymerize_MM_loc": "resource_plate/E1",
            "kunkel_number": 10,
            "reaction_start": "reaction_plate/A1"
        }
    }
    '''
    params = make_dottable_dict(params)
    refs = params.refs

    reactions = refs["reaction_plate"].wells_from(params.reaction_start, params.kunkel_number, columnwise = True)

    for reaction in reactions:
        protocol.transfer(params.polymerize_MM_loc, reaction, params.polymerize_MM_vol, mix_after=True)

    protocol.seal("reaction_plate")

    protocol.incubate("reaction_plate", "ambient", "1.5:hour")

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_polymerize)
