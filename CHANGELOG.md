# CHANGELOG

This project adheres to [Semantic Versioning](http://semver.org/)

## Unreleased
---
Added

Changed

Removed

Fixed


## v3.7.6 - 2016-07-25
---
Added

Changed
- documentation
- convert pipette operations to microliters

Removed

Fixed
- cover_types on 96-deep-kf and 96-deep
- dispense_speed and distribute_target in Distribute instruction

## v3.7.5 - 2016-07-08
---
Added
- plate type 6-flat-tc to ContainerType

Changed

Removed

Fixed


## v3.7.4 - 2016-07-07
---
Added

Changed

Removed

Fixed
- auto-uncover before provision instructions

## v3.7.3 - 2016-07-06
---
Added
- is_resource_id added to dispense and dispense_full_plate instructions
- dispense instruction tests
- autocover before incubate
- assertions and tests for flow_analyze
- WellGroup methods: set_group_name, pop, insert, wells_with
- documentation

Changed
- WellGroup.extend(wells) can now take in a list of wells
- dispense instruction json outputs
- removed capability 'cover' from 96-pcr and 384-pcr plates

Removed

Fixed
- spin auto-cover
- compatibility with py3 in flow_analyze


## v3.7.2 - 2016-06-24
---
Added
- validations before implicit cover or seal
- new plate types 384-clear-clear, 384-flat-white-white-lv, 384-flat-white-white-tc

Changed

Removed

Fixed

## v3.7.1 - 2016-06-17
---
Added
- validations of input types before cover check
- cover_types and seal_types to _CONTAINER_TYPES

Changed

Removed
- string input types for source, destination wells for Instructions Consolidate, Autopick, Mix

Fixed

## v3.7.0 - 2016-06-14
---
Added
- track plate cover status - Container objects now have a `cover` attribute, implicit plate unsealing or uncovering prior to steps that require the plate to be uncovered.

Changed

Removed

Fixed
- Stamp separates row stamps with more than 2 containers

## v3.6.0 - 2016-06-07
---
Added
- Time constraints

Changed
- illuminaseq allows cycle specification

Removed

Fixed

## v3.5.3 - 2016-05-16
---
Added

Changed
- harness.py returns proper boolean for thermocycle types

Removed

Fixed

## v3.5.2 - 2016-05-13
---
Added
- Unit specific error handling

Changed

Removed

Fixed
- thermocycle gradient steps in harness.py

## v3.5.1 - 2016-05-12
---
Added
- mix allows one_tip=True

Changed

Removed

Fixed
- acoustic_transfer handling of droplet size

## v3.5.0 - 2016-05-06
---
Added
- measure_mass instruction
- measure_volume instruction
- illumina_sequence instruction


Changed
- gel purify parameters have changed
- Spin instruction takes directional parameters

Removed

Fixed
 - WellGroup checks that all elements are wells
 - Concatenation of Well to WellGroup no longer returns None
 - gel string in documentation
 - fix harness to be python3 compatible
 - Compatibility of Unit for acceleration

## v3.4.0 - 2016-04-22
---
Added
 - discard() and and set_storage() methods for containers
 - gel_purify instruction to instruction.py and protocol.py
 - support for list input type for humanize and robotize (container and container_type)

Changed

Removed

Fixed

## v3.3.0 - 2016-04-13
---
Added
- csv-table input type to harness.py

Changed

Removed

Fixed

## v3.2.0 - 2016-04-07
---
Added
- additional parameter, gain, to fluorescence
- checking for valid plate read incubate parameters
- Unit(Unit(...)) now returns a Unit
- disclaimer to README.md on unit support
- Unit support for `molar`

Changed
- adding magnetic transfer functions to documentation
- magnetic transfer instructions to now pass relevant inputs through units

Removed

Fixed
- documentation for magnetic transfer instructions correctly uses hertz

## v3.1.0 - 2016-03-24
---
Added
- additional parameters to spectrophotometry instructions (absorbance, luminescence, fluorescence) to instruction.py and protocol.py
- helper function in util.py to create incubation dictionaries
- support for a new instruction for measure_concentration

Changed
- Updated handling of multiplication and division of Units of the same dimension to automatically resolve when possible

Removed

Fixed
- Updated maximum tip capacity for a transfer operation to 900uL instead of 750uL
- Updated Unit package to default to `Autoprotocol` format representation for temperature and speed units


## v3.0.0 - 2016-03-17
---
Added
- container+ input type to harness.py
- magnetic_transfer instruction to instruction.py and protocol.py
- kf container types in container_type.py

Changed
- release versioning has been removed in favor of protocol versioniong in harness.py
- update 6-flat well volumes
- Unit now uses Pint's Quantity as a base class

Removed

Fixed
- default versioning in manifest_test.json
- Update container_test.py and container_type_test.py to include safe_min_volume_ul

## v2.7.0 - 2016-02-18
---
Added
- safe_min_volume_ul in _CONTAINER_TYPES

Changed
- updated dead_volume_ul values in _CONTAINER_TYPES

Removed

Fixed
- Protocol.stamp() smartly calculates max_tip_volume using residual volumes

## v2.6.0 - 2015-02-02
---
Added
- Include well properties in outs
- `extend()` method to WellGroup

Changed
- Allow single Well reading for Absorbance, Fluorescence and Luminescence
- Autopick now conforms to updated ASC (**not backwards compatible**)

Removed
- Protocol.plate_to_magblock() and Protocol.plate_from_magblock()

Fixed
- Protocol.stamp() allows one_tip=True when steps use a `mix_vol` greater than "31:microliter" even if transferred volumes are not all greater than "31:microliter"
- Protocol.transfer() respects when `mix_after` or `mix_before` is explicitly False

## v2.5.0 - 2015-10-12
---
Changed
- Protocol.stamp() and Stamp() has been reformatted to take groups of transfers. This allows for one_tip=True, one_source=True, and WellGroup source and destinations

## v2.4.1 - 2015-10-12
---
Fixed
- volume tracking for stamping to/from 384-well plates
- one_tip = True transfers > 750:microliter are transferred with single tip

## v2.4.0 - 2015-09-28
---
Added
- UserError exception class for returning custom errors from within protocol scripts
- functionality to harness.py for naming aliquots

Changed
- Stamp transfers are not combinable if they use different tip volume types
- Transfers with one_source true does not keep track of the value of volume less than 10^-12

Removed

Fixed
- Small bug for transfer with one_source=true fixed
- Better handling of default append=true behavior for `Protocol.stamp()`
- more recursion in `make_dottable_dict`, a completely unnecessary function you shouldn't use

## v2.3.0 - 2015-08-31
---
Added

Changed
- Protocol.stamp() and Stamp() now support selective (row-wise and column-wise) stamping (see docstring for details)

Removed

Fixed

## v2.2.2 - 2015-08-28
Added
- Storage attribute on Container
- Protocol.store() - manually change storage condition destiny of a Container
- Test for more complicated `transfer`ing with `one_source=True`
- Better error handling in harness.py and accompanying tests

Changed
- Arguments to `Protocol.transfer` for `mix_before` and `mix_after` are now part of **mix_kwargs to allow for specifying separate parameters for mix_before and mix_after

Removed

Fixed
- Error with `transfer`ing with `one_source=True`

## v2.2.1 - 2015-08-20
---
Added
- volume tracking to Protocol.stamp() and associated helper functions in autoprotocol.util

Changed

Removed

Fixed
- semantic versioning fail

## v2.1.1 - 2015-08-06
---
**version number typo**
Added
- name property on Well
- "outs" section of protocol.  Use Well.set_name() to name an aliquot
- unit conversion from milliliters or nanoliters to microliters in `Well.set_volume()`, `Protocol.provision()`, `Protocol.transfer()`, and `Protocol.distribute`

Changed

Removed

Fixed
- Error with `provision`ing to multiple wells of the same container
- Error when `transfer`ing over 750uL
- Unit scalar multiplication

## v2.2.0 - 2015-07-21
---
Added
- `Stamp` class in autoprotocol.instruction
- volume tracking to destination wells when using Protocol.dispense()
- __repr__ override for Unit class

Changed
- Protocol.stamp() now utilizes the new Autoprotocol `stamp` instruction instead of transfer()

Removed

Fixed
- fixed indentation
- refactored Protocol methods: ref, consolidate, transfer, distribute
- better error handling for transfer() and distribute()

## v2.1.0 - 2015-06-10
---
Added
- `flash_freeze()` Protocol method and Instruction
- `criteria` and `dataref` fields to `Autopick()`
- `SangerSeq` now accepts a sequencing `type` of `"rca"` or `"standard"` (defaults to "standard")

Changed
- collapse Protocol.provision() instructions if they're acting on the same container

Removed
- Protocol.thermocycle_ramp()
- Protocol.serial_dilute_rowwise()

Fixed
- type check in Container.wells
- Protocol.ref() behavior when specifying the `id` of an existing container


## v2.0.5 - 2015-06-04
---

Added
- Added folder for sublime text snippets
- volume adjustment when `spread()`ing
- `ImagePlate()` class and `image_plate()` Protocol method for taking images of containers
- add `consolidate()` Protocol method and accompanying tests
- support for container names with slashes in them in `harness.py`
- `1-flat` plate type to `_CONTAINER_TYPES`
- brought back recursively transferring volumes over 900 microliters
- allow transfer from multiple sources to one destination
- support for `choice` input type in `harness.py`
- `provision()` Protocol method
- Additional type-checks in various functions
- More Python3 Compatibility

Removed
- check that a well already exists in a WellGroup

Fixed
- typo in sanger_sequence instruction
- documentation punctuation and grammar

## v2.0.4 - 2015-05-05
---
Added
- More Python3 Compatibility
- specify `Wells` on a container using `container.wells(1,2,3)`or `container.wells([1,2,3])`
- Thermocycle input type in `harness.py`
- `new_group` keyword parameter on `transfer()` and `distribute()` to manually break up `Pipette()` Instructions
- documentation for `plate_to_mag_adapter` and `plate_from_mag_adapter` **subject to change in near future**
- tox for testing with multiple versions of python

Changed
- `gel_separate` generates instructions taking wells and matrix type passed
- `stamp`ing to or from multiple containers now requires that the source or dest variable be passed as a list of `[{"container": <container>, "quadrant": <quadrant>}, ...]`

Removed
- references to specific reagents for `dispense()`

Fixed
- Transfering liquid from `one_source` actually works now

## v2.0.3 - 2015-04-17
---
Added
- At least some Python3 compatibility
- Container.properties is an empty hash by default
- `Container.add_properties()`
- `Container.quadrant()` returns a WellGroup of the 96 wells representing the quadrant passed
- `96-flat-uv` container type in `_CONTAINER_TYPES`
- `6-flat` container type in `_CONTAINER_TYPES`
- co2 parameter in incubate
- `Flow_Analyze` Instruction
- `Spread` Instruction
- `Autopick` Instruction
- `Oligosynthesize` Instruction
- Additional keyword arguments for `transfer()` and `distribute()` to customize pipetting
- Added `pipette_tools` module containing helper methods for the extra pipetting parameters
- `stamp()` Protocol method for using the 96-channel liquid handler
- more tests

Changed
- seal takes a "type" parameter that defaults to ultra-clear
- SangerSeq Instruction and method
- `Protocol.pipette()` is now a private method `_pipette()`
- refactoring of type checks in `Unit`
- improved documentation tree on

Removed
- references to specific matrices and ladders in `gel_separate`
- recursion to deal with transferring over 900uL of liquid

Fixed
- `gel_separate()` generates number of instructions needed for number of wells passed


## v2.0.2 - 2015-03-06
---
Added
- autoprotocol and JSON output examples for almost everything in docs
- link to library documentation at readthedocs.org to README
- default input value and group and group+ input types in `harness.py`
- melting keyword variables and changes to conditionals in Thermocycle
- a wild test appeared!

## v2.0.1 - 2015-02-06
---
Added
- properties attribute to `Well`, along with `set_properties()` method
- aliquot++, integer, boolean input types to harness.py
- `Dispense()` Instruction and accompanying Protocol method for using a reagent dispenser
- `Protocol.dispense_full_plate()`
- warnings for `_mul_` and `_div_` scalar Unit operations
- README.rst

Changed
- "speed" parameter in `Spin()` to "acceleration"

Removed
- `well_type` from `_CONTAINER_TYPES`

Fixed
- spelling of luminescence :(

## v2.0.0 - 2014-01-24
---
Added
- harness.py for parameter conversion
- NumPy style docstrings for most methods
- `Container.inner_wells()` method to exclude edges
- 3-clause BSD license, contributor info
- `WellGroup.indices()` returns a list of string well indices
- dead_volume_ul in _CONTAINER_TYPES
- volume tracking upon `transfer()` and `distribute()`
- "one_tip" option on `transfer()`

Removed
- static methods `Pipette.transfers()` and `Pipette._transferGroup()`

## v1.0.0 - 2014-01-22
---
- generally outdated version that no one should look at anymore