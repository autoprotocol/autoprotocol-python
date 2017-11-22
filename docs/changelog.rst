=========
Changelog
=========

* :release:`4.0.0 <2017-10-06>`
* :feature:`-` allow breathable seals on 96-deep and 24-deep
* :feature:`-` add prioritize_seal_or_cover allow priority selection
* :support:`-` docstring cleanup, linting
* :bug:`-` remove cover prior to mag steps where applicable
* :support:`-` convert test suite to py.test
* :feature:`-` add new containers, true_max_vol_ul in _CONTAINER_TYPES

* :release:`3.10.1 <2017-05-25>`
* :bug:`-` update pint requirements, update error handling on UnitError
* :support:`- backported` fix documentation typos
* :bug:`-` update default lid types for :ref:`container-type-384-echo`, :ref:`container-type-96-flat`, :ref:`container-type-96-flat-uv`, and :ref:`container-type-96-flat-clear-clear-tc`

* :release:`3.10.0 <2016-10-25>`
* :support:`-` add functions and tests to enable use of `--dye_test` flag
* :support:`-` more descriptive error message in :ref:`protocol-ref`
* :bug:`- major` fix name of :ref:`container-type-384-round-clear-clear`
* :feature:`-` new plate types :ref:`container-type-384-v-clear-clear`, :ref:`container-type-384-round-clear-clear`, :ref:`container-type-384-flat-white-white-nbs`
* :bug:`- major` fix :ref:`well-set-properties` so that it completely overwrites the existing properties dict
* :bug:`- major` respect incubate conditions where uncovered=True
* :bug:`- major` prevent invalid incubate parameters in :ref:`protocol-absorbance`
* :bug:`- major` allow incubation of containers at ambient without covers

* :release:`3.9.0 <2016-08-10>`
* :feature:`-` new plate type :ref:`container-type-96-flat-clear-clear-tc`
* :feature:`-` Container method: :ref:`container-tube`
* :support:`-` update documention for :ref:`harness-seal-on-store`
* :bug:`- major` Unit validations from str in :ref:`protocol-flow-analyze` instruction

* :release:`3.8.0 <2016-07-26>`
* :bug:`- major` unit conversion to microliters in :ref:`protocol-dispense` instruction
* :support:`-` using release for changelog and integration into readthedocs documentation

* :release:`3.7.6 <2016-07-25>`
* :bug:`-` dispense_speed and distribute_target in :ref:`protocol-distribute` instruction
* :bug:`127` convert pipette operations to microliters
* :bug:`128` cover_types on :ref:`container-type-96-deep-kf` and :ref:`container-type-96-deep`
* :bug:`-` convert pipette operations to microliters

* :release:`3.7.5 <2016-07-08>`
* :feature:`- backported` plate type :ref:`container-type-6-flat-tc` to ContainerType

* :release:`3.7.4 <2016-07-07>`
* :bug:`-` auto-uncover before :ref:`protocol-provision` instructions

* :release:`3.7.3 <2016-07-06>`
* :feature:`- backported` `is_resource_id` added to :ref:`protocol-dispense` and :ref:`protocol-dispense-full-plate` instructions
* :support:`-` :ref:`protocol-dispense` instruction tests
* :feature:`- backported` autocover before :ref:`protocol-incubate`
* :feature:`- backported` assertions and tests for :ref:`protocol-flow-analyze`
* :feature:`- backported` WellGroup methods: :ref:`wellgroup-group-name`, :ref:`wellgroup-pop`, :ref:`wellgroup-insert`, :ref:`wellgroup-wells-with`
* :support:`- backported` documentation
* :feature:`- backported` :ref:`wellgroup-extend` can now take in a list of wells
* :bug:`-` :ref:`protocol-dispense` instruction json outputs
* :bug:`-` removed capability 'cover' from :ref:`container-type-96-pcr` and :ref:`container-type-384-pcr` plates
* :bug:`-` :ref:`protocol-spin` auto-cover
* :bug:`-` compatibility with py3 in :ref:`protocol-flow-analyze`

