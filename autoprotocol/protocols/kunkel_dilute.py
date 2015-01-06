import json
from autoprotocol.util import make_dottable_dict

def kunkel_dilute(protocol, params):
    '''
    Template for kunkel_dilute_config.json file
    (change or add to defaults for your run):
    {
        "parameters":{
            "kinased_oligo_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_20",
                "discard": false
            },
            "diluted_oligo_plate": {
                "id": null,
                "type": "96-flat",
                "storage": "cold_20",
                "discard": false
            },
            "H2O_1": {
                "id": null,
                "type": "micro-1.5",
                "storage": "ambient",
                "discard": false
            },
            "H2O_2": {
                "id": null,
                "type": "micro-1.5",
                "storage": "ambient",
                "discard": false
            },
            "H2O_3": {
                "id": null,
                "type": "micro-1.5",
                "storage": "ambient",
                "discard": false
            },
            "kinased_oligos": [
                "kinased_oligo_plate/A1",
                "kinased_oligo_plate/B1",
                "kinased_oligo_plate/C1",
                "kinased_oligo_plate/D1",
                "kinased_oligo_plate/E1",
                "kinased_oligo_plate/F1",
                "kinased_oligo_plate/G1",
                "kinased_oligo_plate/H1",
                "kinased_oligo_plate/A2",
                "kinased_oligo_plate/B2",
                "kinased_oligo_plate/C2",
                "kinased_oligo_plate/D2",
                "kinased_oligo_plate/E2",
                "kinased_oligo_plate/F2"
                ],
            "combos": [[2,8],[1,2,7],[3,5,12],[2,5,11],[2,6,8],[2,5,8],[4,5,13],[1,4,5,10],[2,11],[4,14]],
            "water": [
                "H2O_1/0",
                "H2O_2/0",
                "H2O_3/0"
            ],
            "water_vol": "198:microliter",
            "dilution_start": "diluted_oligo_plate/A1",
            "oligo_vol": "2:microliter"
        }
    }
    '''

    params = make_dottable_dict(params)
    refs = make_dottable_dict(params.refs)

    dilute_wells = refs.diluted_oligo_plate.wells_from(params.dilution_start,
                                        len(params.combos), columnwise = True)
    protocol.distribute(params.water.set_volume("1500:microliter"), dilute_wells, params.water_vol,
                        allow_carryover = True)
    oligos = params.kinased_oligos.wells

    for idx,combo in enumerate(params.combos):
        for i in combo:
            olig = oligos[i-1]
            protocol.transfer(olig,dilute_wells.wells[idx],params.oligo_vol,
                                mix_after = True)

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_dilute)
