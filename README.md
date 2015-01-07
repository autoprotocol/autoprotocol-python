# Autoprotocol Python

[Autoprotocol](https://www.autoprotocol.org) is a standard way to express
experiments in life science. This repository contains a python library for
generating Autoprotocol.

## Installation

    $ git clone https://github.com/autoprotocol/autoprotocol-python
    $ cd autoprotocol-python
    $ python setup.py install

## Simple Protocol Example
```python
from autoprotocol-core import Protocol

p = Protocol()
bacteria = p.ref("bacteria", cont_type="96-pcr", storage="cold_4")
medium = p.ref("medium", cont_type="micro-1.5", storage="cold_4")
reaction_plate = p.ref("reaction_plate", cont_type="96-flat", storage="warm_37")
p.incubate(bacteria, "warm_37", "1:hour")
p.distribute(medium.well(0), reaction_plate.wells_from(0,12), "200:microliter")
p.transfer(bacteria.wells_from(0,12), reaction_plate.wells_from(0,12), "2:microliter")
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
