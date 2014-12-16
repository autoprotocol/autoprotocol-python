# Transcriptic Python Client Library

This is a set of helper functions and classes to simplify generating Autoprotocol

## Installation

    git clone https://github.com/autoprotocol/autoprotocol-python
    python setup.py build
    python setup.py install

## Writing Protocols

There are a two ways to write protocols using this library.  In the first way, you can build them as a list of instructions directly and then pass them to the constructor of a `Protocol`:

```python
from transcriptic.protocol import Ref, Pipette, Incubate, Protocol

refs = [
  Ref("bacteria", {"new": "96-pcr", "store": {"where": "cold_4"}}, Container(None, "96-pcr"))
]
instructions = [
  Incubate("bacteria", "warm_37", "30:minute"),
  Pipette([{
    "transfer": {
      "from": "bacteria/A1",
      "to": "bacteria/A2",
      "volume": "15:microliter"
    }
  }])
]
p = Protocol(refs, instructions)
```

The second way is to create a new `Protocol` and then use its helper methods:

```python
from transcriptic.protocol import Protocol

p = Protocol()
bacteria = ref("bacteria", id=None, cont_type="96-pcr", storage="cold_4")
p.incubate(bacteria, "warm_37", "30:minute")
p.transfer(bacteria.well("A1"), bacteria.well("A2"), "15:microliter")
```

Both are equivalent.  The first style is a bit more functional since it allows you to pass around instructions and write functions that return blocks of instructions, whereas the protocol helper methods are all side-effects.


## Running and Submitting Protocols
Each protocol has an accompanying .json config file with the following format:
```
  {
      "refs":{
          "container1_name": {
              "id": null,
              "type": "",
              "storage": "",
              "discard": false
          },
          "container2_name": {
              "id": null,
              "type": "",
              "storage": "",
              "discard": false
          },
          { ... }
      },
      "parameters":{
        "parameter1": "value:1",
        ...

      }
  }
```
protocols are then called from the command-line as follows with the config file following the script module call:

```$ python -m autoprotocol.protocols.example_script example_script_config.json
```
calling the above from the command line will simply output the protocol object as JSON

To submit a protocol to Transcriptic.com to be automated or analyzed, download the transcriptic command-line tool at https://github.com/transcriptic/runner.

You can then pipe protocol modules to transcriptic by doing the following, for example:
```$ python -m autoprotocol.protocols.example_script example_script_config.json | transcriptic analyze
```

## Contributing

The easiest way to contribute is to fork this repository and submit a pull request.  You can also write an email to us if you want to discuss ideas or bugs.

- Max Hodak: max@transcriptic.com
- Jeremy Apthorp: jeremy@transcriptic.com
- Tali Herzka: tali@transcriptic.com
- Sai Kalidindi: sai@transcriptic.com

All code in this project is MIT licensed and you'll have to agree to forfeit copyright for us to merge your pull request.