import json
from autoprotocol.util import make_dottable_dict
from autoprotocol.protocols.kunkel_anneal import kunkel_anneal
from autoprotocol.protocols.kunkel_kinase import kunkel_kinase
from autoprotocol.protocols.kunkel_dilute import kunkel_dilute
from autoprotocol.protocols.kunkel_polymerize import kunkel_polymerize

def kunkel_complete(protocol, params):
    '''
    Template for kunkel_comlplete_config.json file
    **keep container names the same**
    (change or add to defaults for your run):
    {
        "parameters":{
            "oligo_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_20",
                "discard": false
            },
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
            "oligo_number": 12,
            "oligo_start": "oligo_plate/A1",
            "kinase_mix_loc": [
                "resource_plate/1",
                "resource_plate/2",
                "resource_plate/3",
                "resource_plate/4",
                "resource_plate/5",
                "resource_plate/6",
                "resource_plate/7"
            ],
            "kinase_incubation_time": "1:hour",
            "kinase_incubation_temp": "37:celsius",
            "kinase_MM_volume": "23:microliter",
            "conc_oligo_volume": "7:microliter",
            "mix_volume": "10:microliter",
            "kinased_start": "kinased_oligo_plate/A1",
            "kinase_time": "60:minute",
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
            "oligo_vol": "2:microliter",
            "ssDNA_mix_vol": "2.2:microliter",
            "ssDNA_mix_loc": "resource_plate/D1",
            "oligo_vol": "2:microliter",
            "oligos": [
                "diluted_oligo_plate/A1",
                "diluted_oligo_plate/B1",
                "diluted_oligo_plate/C1",
                "diluted_oligo_plate/D1",
                "diluted_oligo_plate/E1",
                "diluted_oligo_plate/F1",
                "diluted_oligo_plate/G1",
                "diluted_oligo_plate/H1",
                "diluted_oligo_plate/A2",
                "diluted_oligo_plate/B2"
            ],
            "polymerize_MM_vol": "2.2:microliter",
            "polymerize_MM_loc": "resource_plate/E1",
            "kunkel_number": 10,
            "reaction_start": "reaction_plate/A1"
        }
    }
    '''
    params = make_dottable_dict(params)

    kunkel_kinase(protocol, params)

    protocol.unseal("kinased_oligo_plate")

    kunkel_dilute(protocol, params)

    kunkel_anneal(protocol, params)

    protocol.unseal("reaction_plate")

    kunkel_polymerize(protocol, params)

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_complete)