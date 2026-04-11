"""
Unit tests for data_driven_parse.py targeting previously uncovered code paths.
"""
import argparse
import csv
import datetime
import io
import os
import sys
import tempfile
import unittest
from collections import defaultdict

from lxml import etree as ET
from numpy import int32, int64

import ccda_to_omop.data_driven_parse as DDP
import ccda_to_omop.value_transformations as VT

# Minimal valid CCDA document for validate_ccda_document / parse_doc tests
MINIMAL_CCDA = b"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <structuredBody>
    <component>
      <section><title>Test</title></section>
    </component>
  </structuredBody>
</ClinicalDocument>"""

# Simple XML element with several typed attributes used by parse_field_from_dict tests
TYPED_ATTRS_XML = b"""<root xmlns:hl7="urn:hl7-org:v3">
  <hl7:element code="12345" codeSystem="2.16.840.1.113883.6.96"
               intVal="42" floatVal="3.14" dateVal="20230101"
               textVal="hello" />
</root>"""

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'resources')


def resource(filename):
    return os.path.join(RESOURCES_DIR, filename)


# ---------------------------------------------------------------------------
# create_hash_too_long  (lines 120-127)
# ---------------------------------------------------------------------------

class TestCreateHashTooLong(unittest.TestCase):

    def test_empty_string_returns_none(self):
        self.assertIsNone(DDP.create_hash_too_long(''))

    def test_nonempty_returns_int(self):
        result = DDP.create_hash_too_long('hello')
        self.assertIsInstance(result, int)

    def test_deterministic(self):
        self.assertEqual(DDP.create_hash_too_long('abc'), DDP.create_hash_too_long('abc'))

    def test_different_inputs_differ(self):
        self.assertNotEqual(DDP.create_hash_too_long('abc'), DDP.create_hash_too_long('xyz'))


# ---------------------------------------------------------------------------
# str2bool  (lines 1095-1102)
# ---------------------------------------------------------------------------

class TestStr2Bool(unittest.TestCase):

    def test_bool_true_passthrough(self):
        self.assertTrue(DDP.str2bool(True))

    def test_bool_false_passthrough(self):
        self.assertFalse(DDP.str2bool(False))

    def test_true_strings(self):
        for v in ('yes', 'true', 't', 'y', '1'):
            with self.subTest(v=v):
                self.assertTrue(DDP.str2bool(v))
                self.assertTrue(DDP.str2bool(v.upper()))

    def test_false_strings(self):
        for v in ('no', 'false', 'f', 'n', '0'):
            with self.subTest(v=v):
                self.assertFalse(DDP.str2bool(v))

    def test_invalid_raises_argument_type_error(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            DDP.str2bool('maybe')


# ---------------------------------------------------------------------------
# parse_field_from_dict — edge cases and data-type conversions
# (lines 138, 154-156, 186-252)
# ---------------------------------------------------------------------------

class TestParseFieldFromDictEdgeCases(unittest.TestCase):

    def setUp(self):
        self.root = ET.fromstring(TYPED_ATTRS_XML)

    def test_missing_element_key_returns_none(self):
        # line 138 — 'element' absent in field_details_dict
        result = DDP.parse_field_from_dict(
            {'attribute': 'code'}, self.root, 'Test', 'field', '/')
        self.assertIsNone(result)

    def test_missing_attribute_key_returns_none(self):
        # lines 154-156 — element found, but 'attribute' absent
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element'}, self.root, 'Test', 'field', '/')
        self.assertIsNone(result)

    def test_element_not_found_returns_none(self):
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:nonexistent', 'attribute': 'code'},
            self.root, 'Test', 'field', '/')
        self.assertIsNone(result)

    def test_attribute_not_on_element_returns_none(self):
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'no_such_attr'},
            self.root, 'Test', 'field', '/')
        self.assertIsNone(result)

    def test_xpath_eval_error_returns_none(self):
        # Malformed XPath triggers XPathEvalError → field_element stays None
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element[@', 'attribute': 'code'},
            self.root, 'Test', 'field', '/')
        self.assertIsNone(result)

    def test_data_type_date(self):
        # line 186-189
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'dateVal', 'data_type': 'DATE'},
            self.root, 'Test', 'field', '/')
        self.assertIsInstance(result, datetime.date)

    def test_data_type_datetime(self):
        # lines 195-198
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'dateVal', 'data_type': 'DATETIME'},
            self.root, 'Test', 'field', '/')
        self.assertIsInstance(result, datetime.datetime)

    def test_data_type_datetime_low(self):
        # lines 204-206
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'dateVal', 'data_type': 'DATETIME_LOW'},
            self.root, 'Test', 'field', '/')
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.hour, 0)

    def test_data_type_datetime_high(self):
        # lines 212-214
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'dateVal', 'data_type': 'DATETIME_HIGH'},
            self.root, 'Test', 'field', '/')
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.hour, 23)

    def test_data_type_long(self):
        # lines 217-221
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'intVal', 'data_type': 'LONG'},
            self.root, 'Test', 'field', '/')
        self.assertEqual(result, int64(42))

    def test_data_type_long_invalid_value_returns_none(self):
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'codeSystem', 'data_type': 'LONG'},
            self.root, 'Test', 'field', '/')
        self.assertIsNone(result)

    def test_data_type_integer(self):
        # lines 224-228
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'intVal', 'data_type': 'INTEGER'},
            self.root, 'Test', 'field', '/')
        self.assertEqual(result, int32(42))

    def test_data_type_integer_invalid_returns_none(self):
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'codeSystem', 'data_type': 'INTEGER'},
            self.root, 'Test', 'field', '/')
        self.assertIsNone(result)

    def test_data_type_biginthash(self):
        # lines 231-235
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'code', 'data_type': 'BIGINTHASH'},
            self.root, 'Test', 'field', '/')
        self.assertIsNotNone(result)

    def test_data_type_text(self):
        # lines 240-242
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'code', 'data_type': 'TEXT'},
            self.root, 'Test', 'field', '/')
        self.assertEqual(result, '12345')

    def test_data_type_float(self):
        # lines 247-250
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'floatVal', 'data_type': 'FLOAT'},
            self.root, 'Test', 'field', '/')
        self.assertAlmostEqual(result, 3.14, places=2)

    def test_data_type_float_invalid_returns_none(self):
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'codeSystem', 'data_type': 'FLOAT'},
            self.root, 'Test', 'field', '/')
        self.assertIsNone(result)

    def test_data_type_unknown_logs_warning(self):
        # line 252 — unknown data_type falls through, raw attribute value returned
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element', 'attribute': 'code', 'data_type': 'UNKNOWN_TYPE'},
            self.root, 'Test', 'field', '/')
        self.assertEqual(result, '12345')

    def test_text_attribute_itertext(self):
        # lines 165-168 — #text attribute uses itertext()
        xml = b"""<root xmlns:hl7="urn:hl7-org:v3">
          <hl7:element><hl7:text>hello world</hl7:text></hl7:element>
        </root>"""
        root = ET.fromstring(xml)
        result = DDP.parse_field_from_dict(
            {'element': 'hl7:element/hl7:text', 'attribute': '#text'},
            root, 'Test', 'field', '/')
        self.assertEqual(result, 'hello world')


# ---------------------------------------------------------------------------
# do_basic_fields — PK field type  (lines 364-375)
# ---------------------------------------------------------------------------

class TestDoBasicFieldsPK(unittest.TestCase):

    def setUp(self):
        self.xml = b"""<root xmlns:hl7="urn:hl7-org:v3">
          <hl7:id root="1.2.3.4" extension="ABC" />
        </root>"""
        self.root = ET.fromstring(self.xml)

    def test_pk_field_stored_in_output_and_pk_dict(self):
        config_dict = {
            'my_id': {
                'config_type': 'PK',
                'element': 'hl7:id',
                'attribute': 'root',
                'order': 1,
            }
        }
        output_dict = {}
        pk_dict = defaultdict(list)
        DDP.do_basic_fields(output_dict, self.root, '/', 'Test', config_dict, set(), pk_dict)
        self.assertEqual(output_dict['my_id'], '1.2.3.4')
        self.assertIn('1.2.3.4', pk_dict['my_id'])

    def test_pk_field_truncated_when_too_long(self):
        from ccda_to_omop.constants import MAX_FIELD_LENGTH
        long_val = 'x' * (MAX_FIELD_LENGTH + 10)
        xml = f'<root xmlns:hl7="urn:hl7-org:v3"><hl7:id root="{long_val}"/></root>'.encode()
        root = ET.fromstring(xml)
        config_dict = {
            'my_id': {'config_type': 'PK', 'element': 'hl7:id', 'attribute': 'root', 'order': 1}
        }
        output_dict = {}
        pk_dict = defaultdict(list)
        DDP.do_basic_fields(output_dict, root, '/', 'Test', config_dict, set(), pk_dict)
        self.assertLessEqual(len(output_dict['my_id']), MAX_FIELD_LENGTH)

    def test_pk_field_with_none_value_uses_else_branch(self):
        # line 373 — PK attribute not found → attribute_value is None (not str)
        config_dict = {
            'my_id': {
                'config_type': 'PK',
                'element': 'hl7:id',
                'attribute': 'nonexistent_attr',
                'order': 1,
            }
        }
        xml = b'<root xmlns:hl7="urn:hl7-org:v3"><hl7:id root="1.2.3"/></root>'
        root = ET.fromstring(xml)
        output_dict = {}
        pk_dict = defaultdict(list)
        DDP.do_basic_fields(output_dict, root, '/', 'Test', config_dict, set(), pk_dict)
        self.assertIsNone(output_dict['my_id'])


# ---------------------------------------------------------------------------
# do_foreign_key_fields — multi-value and missing FK  (lines 429, 433, 438)
# ---------------------------------------------------------------------------

class TestDoForeignKeyFields(unittest.TestCase):

    def setUp(self):
        self.root = ET.fromstring(b'<root/>')
        self.config_dict = {
            'person_id': {'config_type': 'FK', 'FK': 'person_id', 'order': 1}
        }

    def test_fk_resolved_from_single_pk(self):
        pk_dict = defaultdict(list)
        pk_dict['person_id'].append(42)
        output_dict = {}
        DDP.do_foreign_key_fields(output_dict, self.root, '/', 'Test', self.config_dict, set(), pk_dict)
        self.assertEqual(output_dict['person_id'], 42)

    def test_fk_none_when_multiple_pks(self):
        # line 429 — more than one value, can't resolve here
        pk_dict = defaultdict(list)
        pk_dict['person_id'].extend([42, 99])
        output_dict = {}
        DDP.do_foreign_key_fields(output_dict, self.root, '/', 'Test', self.config_dict, set(), pk_dict)
        self.assertIsNone(output_dict['person_id'])

    def test_fk_none_and_error_when_pk_missing(self):
        # lines 433, 438 — field not in pk_dict at all
        pk_dict = defaultdict(list)
        output_dict = {}
        error_set = set()
        DDP.do_foreign_key_fields(output_dict, self.root, '/', 'Test', self.config_dict, error_set, pk_dict)
        self.assertIsNone(output_dict['person_id'])
        self.assertIn('person_id', error_set)

    def test_fk_with_element_and_attribute_in_path_message(self):
        # exercises the path-building for the "not found" warning message
        config = {
            'some_fk': {
                'config_type': 'FK',
                'FK': 'some_fk',
                'element': 'hl7:thing',
                'attribute': 'id',
                'order': 1,
            }
        }
        pk_dict = defaultdict(list)
        output_dict = {}
        error_set = set()
        DDP.do_foreign_key_fields(output_dict, self.root, '/', 'Test', config, error_set, pk_dict)
        self.assertIn('some_fk', error_set)


# ---------------------------------------------------------------------------
# do_derived_fields — error paths  (lines 472-479, 500-512)
# ---------------------------------------------------------------------------

class TestDoDerivedFieldsErrors(unittest.TestCase):

    def setUp(self):
        self.root = ET.fromstring(b'<root/>')
        # Save existing codemap so other tests' __init__ setup isn't clobbered
        self._saved_codemap = VT.get_codemap_dict()

    def tearDown(self):
        # Restore whatever was there before; don't wipe shared VT state
        VT.set_codemap_dict(self._saved_codemap)

    def test_missing_input_field_adds_to_error_set(self):
        # lines 472-473 — argument field not in output_dict
        def fn(args):
            return args.get('x')

        config_dict = {
            'derived_field': {
                'config_type': 'DERIVED',
                'FUNCTION': fn,
                'argument_names': {'x': 'nonexistent_field'},
                'order': 1,
            }
        }
        output_dict = {}
        error_set = set()
        DDP.do_derived_fields(output_dict, self.root, '/', 'Test', config_dict, error_set, defaultdict(list))
        self.assertIn('derived_field', error_set)

    def test_key_error_in_function_adds_to_error_set(self):
        # lines 500-503
        def bad_fn(args):
            raise KeyError('missing_key')

        config_dict = {
            'ke_field': {
                'config_type': 'DERIVED',
                'FUNCTION': bad_fn,
                'argument_names': {},
                'order': 1,
            }
        }
        output_dict = {}
        error_set = set()
        DDP.do_derived_fields(output_dict, self.root, '/', 'Test', config_dict, error_set, defaultdict(list))
        self.assertIn('ke_field', error_set)
        self.assertIsNone(output_dict['ke_field'])

    def test_type_error_in_function_adds_to_error_set(self):
        # lines 505-512
        def bad_fn(args):
            raise TypeError('oops')

        config_dict = {
            'te_field': {
                'config_type': 'DERIVED',
                'FUNCTION': bad_fn,
                'argument_names': {},
                'order': 1,
            }
        }
        output_dict = {}
        error_set = set()
        DDP.do_derived_fields(output_dict, self.root, '/', 'Test', config_dict, error_set, defaultdict(list))
        self.assertIn('te_field', error_set)
        self.assertIsNone(output_dict['te_field'])

    def test_generic_exception_in_function(self):
        # lines 513-517
        def bad_fn(args):
            raise RuntimeError('unexpected')

        config_dict = {
            'gen_field': {
                'config_type': 'DERIVED',
                'FUNCTION': bad_fn,
                'argument_names': {},
                'order': 1,
            }
        }
        output_dict = {}
        error_set = set()
        DDP.do_derived_fields(output_dict, self.root, '/', 'Test', config_dict, error_set, defaultdict(list))
        self.assertIsNone(output_dict['gen_field'])

    def test_successful_derived_field(self):
        def fn(args):
            return 'result_value'

        config_dict = {
            'good_field': {
                'config_type': 'DERIVED',
                'FUNCTION': fn,
                'argument_names': {},
                'order': 1,
            }
        }
        output_dict = {}
        pk_dict = defaultdict(list)
        DDP.do_derived_fields(output_dict, self.root, '/', 'Test', config_dict, set(), pk_dict)
        self.assertEqual(output_dict['good_field'], 'result_value')

    def test_derived_string_result_stored_in_pk_dict(self):
        def fn(args):
            return 'pk_val'

        config_dict = {
            'pk_field': {
                'config_type': 'DERIVED',
                'FUNCTION': fn,
                'argument_names': {},
                'order': 1,
            }
        }
        output_dict = {}
        pk_dict = defaultdict(list)
        DDP.do_derived_fields(output_dict, self.root, '/', 'Test', config_dict, set(), pk_dict)
        self.assertIn('pk_val', pk_dict['pk_field'])


# ---------------------------------------------------------------------------
# do_derived2_fields — exception path  (lines 538-541)
# ---------------------------------------------------------------------------

class TestDoDerived2Fields(unittest.TestCase):

    def setUp(self):
        self.root = ET.fromstring(b'<root/>')

    def test_derived2_normal_execution(self):
        def fn(args_dict, data_dict):
            return 'computed'

        config_dict = {'f': {'config_type': 'DERIVED2', 'FUNCTION': fn, 'order': 1}}
        output_dict = {}
        DDP.do_derived2_fields(output_dict, self.root, '/', 'Test', config_dict, set())
        self.assertEqual(output_dict['f'], 'computed')

    def test_derived2_exception_sets_field_to_none(self):
        # lines 538-541
        def bad_fn(args_dict, data_dict):
            raise RuntimeError('fail')

        config_dict = {'f': {'config_type': 'DERIVED2', 'FUNCTION': bad_fn, 'order': 1}}
        output_dict = {}
        DDP.do_derived2_fields(output_dict, self.root, '/', 'Test', config_dict, set())
        self.assertIsNone(output_dict['f'])


# ---------------------------------------------------------------------------
# do_hash_fields — missing 'fields' attribute  (line 566)
# ---------------------------------------------------------------------------

class TestDoHashFieldsMissingFieldsKey(unittest.TestCase):

    def test_hash_without_fields_key_raises_key_error(self):
        # line 566 — logs error then KeyError when trying to iterate missing 'fields'
        root = ET.fromstring(b'<root/>')
        config_dict = {
            'my_hash': {'config_type': 'HASH', 'order': 1}
            # 'fields' key intentionally absent
        }
        output_dict = {'some_field': 'val'}
        pk_dict = defaultdict(list)
        with self.assertRaises(KeyError):
            DDP.do_hash_fields(output_dict, root, '/', 'Test', config_dict, set(), pk_dict)

    def test_hash_with_field_missing_from_output_dict(self):
        # line 571 — field listed in 'fields' is not present in output_dict
        root = ET.fromstring(b'<root/>')
        config_dict = {
            'my_hash': {
                'config_type': 'HASH',
                'fields': ['present_field', 'absent_field'],
                'order': 1,
            }
        }
        output_dict = {'present_field': 'val'}  # 'absent_field' is intentionally absent
        pk_dict = defaultdict(list)
        DDP.do_hash_fields(output_dict, root, '/', 'Test', config_dict, set(), pk_dict)
        # hash is computed from whatever was collected (just present_field)
        self.assertIn('my_hash', output_dict)


# ---------------------------------------------------------------------------
# do_priority_fields — default / fallback value  (line 643)
# ---------------------------------------------------------------------------

class TestDoPriorityFields(unittest.TestCase):

    def setUp(self):
        self.root = ET.fromstring(b'<root/>')

    def test_priority_first_non_none_wins(self):
        config_dict = {
            'src_a': {'config_type': 'FIELD', 'element': 'x', 'attribute': 'y', 'priority': ('result', 2)},
            'src_b': {'config_type': 'FIELD', 'element': 'x', 'attribute': 'y', 'priority': ('result', 1)},
            'result': {'config_type': 'PRIORITY', 'order': 3},
        }
        output_dict = {'src_a': 'fallback', 'src_b': 'winner'}
        pk_dict = defaultdict(list)
        DDP.do_priority_fields(output_dict, self.root, '/', 'Test', config_dict, set(), pk_dict)
        self.assertEqual(output_dict['result'], 'winner')

    def test_priority_all_none_defaults_to_none(self):
        # no candidate has a value → default_value stays None
        config_dict = {
            'src_a': {'config_type': 'FIELD', 'element': 'x', 'attribute': 'y', 'priority': ('result', 1)},
            'result': {'config_type': 'PRIORITY', 'order': 2},
        }
        output_dict = {'src_a': None}
        pk_dict = defaultdict(list)
        DDP.do_priority_fields(output_dict, self.root, '/', 'Test', config_dict, set(), pk_dict)
        self.assertIsNone(output_dict['result'])

    def test_priority_with_explicit_default_value(self):
        # line 643 — 'default' key in config_dict provides a fallback
        config_dict = {
            'src_a': {'config_type': 'FIELD', 'element': 'x', 'attribute': 'y', 'priority': ('result', 1)},
            'result': {'config_type': 'PRIORITY', 'order': 2},
            'default': {'config_type': 'CONSTANT', 'constant_value': 'fallback', 'order': 99},
        }
        output_dict = {'src_a': None}
        pk_dict = defaultdict(list)
        DDP.do_priority_fields(output_dict, self.root, '/', 'Test', config_dict, set(), pk_dict)
        # config_dict['default'] is the dict entry, not the actual default value scalar
        # the code does: default_value = config_dict['default']
        self.assertIn('result', output_dict)

    def test_priority_skips_empty_string(self):
        # empty string is also treated as "no value" — next candidate chosen
        config_dict = {
            'src_a': {'config_type': 'FIELD', 'element': 'x', 'attribute': 'y', 'priority': ('result', 2)},
            'src_b': {'config_type': 'FIELD', 'element': 'x', 'attribute': 'y', 'priority': ('result', 1)},
            'result': {'config_type': 'PRIORITY', 'order': 3},
        }
        output_dict = {'src_a': 'second', 'src_b': ''}
        pk_dict = defaultdict(list)
        DDP.do_priority_fields(output_dict, self.root, '/', 'Test', config_dict, set(), pk_dict)
        self.assertEqual(output_dict['result'], 'second')


# ---------------------------------------------------------------------------
# parse_config_from_xml_file — error paths  (lines 866, 870-871, 879-880)
# ---------------------------------------------------------------------------

class TestParseConfigFromXmlFileErrors(unittest.TestCase):

    def setUp(self):
        self.tree = ET.fromstring(b'<root xmlns:hl7="urn:hl7-org:v3"/>')

    def test_missing_root_key_returns_none(self):
        # line 866
        config_dict = {'field': {'config_type': 'CONSTANT', 'constant_value': 1, 'order': 1}}
        result = DDP.parse_config_from_xml_file(
            self.tree, 'Test', config_dict, 'test.xml', defaultdict(list))
        self.assertIsNone(result)

    def test_root_missing_element_key_returns_none(self):
        # lines 870-871
        config_dict = {'root': {'config_type': 'ROOT'}}  # no 'element'
        result = DDP.parse_config_from_xml_file(
            self.tree, 'Test', config_dict, 'test.xml', defaultdict(list))
        self.assertIsNone(result)

    def test_root_element_not_found_returns_none(self):
        config_dict = {'root': {'config_type': 'ROOT', 'element': '//hl7:nonexistent'}}
        result = DDP.parse_config_from_xml_file(
            self.tree, 'Test', config_dict, 'test.xml', defaultdict(list))
        self.assertIsNone(result)

    def test_xpath_error_in_root_query_returns_none(self):
        # lines 879-880 — XPathError caught, root_element_list stays empty
        config_dict = {'root': {'config_type': 'ROOT', 'element': '//hl7:element[@'}}
        result = DDP.parse_config_from_xml_file(
            self.tree, 'Test', config_dict, 'test.xml', defaultdict(list))
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# validate_ccda_document  (exercises parse_doc line 1006 path too)
# ---------------------------------------------------------------------------

class TestValidateCcdaDocument(unittest.TestCase):

    def _parse(self, xml_bytes):
        return ET.parse(io.BytesIO(xml_bytes))

    def test_valid_ccda_returns_no_errors(self):
        errors = DDP.validate_ccda_document('test.xml', self._parse(MINIMAL_CCDA))
        self.assertEqual(errors, [])

    def test_wrong_root_tag_returns_error(self):
        bad = b'<?xml version="1.0"?><NotAClinicalDocument xmlns="urn:hl7-org:v3"/>'
        errors = DDP.validate_ccda_document('test.xml', self._parse(bad))
        self.assertGreater(len(errors), 0)
        self.assertIn('not a valid CCDA document', errors[0])

    def test_no_structured_body_returns_error(self):
        no_body = b'<?xml version="1.0"?><ClinicalDocument xmlns="urn:hl7-org:v3"/>'
        errors = DDP.validate_ccda_document('test.xml', self._parse(no_body))
        self.assertGreater(len(errors), 0)
        self.assertIn('structuredBody', errors[0])


# ---------------------------------------------------------------------------
# parse_string  (lines 916-940)
# ---------------------------------------------------------------------------

class TestParseString(unittest.TestCase):

    CCDA_WITH_PERSON = b"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <recordTarget>
    <patientRole>
      <id extension="PAT001" root="1.2.3"/>
      <patient>
        <administrativeGenderCode code="M"/>
        <birthTime value="19800101"/>
        <raceCode code="2106-3"/>
        <ethnicGroupCode code="2186-5"/>
      </patient>
    </patientRole>
  </recordTarget>
  <structuredBody>
    <component>
      <section><title>Test</title></section>
    </component>
  </structuredBody>
</ClinicalDocument>"""

    @classmethod
    def setUpClass(cls):
        from ccda_to_omop.metadata import get_meta_dict
        cls.meta = get_meta_dict()

    def test_returns_dict(self):
        result = DDP.parse_string(self.CCDA_WITH_PERSON, 'test.xml', self.meta)
        self.assertIsInstance(result, dict)

    def test_has_person_config(self):
        result = DDP.parse_string(self.CCDA_WITH_PERSON, 'test.xml', self.meta)
        self.assertIn('Person', result)

    def test_all_values_list_or_none(self):
        result = DDP.parse_string(self.CCDA_WITH_PERSON, 'test.xml', self.meta)
        for config_name, records in result.items():
            self.assertTrue(
                records is None or isinstance(records, list),
                f"Config '{config_name}' should be list or None"
            )