* :release:`3.7.2 <2016-06-24>`
* :feature:`- backported` validations before implicit cover or seal
* :feature:`- backported` new plate types :ref:`container-type-384-flat-clear-clear`, :ref:`container-type-384-flat-white-white-lv`, :ref:`container-type-384-flat-white-white-tc`

* :release:`3.7.1 <2016-06-17>`
* :feature:`- backported` validations of input types before cover check
* :feature:`- backported` cover_types and seal_types to _CONTAINER_TYPES
* :bug:`-` string input types for source, destination wells for Instructions :ref:`protocol-consolidate`, :ref:`protocol-autopick`, :ref:`protocol-mix`

* :release:`3.7.0 <2016-06-14>`
* :feature:`-` track plate cover status - Container objects now have a `cover` attribute, implicit plate unsealing or uncovering prior to steps that require the plate to be uncovered.
* :bug:`- major` :ref:`protocol-stamp` separates row stamps with more than 2 containers

* :release:`3.6.0 <2016-06-07>`
* :feature:`-` :ref:`protocol-add-time-constraint` added
* :feature:`-` :ref:`protocol-illuminaseq` allows cycle specification

* :release:`3.5.3 <2016-05-16>`
* :bug:`-` harness.py returns proper boolean for thermocycle types

* :release:`3.5.2 <2016-05-13>`
* :feature:`- backported` :ref:`unit-unit` specific error handling
* :bug:`-` thermocycle gradient steps in harness.py

* :release:`3.5.1 <2016-05-12>`
* :feature:`- backported` :ref:`protocol-mix` allows one_tip=True
* :bug:`-` :ref:`protocol-acoustic-transfer` handling of droplet size

* :release:`3.5.0 <2016-05-06>`
* :feature:`-` :ref:`protocol-measure-mass` instruction
* :feature:`-` :ref:`protocol-measure-volume` instruction
* :feature:`-` :ref:`protocol-illuminaseq` instruction
* :feature:`-` :ref:`protocol-gel-purify` parameters improved
* :feature:`-` :ref:`protocol-spin` instruction takes directional parameters
* :bug:`- major` WellGroup checks that all elements are wells
* :bug:`- major` Concatenation of Well to WellGroup no longer returns None
* :support:`-` gel string in documentation
* :bug:`- major` fix harness to be python3 compatible
* :bug:`- major` Compatibility of Unit for acceleration

