from autoprotocol.util import make_dottable_dict
from autoprotocol.unit import Unit

def bead_purification(protocol, params):
    '''
    Template for bead_purification_params.json config file
    (change or add to defaults for your run):
    {
        "parameters": {
            "beads": {
                "id": null,
                "type": "micro-1.5",
                "storage": "cold_4",
                "discard": false
            },
            "resource_plate": {
                "id": null,
                "type": "96-deep",
                "storage": "cold_20",
                "discard": false
            },
            "sample_plate": {
                "id": null,
                "type": "96-pcr",
                "storage": "cold_4",
                "discard": false
            },
            "trash": {
                "id": null,
                "type": "96-deep",
                "storage": null,
                "discard": true
                },
            "sample_number": 12,
            "sample_start": "sample_plate/A1",
            "sample_volume": "20:microliter",
            "destination_start": "sample_plate/B1",
            "initial_incubation_time": "10:minute",
            "initial_incubation_temp": "ambient",
            "initial_mag_adapter_time": "2:minute",
            "ethanol_wash_vol": "60:microliter",
            "supernatant_removal_vol": "42:microliter",
            "wash_removal_vol": "90:microliter",
            "ethanol_air_dry_time": "15:minute",
            "ethanol_air_dry_temp": "ambient",
            "resuspension_time": "5:minute",
            "final_mag_adapter_time": "5:minute",
            "resuspension_vol": "50:microliter",
            "ethanol": "resource_plate/A1",
            "te": "resource_plate/A2"
        }
    }


    '''
    params = make_dottable_dict(params)
    refs = make_dottable_dict(params.refs)

    samples = refs.sample_plate.wells_from(
        params.sample_start,
        params.sample_number
    ).set_volume(params.sample_volume)
    destinations = refs.sample_plate.wells_from(
        params.destination_start, params.sample_number)
    bead_volume = Unit.fromstring(
        params.sample_volume) * Unit(1.8, "microliter")

    # Allow beads to come to room temperature

    # Resuspend the beads
    protocol.mix(refs.beads.well(0), volume="500:microliter")

    protocol.transfer(
        refs.beads.well(0),
        samples,
        bead_volume,
        mix_after=True,
        repetitions=20,
        mix_vol=bead_volume)

    # Let sit at RT for 10min, important, maybe longer, e.g. 20min
    protocol.incubate(
        refs.sample_plate,
        params.initial_incubation_temp,
        params.initial_incubation_time)

    # Put into magnetic adapter for 2 minutes. Should remain here.
    protocol.plate_to_mag_adapter(
        refs.sample_plate, params.initial_mag_adapter_time)

    for i, s in enumerate(samples.wells):
        # before adding ethanol for wash, remove all liquid from well while
        # plate is on magnet block
        protocol.transfer(
            s, refs.trash.well(i), params.supernatant_removal_vol)

        # wash with ethanol by mixing 25x, transfer supernatant to trash
        protocol.transfer(
            params.ethanol,
            s,
            params.ethanol_wash_vol,
            mix_after=True,
            mix_vol="50:microliter",
            repetitions=25)

        protocol.transfer(s, refs.trash.well(i), params.wash_removal_vol)

    # Air dry for 10 minutes (often this step takes longer than 10 minutes if
    # ethanol is not removed carefully enough)
    protocol.incubate(
        refs.sample_plate,
        params.ethanol_air_dry_temp,
        params.ethanol_air_dry_time)

    protocol.plate_off_mag_adapter(refs.sample_plate)

    # resuspend in TE
    protocol.transfer(
        params.te,
        samples,
        params.resuspension_vol,
        mix_after="True",
        repetitions=20,
        mix_vol=params.resuspension_vol)

    # incubate at ambient while plate is OFF the mag plate after resuspending
    # in TE
    protocol.incubate(refs.sample_plate, "ambient", params.resuspension_time)

    # Put back into magnetic adapter for 5min
    protocol.plate_to_mag_adapter(
        refs.sample_plate, params.final_mag_adapter_time)

    # Pipette 20ul to clean well
    protocol.transfer(samples, destinations, params.resuspension_vol)

if __name__ == '__main__':
    from autoprotocol.harness import run
    run(bead_purification)
