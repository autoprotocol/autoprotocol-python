# Autoprotocol Python

[Autoprotocol](https://www.autoprotocol.org) is a standard way to express
experiments in life science. This repository contains a python library for
generating Autoprotocol, and a number of validated protocols.

## Installation

    $ git clone https://github.com/autoprotocol/autoprotocol-python
    $ cd autoprotocol-python
    $ python setup.py install

## Writing Protocols

```python
from autoprotocol import Protocol

p = Protocol()
bacteria = p.ref("bacteria", id="ct1xxxxx", cont_type="96-pcr", storage="cold_4")
p.incubate(bacteria, "warm_37", "30:minute")
p.transfer(bacteria.well("A1"), bacteria.well("A2"), "15:microliter")
```

## Running and Submitting Protocols
The protocols in the `autoprotocol.protocols` module can be run directly from
the command line, using a JSON configuration file to specify parameters. For
example, to run the Gibson assembly protocol:

    $ python -mautoprotocol.protocols.gibson_assembly gibson_config.json

Where `gibson_config.json` looks like:
```
{
  "refs": {
    "resources": {
      "id": <container id>,
      "type": "96-pcr",
      "storage": "cold_20"
    },
    "destination_plate": {
      "id": null,
      "type": "96-pcr",
      "storage": "cold_4",
      "discard": false
    }
  },
  "parameters": {
    "backbone_loc": "resources/A1",
    "insert1_loc": "resources/A2",
    "insert2_loc": "resources/A3",
    "gibson_mix_loc": "resources/A4",
    "final_mix_loc": "resources/A5",
    "destination_well": "destination_plate/A1",
    "backbone_volume": "5:microliter",
    "insert1_volume": "2.5:microliter",
    "insert2_volume": "2.5:microliter",
    "gibson_mix_volume": "10:microliter",
    "gibson_reaction_time": "40:minute"
  }
}
```

Running the protocol will produce JSON-formatted autoprotocol output on
standard out. To submit a protocol to transcriptic.com to be run or analyzed,
use the [Transcriptic Runner](http://github.com/transcriptic/runner):

    $ python -m autoprotocol.protocols.gibson_assembly gibson_config.json \
        | transcriptic analyze

## Contributing

The easiest way to contribute is to fork this repository and submit a pull
request.  You can also write an email to us if you want to discuss ideas or
bugs.

- Max Hodak: max@transcriptic.com
- Jeremy Apthorp: jeremy@transcriptic.com
- Tali Herzka: tali@transcriptic.com

autoprotocol-python is BSD licensed (see LICENSE). Before we can accept your
pull request, we require that you sign a CLA (Contributor License Agreement)
allowing us to distribute your work under the BSD license. Email one of the
authors listed above for more details.
