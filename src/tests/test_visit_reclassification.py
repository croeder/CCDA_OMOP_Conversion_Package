"""
Unit tests for reclassify_nested_visit_occurrences_as_detail() and its
helper functions in visit_reconciliation.py.
"""

import datetime
import unittest
from numpy import int64

import ccda_to_omop.visit_reconciliation as VR


def make_visit(visit_occurrence_id, person_id, concept_id,
               start_date, end_date, cfg_name='Visit'):
    """Helper: build a minimal visit_occurrence record."""
    return {
        'visit_occurrence_id': int64(visit_occurrence_id),
        'person_id': int64(person_id),
        'visit_concept_id': int64(concept_id),
        'visit_start_date': start_date,
        'visit_start_datetime': datetime.datetime.combine(start_date, datetime.time.min),
        'visit_end_date': end_date,
        'visit_end_datetime': datetime.datetime.combine(end_date, datetime.time.max),
        'visit_type_concept_id': int64(44818517),
        'cfg_name': cfg_name,
    }


INPATIENT = 9201   # OMOP inpatient concept
OUTPATIENT = 9202  # OMOP outpatient concept


class TestStripTz(unittest.TestCase):

    def test_strips_tz_from_aware_datetime(self):
        dt = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
        result = VR.strip_tz(dt)
        self.assertIsNone(result.tzinfo)
        self.assertEqual(result, datetime.datetime(2020, 1, 1))

    def test_leaves_naive_datetime_unchanged(self):
        dt = datetime.datetime(2020, 1, 1)
        self.assertEqual(VR.strip_tz(dt), dt)

    def test_leaves_date_unchanged(self):
        d = datetime.date(2020, 1, 1)
        self.assertEqual(VR.strip_tz(d), d)

    def test_leaves_none_unchanged(self):
        self.assertIsNone(VR.strip_tz(None))


class TestGetVisitDurationDays(unittest.TestCase):

    def test_same_day(self):
        # make_visit sets start_datetime to midnight and end_datetime to 23:59:59,
        # so a same-day visit has duration ~1 day (nearly 24 hours), not 0.
        visit = make_visit(1, 1, OUTPATIENT,
                           datetime.date(2020, 1, 1), datetime.date(2020, 1, 1))
        duration = VR.get_visit_duration_days(visit)
        self.assertGreater(duration, 0.0)
        self.assertLess(duration, 1.5)

    def test_multi_day(self):
        # make_visit sets end_datetime to 23:59:59, so Jan 1 -> Jan 3 spans ~3 calendar days.
        visit = make_visit(1, 1, OUTPATIENT,
                           datetime.date(2020, 1, 1), datetime.date(2020, 1, 3))
        duration = VR.get_visit_duration_days(visit)
        self.assertGreater(duration, 1.0)
        self.assertLess(duration, 4.0)

    def test_missing_dates_returns_none(self):
        visit = {'visit_occurrence_id': int64(1)}
        self.assertIsNone(VR.get_visit_duration_days(visit))


class TestIsTemporallyContained(unittest.TestCase):

    def _visit(self, vid, start, end):
        return make_visit(vid, 1, OUTPATIENT, start, end)

    def test_child_fully_inside_parent(self):
        parent = self._visit(1, datetime.date(2020, 1, 1), datetime.date(2020, 1, 10))
        child  = self._visit(2, datetime.date(2020, 1, 3), datetime.date(2020, 1, 7))
        self.assertTrue(VR.is_temporally_contained(child, parent))

    def test_child_equals_parent(self):
        parent = self._visit(1, datetime.date(2020, 1, 1), datetime.date(2020, 1, 10))
        child  = self._visit(2, datetime.date(2020, 1, 1), datetime.date(2020, 1, 10))
        self.assertTrue(VR.is_temporally_contained(child, parent))

    def test_child_outside_parent(self):
        parent = self._visit(1, datetime.date(2020, 1, 1), datetime.date(2020, 1, 5))
        child  = self._visit(2, datetime.date(2020, 1, 6), datetime.date(2020, 1, 10))
        self.assertFalse(VR.is_temporally_contained(child, parent))

    def test_child_overlaps_but_not_contained(self):
        parent = self._visit(1, datetime.date(2020, 1, 1), datetime.date(2020, 1, 5))
        child  = self._visit(2, datetime.date(2020, 1, 3), datetime.date(2020, 1, 8))
        self.assertFalse(VR.is_temporally_contained(child, parent))

    def test_missing_dates_returns_false(self):
        parent = {'visit_occurrence_id': int64(1)}
        child  = {'visit_occurrence_id': int64(2)}
        self.assertFalse(VR.is_temporally_contained(child, parent))


