# Autoprotocol Python

[Autoprotocol](https://www.autoprotocol.org) is a standard way to express
experiments in life science. This repository contains a python library for
generating Autoprotocol.

## Installation

    $ git clone https://github.com/autoprotocol/autoprotocol-python
    $ cd autoprotocol-python
    $ python setup.py install
    
or, alternatively:

    $ pip install autoprotocol

## Simple Protocol Example
A basic protocol object has empty "refs" and "instructions" stanzas.  Various helper methdods in Protocol are then used to append instructions and refs to the object such as in the simple protocol below: 

```python
from autoprotocol.protocol import Protocol

p = Protocol()
bacteria = p.ref("bacteria", cont_type="96-pcr", storage="cold_4")
medium = p.ref("medium", cont_type="micro-1.5", storage="cold_4")
reaction_plate = p.ref("reaction_plate", cont_type="96-flat", storage="warm_37")
p.incubate(bacteria, "warm_37", "1:hour")
p.distribute(medium.well(0), reaction_plate.wells_from(0,4), "200:microliter")
p.transfer(bacteria.wells_from(0,4), reaction_plate.wells_from(0,4), "2:microliter")

```
calling `p.as_dict()` on the protocol above (or to pretty print, `json.dumps(p.as_dict, indent=2)`) produces the following autoprotocol:

```
{
  "refs": {
    "medium": {
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
      "duration": "1:hour", 
      "where": "warm_37", 
      "object": "bacteria", 
      "shaking": false, 
      "op": "incubate"
    }, 
    {
      "groups": [
        {
          "distribute": {
            "to": [
              {
                "volume": "200:microliter", 
                "well": "reaction_plate/0"
              }, 
              {
                "volume": "200:microliter", 
                "well": "reaction_plate/1"
              }, 
              {
                "volume": "200:microliter", 
                "well": "reaction_plate/2"
              }, 
              {
                "volume": "200:microliter", 
                "well": "reaction_plate/3"
              }
            ], 
            "from": "medium/0", 
            "allow_carryover": false
          }
        }, 
        {
          "transfer": [
            {
              "volume": "2.0:microliter", 
              "to": "reaction_plate/0", 
              "from": "bacteria/0"
            }
          ]
        }, 
        {
          "transfer": [
            {
              "volume": "2.0:microliter", 
              "to": "reaction_plate/1", 
              "from": "bacteria/1"
            }
          ]
        }, 
        {
          "transfer": [
            {
              "volume": "2.0:microliter", 
              "to": "reaction_plate/2", 
              "from": "bacteria/2"
            }
          ]
        }, 
        {
          "transfer": [
            {
              "volume": "2.0:microliter", 
              "to": "reaction_plate/3", 
              "from": "bacteria/3"
            }
          ]
        }
      ], 
      "op": "pipette"
    }
  ]
}
```

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
