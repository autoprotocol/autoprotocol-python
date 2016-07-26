# Autoprotocol Python Library

[![Build Status](https://travis-ci.org/autoprotocol/autoprotocol-python.svg?branch=master)](https://travis-ci.org/autoprotocol/autoprotocol-python)
[![PyPI version](https://img.shields.io/pypi/v/autoprotocol.svg?maxAge=2592000)](https://pypi.python.org/pypi/autoprotocol)

### **[View Library Documentation on readthedocs.org](http://autoprotocol-python.readthedocs.org/en/latest/)**

[Autoprotocol](http://www.autoprotocol.org) is a standard way to express
experiments in life science. This repository contains a python library for
generating Autoprotocol.

## Installation

    $ git clone https://github.com/autoprotocol/autoprotocol-python
    $ cd autoprotocol-python
    $ python setup.py install

or, alternatively:

    $ pip install autoprotocol

**check the releases tab or the [changelog](http://autoprotocol-python.readthedocs.io/en/latest/changelog.html) in this repository to see the latest release that will be downloaded.  To be completely up to date it's safest to clone and install this repository as above**

## Building a Protocol
A basic protocol object has empty "refs" and "instructions" stanzas.  Various helper methods in the Protocol class are used to append Instructions and Refs to the Protocol object such as in the simple protocol below:

```python
import json
from autoprotocol.protocol import Protocol

#instantiate new Protocol object
p = Protocol()

# append refs (containers) to Protocol object
bacteria = p.ref("bacteria", cont_type="96-pcr", storage="cold_4")
media = p.ref("media", cont_type="micro-1.5", storage="cold_4")
reaction_plate = p.ref("reaction_plate", cont_type="96-flat", storage="warm_37")

# distribute media from 1.5mL tube to reaction wells
p.distribute(media.well(0).set_volume("1000:microliter"),
             reaction_plate.wells_from(0,4), ["140:microliter",
             "130:microliter", "120:microliter", "100:microliter"])

# transfer bacteria from source wells to reaction wells
p.transfer(bacteria.wells_from(0,4), reaction_plate.wells_from(0,4),
           ["10:microliter", "20:microliter", "30:microliter", "40:microliter"])

# cover plate
p.cover(reaction_plate)

# incubate bacteria at 37 degrees for 5 hours
p.incubate(reaction_plate, "warm_37", "5:hour", shaking=True)

# read absorbance of the first four wells on the reaction plate at 600 nanometers
p.absorbance(reaction_plate, reaction_plate.wells_from(0,4).indices(), "600:nanometer",
             "OD600_reading_01092014")

print json.dumps(p.as_dict(), indent=2)
```
The script above prints the following output to standard out by calling as_dict() on the Protocol object:

```
{
  "refs": {
    "media": {
      "new": "micro-1.5",
      "store": {
        "where": "cold_4"
      }
    },
    "bacteria": {
      "new": "96-pcr",
      "store": {
        "where": "cold_4"
      }
    },
    "reaction_plate": {
      "new": "96-flat",
      "store": {
        "where": "warm_37"
      }
    }
  },
  "instructions": [
    {
      "groups": [
        {
          "distribute": {
            "to": [
              {
                "volume": "140.0:microliter",
                "well": "reaction_plate/0"
              },
              {
                "volume": "130.0:microliter",
                "well": "reaction_plate/1"
              },
              {
                "volume": "120.0:microliter",
                "well": "reaction_plate/2"
              },
              {
                "volume": "100.0:microliter",
                "well": "reaction_plate/3"
              }
            ],
            "from": "media/0",
            "allow_carryover": false
          }
        },
        {
          "transfer": [
            {
              "volume": "10.0:microliter",
              "to": "reaction_plate/0",
              "from": "bacteria/0"
            }
          ]
        },
        {
          "transfer": [
            {
              "volume": "20.0:microliter",
              "to": "reaction_plate/1",
              "from": "bacteria/1"
            }
          ]
        },
        {
          "transfer": [
            {
              "volume": "30.0:microliter",
              "to": "reaction_plate/2",
              "from": "bacteria/2"
            }
          ]
        },
        {
          "transfer": [
            {
              "volume": "40.0:microliter",
              "to": "reaction_plate/3",
              "from": "bacteria/3"
            }
          ]
        }
      ],
      "op": "pipette"
    },
    {
      "lid": "standard",
      "object": "reaction_plate",
      "op": "cover"
    },
    {
      "where": "warm_37",
      "object": "reaction_plate",
      "co2_percent": 0,
      "duration": "5:hour",
      "shaking": true,
      "op": "incubate"
    },
    {
      "dataref": "OD600_reading_01092014",
      "object": "reaction_plate",
      "wells": [
        "A1",
        "A2",
        "A3",
        "A4"
      ],
      "num_flashes": 25,
      "wavelength": "600:nanometer",
      "op": "absorbance"
    }
  ]
}
```
## Extras

A folder of SublimeText snippets for this library is included in this repo.  To use them, copy the folder to `~/Library/Application\ Support/Sublime\ Text\ 3/Packages/User`
(replace with the version of Sublime Text you're using if it's not 3).

## Disclaimers

The Autoprotocol Python Library contains official support for units listed in the [Autoprotocol](http://www.autoprotocol.org) specification. Other units and abbreviations of units have been provided as a convenience.

## Contributing

The easiest way to contribute is to fork this repository and submit a pull
request.  You can also submit an issue or write an email to us at
support@transcriptic.com if you want to discuss ideas or bugs.

autoprotocol-python is BSD licensed (see [LICENSE](http://autoprotocol-python.readthedocs.io/en/latest/LICENSE.html)).
Before we can accept your pull request, we require that you sign a CLA (Contributor License Agreement)
allowing us to distribute your work under the BSD license. Email one of the [AUTHORS](http://autoprotocol-python.readthedocs.io/en/latest/AUTHORS.html) for more details.
