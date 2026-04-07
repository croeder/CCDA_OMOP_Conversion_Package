"""
Integration tests for parse_doc() in data_driven_parse.py.

These tests run against real CCDA sample files in resources/ and validate
that the output structure matches expectations (keys present, record counts,
field types) without requiring a full OMOP database.
"""

import datetime
import os
import unittest

from ccda_to_omop.metadata import get_meta_dict
import ccda_to_omop.data_driven_parse as DDP

RESOURCES_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'resources'
)


def resource(filename):
    return os.path.join(RESOURCES_DIR, filename)


class TestParseDocReturnsDict(unittest.TestCase):
    """parse_doc() returns a dict keyed by config name."""

    @classmethod
    def setUpClass(cls):
        cls.meta = get_meta_dict()

    def test_returns_dict(self):
        result = DDP.parse_doc(resource('bare-minimum_Results.xml'), self.meta, '')
        self.assertIsInstance(result, dict)

    def test_known_configs_present(self):
        result = DDP.parse_doc(resource('bare-minimum_Results.xml'), self.meta, '')
        for config in ('Person', 'Visit', 'Location'):
            self.assertIn(config, result, f"Expected config '{config}' in result")

    def test_all_values_are_lists_or_none(self):
        result = DDP.parse_doc(resource('bare-minimum_Results.xml'), self.meta, '')
        for config_name, records in result.items():
            self.assertTrue(
                records is None or isinstance(records, list),
                f"Config '{config_name}' value should be list or None, got {type(records)}"
            )

    def test_records_are_dicts(self):
        result = DDP.parse_doc(resource('bare-minimum_Results.xml'), self.meta, '')
        for config_name, records in result.items():
            if records:
                for rec in records:
                    self.assertIsInstance(
                        rec, dict,
                        f"Record in '{config_name}' should be a dict"
                    )


class TestParseDocPersonRecord(unittest.TestCase):
    """Person records from a known sample file have expected fields."""

    @classmethod
    def setUpClass(cls):
        cls.meta = get_meta_dict()
        result = DDP.parse_doc(resource('bare-minimum_Results.xml'), cls.meta, '')
        cls.person_records = result.get('Person', [])

    def test_person_record_count(self):
        self.assertGreater(len(self.person_records), 0, "Expected at least one Person record")

    def test_person_has_required_fields(self):
        required = ['person_id', 'gender_concept_id', 'year_of_birth',
                    'race_concept_id', 'ethnicity_concept_id']
        for rec in self.person_records:
            for field in required:
                self.assertIn(field, rec, f"Person record missing field '{field}'")

    def test_person_id_field_present(self):
        # person_id may be None in bare-minimum docs (no patient ID element),
        # but the field key must exist in every Person record.
        for rec in self.person_records:
            self.assertIn('person_id', rec, "person_id key should be present in Person record")


class TestParseDocVisitRecord(unittest.TestCase):
    """Visit records have expected fields and date types."""

    @classmethod
    def setUpClass(cls):
        cls.meta = get_meta_dict()
        result = DDP.parse_doc(resource('bare-minimum_Results.xml'), cls.meta, '')
        cls.visit_records = result.get('Visit', [])

    def test_visit_record_count(self):
        self.assertGreater(len(self.visit_records), 0, "Expected at least one Visit record")

    def test_visit_has_required_fields(self):
        required = ['visit_occurrence_id', 'person_id', 'visit_concept_id',
                    'visit_start_date', 'visit_end_date']
        for rec in self.visit_records:
            for field in required:
                self.assertIn(field, rec, f"Visit record missing field '{field}'")

    def test_visit_dates_are_date_type(self):
        for rec in self.visit_records:
            for date_field in ('visit_start_date', 'visit_end_date'):
                val = rec.get(date_field)
                if val is not None:
                    self.assertIsInstance(
                        val, (datetime.date, datetime.datetime),
                        f"{date_field} should be a date/datetime, got {type(val)}"
                    )


class TestParseDocSingleConfig(unittest.TestCase):
    """parse_doc() with a specific parse_config only processes that config."""

    @classmethod
    def setUpClass(cls):
        cls.meta = get_meta_dict()

    def test_single_config_person_only(self):
        result = DDP.parse_doc(resource('bare-minimum_Results.xml'), self.meta, 'Person')
        self.assertIn('Person', result)
        # Other configs should not appear
        for config_name in result:
            self.assertEqual(
                config_name, 'Person',
                f"Expected only 'Person' config, got '{config_name}'"
            )

    def test_single_config_returns_records(self):
        result = DDP.parse_doc(resource('bare-minimum_Results.xml'), self.meta, 'Person')
        self.assertGreater(len(result.get('Person', [])), 0)


class TestParseDocMultipleFiles(unittest.TestCase):
    """parse_doc() works across multiple sample files without raising."""

    @classmethod
    def setUpClass(cls):
        cls.meta = get_meta_dict()

    def _parse(self, filename):
        path = resource(filename)
        if not os.path.exists(path):
            self.skipTest(f"{filename} not found in resources/")
        return DDP.parse_doc(path, self.meta, '')

    def test_ccd_sample(self):
        result = self._parse('CCD-Sample.xml')
        self.assertIsInstance(result, dict)
        self.assertIn('Person', result)

    def test_ambulatory_sample(self):
        result = self._parse('CCDA_CCD_b1_Ambulatory_v2.xml')
        self.assertIsInstance(result, dict)

    def test_inpatient_sample(self):
        result = self._parse('CCDA_CCD_b1_InPatient_v2.xml')
        self.assertIsInstance(result, dict)

    def test_measurement_results(self):
        result = self._parse('bare-minimum_Results.xml')
        measurement_configs = [k for k in result if k.startswith('MEASUREMENT')]
        self.assertGreater(len(measurement_configs), 0, "Expected at least one MEASUREMENT config")


if __name__ == '__main__':
    unittest.main()
