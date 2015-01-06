import json
from autoprotocol.util import make_dottable_dict

def kunkel_kinase(protocol, params):
    '''
    Template for kunkel_kinase_config.json file
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
            "resource_plate": {
                "id": null,
                "type": "384-pcr",
                "storage": "cold_20",
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
            "kinase_time": "60:minute"
        }
    }
    '''

    params = make_dottable_dict(params)
    refs = params.refs

    oligo_wells = refs["oligo_plate"].wells_from(params.oligo_start, params.oligo_number, columnwise = True)
    kinased_wells = refs["kinased_oligo_plate"].wells_from("A1", params.oligo_number, columnwise = True)

    protocol.distribute(params.kinase_mix_loc.set_volume("47:microliter"), kinased_wells, params.kinase_MM_volume)

    protocol.transfer(oligo_wells, kinased_wells, params.conc_oligo_volume, mix_after = True)

    protocol.seal("kinased_oligo_plate")

    protocol.thermocycle("kinased_oligo_plate",
    [{"cycles": 1, "steps": [
        {"temperature": "37:celsius", "duration": params.kinase_time},
        ]}
    ])

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_kinase)
