# CHANGELOG

This project adheres to [Semantic Versioning](http://semver.org/)

## Unreleased

### Fixed
- typo in sanger_sequence instruction

### Added
- volume adjustment when `spread()`ing
- `ImagePlate()` class and `image_plate()` Protocol method for taking images of containers


## v2.0.4 - 2015-05-05

### Added
- More Python3 Compatibility
- specify `Wells` on a container using `container.wells(1,2,3)`or `container.wells([1,2,3])`
- Thermocycle input type in `harness.py`
- `new_group` keyword parameter on `transfer()` and `distribute()` to manually break up `Pipette()` Instructions
- documentation for `plate_to_mag_adapter` and `plate_from_mag_adapter` **subject to change in near future**
- tox for testing with multiple versions of python

### Changed
- `gel_separate` generates instructions taking wells and matrix type passed
- `stamp`ing to or from multiple containers now requires that the source or dest variable be passed as a list of `[{"container": <container>, "quadrant": <quadrant>}, ...]`

### Removed
- references to specific reagents for `dispense()`

### Fixed
- Transfering liquid from `one_source` actually works now

## v2.0.3 - 2015-04-17


### Added
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

### Changed
- seal takes a "type" parameter that defaults to ultra-clear
- SangerSeq Instruction and method
- `Protocol.pipette()` is now a private method `_pipette()`
- refactoring of type checks in `Unit`
- improved documentation tree on

### Removed
- references to specific matrices and ladders in `gel_separate`
- recursion to deal with transferring over 900uL of liquid

### Fixed
- `gel_separate()` generates number of instructions needed for number of wells passed


## v2.0.2 - 2015-03-06

### Added
- autoprotocol and JSON output examples for almost everything in docs
- link to library documentation at readthedocs.org to README
- default input value and group and group+ input types in `harness.py`
- melting keyword variables and changes to conditionals in Thermocycle
- a wild test appeared!

## v2.0.1 - 2015-02-06

### Added
- properties attribute to `Well`, along with `set_properties()` method
- aliquot++, integer, boolean input types to harness.py
- `Dispense()` Instruction and accompanying Protocol method for using a reagent dispenser
- `Protocol.dispense_full_plate()`
- warnings for `_mul_` and `_div_` scalar Unit operations
- README.rst

### Changed
- "speed" parameter in `Spin()` to "acceleration"

### Removed
- `well_type` from `_CONTAINER_TYPES`

### Fixed
- spelling of luminescence :(

## v2.0.0 - 2014-01-24

### Added
- harness.py for parameter conversion
- NumPy style docstrings for most methods
- `Container.inner_wells()` method to exclude edges
- 3-clause BSD license, contributor info
- `WellGroup.indices()` returns a list of string well indices
- dead_volume_ul in _CONTAINER_TYPES
- volume tracking upon `transfer()` and `distribute()`
- "one_tip" option on `transfer()`

### Removed
- static methods `Pipette.transfers()` and `Pipette._transferGroup()`

## v1.0.0 - 2014-01-22

- generatlly outdated version that no one should look at anymore
















