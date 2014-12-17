import json
from autoprotocol.util import make_dottable_dict

def kunkel_kinase(protocol, refs, params):
    params = make_dottable_dict(params)

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
