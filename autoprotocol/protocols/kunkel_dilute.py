import json
from autoprotocol.container import WellGroup
from autoprotocol.util import make_dottable_dict

def kunkel_dilute(protocol, refs, params):
    params = make_dottable_dict(params)
    dilute_wells = refs["diluted_oligo_plate"].wells_from(params.dilution_start,
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
        print json.dumps(protocol.as_dict(), indent=4)

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(kunkel_dilute)