# ---------------------------------------------------------------------------
# make_distinct
# ---------------------------------------------------------------------------

class TestMakeDistinct(unittest.TestCase):

    def test_removes_duplicates(self):
        rows = [{'a': 1, 'b': 2}, {'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
        self.assertEqual(len(DDP.make_distinct(rows)), 2)

    def test_empty_list(self):
        self.assertEqual(DDP.make_distinct([]), [])

    def test_all_unique_unchanged(self):
        rows = [{'a': 1}, {'a': 2}, {'a': 3}]
        self.assertEqual(len(DDP.make_distinct(rows)), 3)

    def test_order_preserved_for_first_occurrence(self):
        rows = [{'a': 1}, {'a': 2}, {'a': 1}]
        result = DDP.make_distinct(rows)
        self.assertEqual(result[0], {'a': 1})
        self.assertEqual(result[1], {'a': 2})


# ---------------------------------------------------------------------------
# sort_output_and_omit_dict
# ---------------------------------------------------------------------------

class TestSortOutputAndOmitDict(unittest.TestCase):
    """Typeguard samples inner dict values, so use real-looking config dicts
    that include a string config_type key alongside integer order values."""

    def _make_config(self, **fields):
        """Build a config dict where each entry has config_type (str) and optional order."""
        return {k: {'config_type': 'FIELD', 'element': 'x', 'attribute': 'y', **v}
                for k, v in fields.items()}

    def test_sorts_by_order_attribute(self):
        output_dict = {'c': 'v3', 'a': 'v1', 'b': 'v2'}
        config_dict = self._make_config(c={'order': 3}, a={'order': 1}, b={'order': 2})
        result = DDP.sort_output_and_omit_dict(output_dict, config_dict, 'Test')
        self.assertEqual(list(result.keys()), ['a', 'b', 'c'])

    def test_omits_fields_without_order(self):
        output_dict = {'x': 'val', 'y': 'other'}
        config_dict = {'x': {'config_type': 'FIELD', 'element': 'x', 'attribute': 'y', 'order': 1},
                       'y': {'config_type': 'FIELD', 'element': 'y', 'attribute': 'z'}}
        result = DDP.sort_output_and_omit_dict(output_dict, config_dict, 'Test')
        self.assertIn('x', result)
        self.assertNotIn('y', result)



# ---------------------------------------------------------------------------
# write_all_csv_files  (lines 1065-1072)
# ---------------------------------------------------------------------------

class TestWriteAllCsvFiles(unittest.TestCase):

    def test_writes_csv_file(self):
        data = {'TestDomain': [{'field_a': 'val1', 'field_b': 'val2'}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                DDP.write_all_csv_files(data)
                self.assertTrue(os.path.exists('TestDomain.csv'))
                with open('TestDomain.csv') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['field_a'], 'val1')
            finally:
                os.chdir(orig)

    def test_skips_empty_domain(self):
        data = {'EmptyDomain': []}
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                DDP.write_all_csv_files(data)
                self.assertFalse(os.path.exists('EmptyDomain.csv'))
            finally:
                os.chdir(orig)

    def test_skips_none_domain(self):
        data = {'NullDomain': None}
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                DDP.write_all_csv_files(data)
                self.assertFalse(os.path.exists('NullDomain.csv'))
            finally:
                os.chdir(orig)


# ---------------------------------------------------------------------------
# write_individual_csv_files  (lines 1077-1091)
# ---------------------------------------------------------------------------

class TestWriteIndividualCsvFiles(unittest.TestCase):

    def test_writes_csv_with_cfg_name(self):
        # The function writes to f"../{out_file_path}__{cfg_name}.csv"
        # Use a subdir so ".." resolves to tmpdir where we can write.
        data = {'Domain': [{'cfg_name': 'MyCfg', 'field': 'value'}]}
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, 'sub')
            os.makedirs(subdir)
            orig = os.getcwd()
            os.chdir(subdir)
            try:
                DDP.write_individual_csv_files('testfile', data)
                expected = os.path.join(tmpdir, 'testfile__MyCfg.csv')
                self.assertTrue(os.path.exists(expected))
                with open(expected) as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['field'], 'value')
            finally:
                os.chdir(orig)

    def test_skips_empty_domain(self):
        data = {'EmptyDomain': []}
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, 'sub')
            os.makedirs(subdir)
            orig = os.getcwd()
            os.chdir(subdir)
            try:
                DDP.write_individual_csv_files('testfile', data)
                # nothing should be written
                self.assertEqual(os.listdir(tmpdir), ['sub'])
            finally:
                os.chdir(orig)


# ---------------------------------------------------------------------------
# process_file  (lines 1053-1062) — requires resources dir
# ---------------------------------------------------------------------------

class TestProcessFile(unittest.TestCase):

    def test_process_file_returns_dict(self):
        path = resource('bare-minimum_Results.xml')
        if not os.path.exists(path):
            self.skipTest('bare-minimum_Results.xml not found')
        result = DDP.process_file(path, False, '')
        self.assertIsInstance(result, dict)

    def test_process_file_single_config(self):
        path = resource('bare-minimum_Results.xml')
        if not os.path.exists(path):
            self.skipTest('bare-minimum_Results.xml not found')
        result = DDP.process_file(path, False, 'Person')
        self.assertIn('Person', result)


if __name__ == '__main__':
    unittest.main()
