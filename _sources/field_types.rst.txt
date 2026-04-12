Field Types (config_type reference)
===================================

Each field in a parse configuration has a ``config_type`` that controls how
the parser populates it. The behaviour of each type is implemented in
``data_driven_parse.py`` by a corresponding ``do_*`` function.

None
----

*Implemented by:* ``do_none_fields()``

Set fields whose config_type is None to None in output_dict.

CONSTANT
--------

*Implemented by:* ``do_constant_fields()``

Write CONSTANT fields from config into output_dict, truncating strings to the allowed length.

FILENAME
--------

*Implemented by:* ``do_filename_fields()``

Write the source filename into any FILENAME-typed fields in output_dict.

FIELD
-----

*Implemented by:* ``do_basic_fields()``

Extract FIELD and PK values from the XML element and write them into output_dict.

PK values are also appended to pk_dict so downstream FK fields can reference them.
String values are whitespace-normalized and truncated to the configured max length.

FK
--

*Implemented by:* ``do_foreign_key_fields()``

When a configuration has an FK field, it uses the tag in that configuration
to find corresponding values from PK fields.  This mechanism is intended for
PKs uniquely identified in a CCDA document header for any places in the sections
it would be used as an FK. This is typically true for person_id and visit_occurrence_id,
but there are exceptions. In particular, some documents have multiple encounters, so
you can't just naively choose the only visit_id because there are many.

Choosing the visit is more complicated, because it requires a join (on date ranges)
between the domain table and the encounters table, or portion of the header that
has encompassingEncounters in it. This code, the do_foreign_key_fields() function
operates in too narrow a context for that join. These functions are scoped down
to processing a single config entry for a particular OMOP domain. The output_dict,
parameter is just for that one domain. It wouldn't include the encounters.
For example, the measurement_results.py file has a configuration for parsing OMOP
measurement rows out of an XML file. The visit.py would have been previosly processed
and it's rows stashed away elsewhere in the parse_doc() function whose scope is large
enough to consider all the configurations. So the visit choice/reconciliation
must happen from there.

TL;DR not all foreign keys are resolved here. In particular, domain FK references,
visit_occurrence_id, in cases where more than a single encounter has previously been
parsed, are not, can not, be resolved here. See the parse_doc() function for how
it is handled there.

DERIVED
-------

*Implemented by:* ``do_derived_fields()``

Do/compute derived values now that their inputs should be available in the output_dict
Except for a special argument named 'default', when the value is what is other wise the field to look up in the output dict.

This set-up is for functions that expect explicit named arguments. This code here adds values for those arguments to the
the dictionary passed to the function.
It's tempting to want to pass a list of arguments, but that's not how this function works.

Also a PK

DERIVED2
--------

*Implemented by:* ``do_derived2_fields()``

Compute DERIVED2 fields using functions that receive the full output_dict and argument_list.

Unlike DERIVED, the called function is responsible for fetching its own values from
output_dict using the key_list in argument_list, allowing a variable number of inputs.

HASH
----

*Implemented by:* ``do_hash_fields()``

Compute HASH fields by hashing a list of named input fields into a single ID.

Similar to DERIVED but takes a list of field names rather than individually named arguments.
The resulting hash is also stored in pk_dict so it can be used as a PK/FK reference.
Note: hash IDs are 64-bit but OMOP integer columns are typically 32-bit — use with care.
See the code for data_type-based conversion logic.
    where a different kind of hash is beat into an integer.

    ALSO A PK

PRIORITY
--------

*Implemented by:* ``do_priority_fields()``

ARGS expected in config:
    'config_type': 'PRIORITY',
    'defult': 0, in case there is no non-null value in the priority change and we don't want a null value in the end.
    'order': 17
Returns the list of  priority_names so the chosen one (first non-null) can be
added to output fields Also, adds this field to the PK list?
This is basically what SQL calls a coalesce.

Within the config_dict, find all fields tagged with priority and group
them by their priority names in a dictionary keyed by that name
Ex. { 'person_id': [ ('person_id_ssn', 1), ('person_id_unknown', 2) ]
Sort them, choose the first one that is not None.

NB now there is a separate config_type PRIORITY to compliment the priority attribute.
So you might have person_id_npi, person_id_ssn and person_id_hash tagged with priority
attributes to create a field person_id, but then also another field, just plain person_id.
The point of it is to have a unique place to put that field's order attribute. The code
here (and in the ordering code later) must be aware of a  that field in the
config_dict (where it isn't used) ...and not clobber it. It's an issue over in the
sorting/ordering.
