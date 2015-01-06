import json
from autoprotocol.util import make_dottable_dict

def kunkel_anneal(protocol, params):
    '''
    Template for kunkel_anneal_config.json file
    (change or add to defaults for your run):
    {
        "parameters":{
            "diluted_oligo_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_20",
                "discard": false
            },
            "resource_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_20",
                "discard": false
            },
            "reaction_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "ambient",
                "discard": false
            },
            "ssDNA_mix_vol": "2.2:microliter",
            "ssDNA_mix_loc": "resource_plate/D1",
            "oligo_vol": "2:microliter",
            "oligos": [
                "diluted_oligo_plate/0",
                "diluted_oligo_plate/1",
                "diluted_oligo_plate/2",
                "diluted_oligo_plate/3",
                "diluted_oligo_plate/4",
                "diluted_oligo_plate/5",
                "diluted_oligo_plate/6",
                "diluted_oligo_plate/7",
                "diluted_oligo_plate/8",
                "diluted_oligo_plate/9",
                "diluted_oligo_plate/10"
            ]
        }
    }
    '''
    params = make_dottable_dict(params)
    refs = make_dottable_dict(params.refs)

    reaction_wells = refs["reaction_plate"].wells_from(0,len(params.oligos), columnwise=True)

    protocol.distribute(params.ssDNA_mix_loc,reaction_wells, params.ssDNA_mix_vol)

    for oligo,reaction in zip(params.oligos,reaction_wells.wells):
        protocol.transfer(oligo,reaction,params.oligo_vol,mix_after=True)

    protocol.seal("reaction_plate")

    protocol.thermocycle_ramp("reaction_plate","95:celsius", "25:celsius", "60:minute", step_duration="4:minute")

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_anneal)