class TestIdentifyInpatientParents(unittest.TestCase):

    def test_inpatient_short_stay_is_eligible(self):
        visit = make_visit(1, 1, INPATIENT,
                           datetime.date(2020, 1, 1), datetime.date(2020, 1, 5))
        result = VR.identify_inpatient_parents([visit])
        self.assertEqual(len(result), 1)

    def test_outpatient_excluded(self):
        visit = make_visit(1, 1, OUTPATIENT,
                           datetime.date(2020, 1, 1), datetime.date(2020, 1, 5))
        result = VR.identify_inpatient_parents([visit])
        self.assertEqual(len(result), 0)

    def test_inpatient_over_max_duration_excluded(self):
        visit = make_visit(1, 1, INPATIENT,
                           datetime.date(2020, 1, 1), datetime.date(2021, 3, 1))  # > 367 days
        result = VR.identify_inpatient_parents([visit])
        self.assertEqual(len(result), 0)

    def test_empty_list(self):
        self.assertEqual(VR.identify_inpatient_parents([]), [])


class TestReclassifyNestedVisits(unittest.TestCase):
    """Tests for the main reclassify_nested_visit_occurrences_as_detail() function."""

    def test_empty_omop_dict(self):
        result = VR.reclassify_nested_visit_occurrences_as_detail({})
        self.assertIsInstance(result, dict)

    def test_no_visits_returns_unchanged(self):
        omop_dict = {'Measurement': [{'measurement_id': int64(1)}]}
        result = VR.reclassify_nested_visit_occurrences_as_detail(omop_dict)
        self.assertIn('Measurement', result)

    def test_single_visit_no_reclassification(self):
        visit = make_visit(1, 1, OUTPATIENT,
                           datetime.date(2020, 1, 1), datetime.date(2020, 1, 2))
        omop_dict = {'Visit': [visit]}
        result = VR.reclassify_nested_visit_occurrences_as_detail(omop_dict)
        self.assertEqual(len(result['Visit']), 1)

    def test_nested_inpatient_child_becomes_visit_detail(self):
        """A child visit contained within an inpatient parent should be reclassified."""
        parent = make_visit(1, 1, INPATIENT,
                            datetime.date(2020, 1, 1), datetime.date(2020, 1, 10))
        child  = make_visit(2, 1, OUTPATIENT,
                            datetime.date(2020, 1, 3), datetime.date(2020, 1, 5))
        omop_dict = {'Visit': [parent, child]}
        result = VR.reclassify_nested_visit_occurrences_as_detail(omop_dict)

        # Parent stays in Visit; child moves to visit_detail config
        visit_ids = [v['visit_occurrence_id'] for v in result.get('Visit', [])]
        self.assertIn(int64(1), visit_ids, "Inpatient parent should remain in Visit")

        detail_config = result.get('VISITDETAIL_visit_occurrence', [])
        detail_ids = [d.get('visit_detail_id') for d in detail_config]
        self.assertIn(int64(2), detail_ids, "Child visit should be reclassified as visit_detail")

    def test_two_standalone_outpatient_visits_not_reclassified(self):
        """Two non-overlapping outpatient visits should both stay in Visit."""
        v1 = make_visit(1, 1, OUTPATIENT,
                        datetime.date(2020, 1, 1), datetime.date(2020, 1, 2))
        v2 = make_visit(2, 1, OUTPATIENT,
                        datetime.date(2020, 2, 1), datetime.date(2020, 2, 2))
        omop_dict = {'Visit': [v1, v2]}
        result = VR.reclassify_nested_visit_occurrences_as_detail(omop_dict)
        self.assertEqual(len(result.get('Visit', [])), 2)
        self.assertEqual(len(result.get('VISITDETAIL_visit_occurrence', [])), 0)

    def test_encompassing_encounter_merged_into_visit(self):
        """Visit_encompassingEncounter records should be merged into Visit."""
        enc = make_visit(10, 1, OUTPATIENT,
                         datetime.date(2020, 3, 1), datetime.date(2020, 3, 2),
                         cfg_name='Visit_encompassingEncounter')
        # Provide two visits so the function goes past the single-visit early-return path,
        # which is the path that actually merges and removes Visit_encompassingEncounter.
        enc2 = make_visit(11, 1, OUTPATIENT,
                          datetime.date(2020, 4, 1), datetime.date(2020, 4, 2),
                          cfg_name='Visit_encompassingEncounter')
        omop_dict = {'Visit_encompassingEncounter': [enc, enc2]}
        result = VR.reclassify_nested_visit_occurrences_as_detail(omop_dict)
        self.assertIn('Visit', result)
        visit_ids = [v['visit_occurrence_id'] for v in result['Visit']]
        self.assertIn(int64(10), visit_ids)
        self.assertIn(int64(11), visit_ids)
        # Source config is removed after merging
        self.assertNotIn('Visit_encompassingEncounter', result)


if __name__ == '__main__':
    unittest.main()
