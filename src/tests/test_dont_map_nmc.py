import unittest
import ccda_to_omop.value_transformations as VT
import ccda_to_omop.util as U
import pathlib
import numpy as np
from ccda_to_omop import package_constant_access


class Test_disallow_no_matching_concept(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        package_constant_access.set_allow_no_matching_concept(False)
        super().__init__(*args, **kwargs)
        self.vocab_oid = '2.16.840.1.113883.6.1'
        self.concept_code = '0000-0'
        self.expected_concept_id = None 
        self.expected_source_concept_id = None
        self.expected_domain_id = 'Observation'
        mock_map = {
            ('2.16.840.1.113883.6.1', '0000-0'): [{'target_concept_id': np.int32(0), 'target_domain_id': 'Observation', 'source_concept_id': np.int32(0)}] 
        }
        #VT.set_codemap_dict(mock_map)
        home=pathlib.Path(__file__).parent.parent.parent.resolve()
        codemap_dict = U.create_codemap_dict_from_csv(f"{home}/resources/map.csv")
        VT.set_codemap_dict(codemap_dict)
        self.args_dict = { 'vocabulary_oid': self.vocab_oid,
                      'concept_code': self.concept_code }
    

    def test_concept_id(self):
        concept_id = VT.codemap_xwalk_concept_id(self.args_dict)
        self.assertEqual(concept_id, self.expected_concept_id)


    def test_domain_id(self):
        concept_id = VT.codemap_xwalk_domain_id(self.args_dict)
        self.assertEqual(concept_id, self.expected_domain_id)


    def test_source_concept_id(self):
        concept_id = VT.codemap_xwalk_source_concept_id(self.args_dict)
        #self.assertEqual(concept_id, self.expected_default_value)
        # 0000-0 is in the map now with a 0. FIX 
        self.assertIsNone(concept_id)
