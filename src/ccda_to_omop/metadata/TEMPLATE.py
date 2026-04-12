"""
Template for a new OMOP domain parse configuration.

Copy this file to a new name following the convention:
    DOMAIN-from-ccda_section.py       (e.g. CONDITION-from-problems.py)
    or for configs with a single section:
    domain_section.py                 (e.g. condition.py)

Then fill in the XPath expressions and field mappings for your target domain.
See condition.py for the simplest real-world example.
"""

import ccda_to_omop.value_transformations as VT

metadata = {

    # The key is the config name used in logs and output filenames.
    'MyDomain': {

        # ROOT: identifies the repeating XML element that produces one output row each.
        'root': {
            'config_type': 'ROOT',
            'expected_domain_id': 'Condition',          # OMOP domain name
            'element': (                                 # XPath from the document root
                "./hl7:component/hl7:structuredBody/hl7:component/hl7:section"
                "/hl7:templateId[@root='2.16.840.1.113883.10.20.22.2.5.1']"
                "/../hl7:entry/hl7:act/hl7:entryRelationship/hl7:observation"
            )
        },

        # HASH: surrogate primary key — hashed from a stable set of field values.
        'my_domain_id': {
            'config_type': 'HASH',
            'fields': ['person_id', 'my_concept_code', 'my_concept_code_system',
                       'my_start_date', 'my_end_date'],
            'order': 1
        },

        # FK: foreign key populated from a previously parsed config (e.g. Person).
        'person_id':            {'config_type': 'FK', 'FK': 'person_id',            'order': 2},
        'visit_occurrence_id':  {'config_type': 'FK', 'FK': 'visit_occurrence_id',  'order': 12},
        'provider_id':          {'config_type': 'FK', 'FK': 'provider_id',          'order': 11},

        # FIELD: extract an XML attribute value via XPath (relative to root element).
        'my_concept_code': {
            'config_type': 'FIELD',
            'element': 'hl7:value',
            'attribute': 'code'
        },
        'my_concept_code_system': {
            'config_type': 'FIELD',
            'element': 'hl7:value',
            'attribute': 'codeSystem'
        },

        # DERIVED: compute a value by calling a VT function with named arguments.
        'my_concept_id': {
            'config_type': 'DERIVED',
            'FUNCTION': VT.codemap_xwalk_concept_id,
            'argument_names': {
                'concept_code':   'my_concept_code',
                'vocabulary_oid': 'my_concept_code_system',
            },
            'order': 3
        },
        'domain_id': {
            'config_type': 'DERIVED',
            'FUNCTION': VT.codemap_xwalk_domain_id,
            'argument_names': {
                'concept_code':   'my_concept_code',
                'vocabulary_oid': 'my_concept_code_system',
            }
        },

        # FIELD with data_type: parse as DATE or DATETIME.
        'my_start_date': {
            'config_type': 'FIELD',
            'element': 'hl7:effectiveTime/hl7:low',
            'attribute': 'value',
            'data_type': 'DATE',
            'order': 4
        },
        'my_end_date': {
            'config_type': 'FIELD',
            'element': 'hl7:effectiveTime/hl7:high',
            'attribute': 'value',
            'data_type': 'DATE',
            'order': 5
        },

        # CONSTANT: fixed value written to every row.
        'my_type_concept_id': {
            'config_type': 'CONSTANT',
            'constant_value': 0,    # replace with the appropriate OMOP concept ID
            'order': 8
        },

        # None: column required by OMOP schema but not populated by this config.
        'visit_detail_id':   {'config_type': None, 'order': 13},

        # FILENAME and cfg_name are required on every config.
        'filename': {'config_type': 'FILENAME', 'order': 100},
        'cfg_name': {
            'config_type': 'CONSTANT',
            'constant_value': 'MyDomain',
            'length': 100,
            'order': 101
        },
    }
}
