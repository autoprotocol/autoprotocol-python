import argparse
import json
import sys
from autoprotocol.util import make_dottable_dict
from autoprotocol.unit import Unit
from autoprotocol.container import Well, WellGroup


def bradford(protocol, refs, params):
    params = make_dottable_dict(params)
    refs = make_dottable_dict(refs)

    standard_wells = refs.standard_plate.wells_from(0,8,columnwise=True)
    wells_to_measure = refs.bradford_plate.wells_from(0, (len(standard_wells) *
        params.standard_replicates) +
        (params.sample_number * params.sample_replicates)
        + params.num_blanks, columnwise = True)

    wells_with_standard = wells_to_measure.wells[0:3*len(standard_wells)]
    sample_wells = wells_to_measure.wells[len(wells_with_standard):len(wells_to_measure)-3]
    blanks = wells_to_measure.wells[-1:-params.num_blanks]
    coomassie = WellGroup([])
    for name,ref in refs.items():
        if name.rsplit("_")[0] == "coomassie":
            coomassie.append(ref.well(0).set_volume('1500:microliter'))

    protein_samples = WellGroup([])
    for name,ref in refs.items():
        if name.split("_")[0] == "lysate":
            protein_samples.append(ref.well(0))
    protocol.distribute(coomassie,
        wells_to_measure,
        "198:microliter",
        allow_carryover=True)
    # make BSA standard on separate plate
    protocol.transfer(refs.BSA.well("A1"), standard_wells[0], "20:microliter")
    protocol.distribute(refs.water, WellGroup(standard_wells.wells[1:7]),
                        "10:microliter", allow_carryover=True)
    # serial diultion of BSA standard
    for idx in range(1, len(standard_wells.wells)):
        protocol.transfer(standard_wells.wells[idx - 1],
                          standard_wells.wells[idx], "10:microliter",
                          mix_after=True)

    standard_start = 0
    for i in range(0, params.standard_replicates):
        protocol.transfer(standard_wells,
                refs.bradford_plate.wells_from(standard_start, 8, columnwise=True),
                "2:microliter", mix_after=True)
        standard_start += 1

    start = 0
    end = 3
    for sample in protein_samples.wells:
        for i in range(start, end):
            protocol.transfer(sample, sample_wells[i], "2:microliter", mix_after=True)
        start += 3
        end += 3

    protocol.absorbance(refs.bradford_plate, wells_to_measure, "595:nanometer",
                        dataref="bradford")

    print json.dumps(protocol.as_dict(),indent=4)

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(bradford)