* :release:`3.4.0 <2016-04-22>`
* :feature:`-` :ref:container-discard` and and :ref:`container-set-storage` methods for containers
* :feature:`-` :ref:`protocol-gel-purify` instruction to instruction.py and protocol.py
* :feature:`-` support for list input type for humanize and robotize (container and container_type)

* :release:`3.3.0 <2016-04-13>`
* :feature:`-` csv-table input type to harness.py

* :release:`3.2.0 <2016-04-07>`
* :feature:`-` additional parameter, `gain`, to :ref:`protocol-fluorescence`
* :feature:`-` checking for valid plate read incubate parameters
* :feature:`-` Unit(Unit(...)) now returns a Unit
* :feature:`-` disclaimer to README.md on unit support
* :feature:`-` Unit support for `molar`
* :support:`-` adding magnetic transfer functions to documentation
* :feature:`-` magnetic transfer instructions to now pass relevant inputs through units
* :support:`-` documentation for magnetic transfer instructions correctly uses hertz

* :release:`3.1.0 <2016-03-24>`
* :feature:`-` additional parameters to spectrophotometry instructions (:ref:`protocol-absorbance`, :ref:`protocol-luminescence`, :ref:`protocol-fluorescence`) to instruction.py and protocol.py
* :feature:`-` helper function in util.py to create incubation dictionaries
* :feature:`-` support for a new instruction for :ref:`protocol-measure-concentration`
* :bug:`- major` Updated handling of multiplication and division of Units of the same dimension to automatically resolve when possible
* :bug:`- major` Updated maximum tip capacity for a transfer operation to 900uL instead of 750uL
* :bug:`- major` Updated Unit package to default to `Autoprotocol` format representation for temperature and speed units

* :release:`3.0.0 <2016-03-17>`
* :feature:`-` `container+` input type to harness.py
* :feature:`-` `magnetic_transfer` instruction to instruction.py and protocol.py
* :feature:`-` kf container types :ref:`container-type-96-v-kf` and :ref:`container-type-96-deep-kf` in container_type.py
* :feature:`-` release versioning has been removed in favor of protocol versioniong in harness.py
* :feature:`-` update :ref:`container-type-6-flat` well volumes
* :feature:`-` :ref:`unit-unit` now uses Pint's Quantity as a base class
* :bug:`- major` default versioning in manifest_test.json
* :bug:`- major` Update container_test.py and container_type_test.py to include safe_min_volume_ul

* :release:`2.7.0 <2016-02-18>`
* :feature:`-` safe_min_volume_ul in _CONTAINER_TYPES
* :feature:`-` updated dead_volume_ul values in _CONTAINER_TYPES
* :bug:`- major` :ref:`protocol-stamp` smartly calculates max_tip_volume using residual volumes

* :release:`2.6.0 <2015-02-02>`
* :feature:`-` Include well properties in outs
* :feature:`-` :ref:`wellgroup-extend` method to WellGroup
* :feature:`-` Allow single Well reading for Absorbance, Fluorescence and Luminescence
* :feature:`-` :ref:`protocol-autopick` now conforms to updated ASC (**not backwards compatible**)
* :support:`-` Protocol.plate_to_magblock() and Protocol.plate_from_magblock()
* :bug:`- major` Protocol.stamp() allows one_tip=True when steps use a `mix_vol` greater than "31:microliter" even if transferred volumes are not all greater than "31:microliter"
* :bug:`- major` :ref:`protocol-transfer` respects when `mix_after` or `mix_before` is explicitly False

* :release:`2.5.0 <2015-10-12>`
* :feature:`-` :ref:`protocol-stamp` has been reformatted to take groups of transfers. This allows for one_tip=True, one_source=True, and WellGroup source and destinations

* :release:`2.4.1 <2015-10-12>`
* :bug:`-` volume tracking for :ref:`protocol-stamp` ing to/from 384-well plates
* :bug:`-` one_tip = True transfers > 750:microliter are transferred with single tip

* :release:`2.4.0 <2015-09-28>`
* :feature:`-` UserError exception class for returning custom errors from within protocol scripts
* :feature:`-` functionality to harness.py for naming aliquots
* :support:`-` :ref:`protocol-stamp` transfers are not combinable if they use different tip volume types
* :support:`-` Transfers with one_source true does not keep track of the value of volume less than 10^-12
* :bug:`- major` Small bug for transfer with one_source=true fixed
* :bug:`- major` Better handling of default append=true behavior for :ref:`protocol-stamp`
* :bug:`- major` more recursion in `make_dottable_dict`, a completely unnecessary function you shouldn't use

* :release:`2.3.0 <2015-08-31>`
* :feature:`-` :ref:`protocol-stamp` now support selective (row-wise and column-wise) stamping (see docstring for details)

* :release:`2.2.2 <2015-08-28>`
* :feature:`- backported` Storage attribute on Container
* :feature:`- backported` Protocol.store() 
* :feature:`- backported` manually change storage condition destiny of a Container
* :feature:`- backported` Test for more complicated `transfer`ing with `one_source=True`
* :feature:`- backported` Better error handling in harness.py and accompanying tests
* :feature:`- backported` Arguments to :ref:`protocol-transfer` for `mix_before` and `mix_after` are now part of **mix_kwargs** to allow for specifying separate parameters for mix_before and mix_after
* :bug:`-` Error with `transfer`ing with `one_source=True`

* :release:`2.2.1 <2015-08-20>`
* :feature:`- backported` volume tracking to :ref:`protocol-stamp` and associated helper functions in autoprotocol.util
* :support:`- backported` semantic versioning fail
* :feature:`- backported` name property on Well
* :feature:`- backported` "outs" section of protocol.  Use :ref:`well-set-name` to name an aliquot
* :feature:`- backported` unit conversion from milliliters or nanoliters to microliters in `Well.set_volume()`, :ref:`protocol-provision`, :ref:`protocol-transfer`, and :ref:`protocol-distribute`
* :bug:`-` Error with :ref:`protocol-provision` ing to multiple wells of the same container
* :bug:`-` Error when :ref:`protocol-transfer` ing over 750uL
* :bug:`-` Unit scalar multiplication

* :release:`2.2.0 <2015-07-21>`
* :feature:`-` `Stamp` class in autoprotocol.instruction
* :feature:`-` volume tracking to destination wells when using Protocol.dispense()
* :feature:`-` `__repr__` override for Unit class
* :feature:`-` :ref:`protocol-stamp` now utilizes the new Autoprotocol `stamp` instruction instead of :ref:`protocol-transfer`
* :bug:`- major` fixed indentation
* :bug:`- major` refactored Protocol methods: :ref:`protocol-ref`, :ref:`protocol-consolidate`, :ref:`protocol-transfer`, :ref:`protocol-distribute`
* :bug:`- major` better error handling for :ref:`protocol-transfer` and :ref:`protocol-distribute`

* :release:`2.1.0 <2015-06-10>`
* :feature:`-` :ref:`protocol-flash-freeze` Protocol method and Instruction
* :feature:`-` `criteria` and `dataref` fields to :ref:`protocol-autopick`
* :feature:`-` :ref:`protocol-sangerseq` now accepts a sequencing `type` of `"rca"` or `"standard"` (defaults to "standard")
* :feature:`-` collapse :ref:`protocol-provision` instructions if they're acting on the same container
* :support:`-` Protocol.thermocycle_ramp()
* :support:`-` Protocol.serial_dilute_rowwise()
* :bug:`- major` type check in Container.wells
* :bug:`- major` :ref:`protocol-ref` behavior when specifying the `id` of an existing container

* :release:`2.0.5 <2015-06-04>`
* :support:`- backported` Added folder for sublime text snippets
* :feature:`- backported` volume adjustment when :ref:`protocol-spread` ing
* :feature:`- backported` `ImagePlate()` class and :ref:`protocol-image-plate` Protocol method for taking images of containers
* :feature:`- backported` add :ref:`protocol-consolidate` Protocol method and accompanying tests
* :feature:`- backported` support for container names with slashes in them in `harness.py`
* :feature:`- backported` :ref:`container-type-1-flat` plate type to `_CONTAINER_TYPES`
* :feature:`- backported` brought back recursively transferring volumes over 900 microliters
* :feature:`- backported` allow transfer from multiple sources to one destination
* :feature:`- backported` support for `choice` input type in `harness.py`
* :feature:`- backported` :ref:`protocol-provision` Protocol method
* :feature:`- backported` Additional type-checks in various functions
* :feature:`- backported` More Python3 Compatibility
* :support:`- backported` check that a well already exists in a WellGroup
* :bug:`-` typo in :ref:`protocol-sangerseq` instruction
* :support:`- backported` documentation punctuation and grammar

* :release:`2.0.4 <2015-05-05>`
* :feature:`- backported` More Python3 Compatibility
* :feature:`- backported` specify `Wells` on a container using `container.wells(1,2,3)`or `container.wells([1,2,3])`
* :feature:`- backported` Thermocycle input type in `harness.py`
* :feature:`- backported` `new_group` keyword parameter on :ref:`protocol-transfer` and :ref:`protocol-distribute` to manually break up `Pipette()` Instructions
* :support:`- backported` documentation for `plate_to_mag_adapter` and `plate_from_mag_adapter` **subject to change in near future**
* :feature:`- backported` tox for testing with multiple versions of python
* :feature:`- backported` :ref:`protocol-gel-separate` generates instructions taking wells and matrix type passed
* :feature:`- backported` :ref:`protocol-stamp` ing to or from multiple containers now requires that the source or dest variable be passed as a list of `[{"container": <container>, "quadrant": <quadrant>}, ...]`
* :bug:`-` references to specific reagents for :ref:`protocol-dispense`
* :bug:`-` Transfering liquid from `one_source` actually works now

* :release:`2.0.3 <2015-04-17>`
* :feature:`- backported` At least some Python3 compatibility
* :feature:`- backported` Well.properties is an empty hash by default
* :feature:`- backported` :ref:`well-add-properties`
* :feature:`- backported` :ref:`container-quadrant` returns a WellGroup of the 96 wells representing the quadrant passed
* :feature:`- backported` `96-flat-uv` container type in `_CONTAINER_TYPES`
* :feature:`- backported` `6-flat` container type in `_CONTAINER_TYPES`
* :feature:`- backported` co2 parameter in :ref:`protocol-incubate`
* :feature:`- backported` :ref:`protocol-flow-analyze` Instruction
* :feature:`- backported` :ref:`protocol-spread` Instruction
* :feature:`- backported` :ref:`protocol-autopick` Instruction
* :feature:`- backported` :ref:`protocol-oligosynthesize` Instruction
* :feature:`- backported` Additional keyword arguments for :ref:`protocol-transfer` and :ref:`protocol-distribute` to customize pipetting
* :feature:`- backported` Added `pipette_tools` module containing helper methods for the extra pipetting parameters
* :feature:`- backported` :ref:`protocol-stamp` Protocol method for using the 96-channel liquid handler
* :feature:`- backported` more tests
* :feature:`- backported` seal takes a "type" parameter that defaults to ultra-clear
* :feature:`- backported` :ref:`protocol-sangerseq` Instruction and method
* :feature:`- backported` `Protocol.pipette()` is now a private method `_pipette()`
* :bug:`-` refactoring of type checks in :ref:`unit-unit`
* :support:`- backported` improved documentation tree
* :bug:`-` references to specific matrices and ladders in :ref:`protocol-gel-separate`
* :bug:`-` recursion to deal with transferring over 900uL of liquid
* :bug:`-` :ref:`protocol-gel-separate` generates number of instructions needed for number of wells passed

* :release:`2.0.2 <2015-03-06>`
* :support:`- backported` autoprotocol and JSON output examples for almost everything in docs
* :support:`- backported` link to library documentation at readthedocs.org to README
* :feature:`- backported` default input value and group and group+ input types in `harness.py`
* :feature:`- backported` melting keyword variables and changes to conditionals in Thermocycle
* :support:`- backported` a wild test appeared!

* :release:`2.0.1 <2015-02-06>`
* :feature:`- backported` properties attribute to `Well`, along with :ref:`well-set-properties` method
* :feature:`- backported` aliquot++, integer, boolean input types to harness.py
* :feature:`- backported` :ref:`protocol-dispense` Instruction and accompanying Protocol method for using a reagent dispenser
* :feature:`- backported` :ref:`protocol-dispense-full-plate`
* :feature:`- backported` warnings for `_mul_` and `_div_` scalar Unit operations
* :support:`- backported` README.rst
* :bug:`-` "speed" parameter in :ref:`protocol-spin` to "acceleration"
* :bug:`-` `well_type` from `_CONTAINER_TYPES`
* :bug:`-` spelling of luminescence :(

* :release:`2.0.0 <2014-01-24>`
* :feature:`-` harness.py for parameter conversion
* :support:`-` NumPy style docstrings for most methods
* :feature:`-` :ref:`container-inner-wells` method to exclude edges
* :feature:`-` 3-clause BSD license, contributor info
* :feature:`-` :ref:`wellGroup-indices` returns a list of string well indices
* :feature:`-` dead_volume_ul in _CONTAINER_TYPES
* :feature:`-` volume tracking upon :ref:`protocol-transfer` and :ref:`protocol-distribute`
* :feature:`-` "one_tip" option on :ref:`protocol-transfer`
* :support:`-` static methods `Pipette.transfers()` and `Pipette._transferGroup()`

* :release:`1.0.0 <2014-01-22>`
* :feature:`-` initializing ap-py
