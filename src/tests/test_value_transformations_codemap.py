import unittest
import ccda_to_omop.value_transformations as VT
import ccda_to_omop.util as U
import pathlib
import numpy as np
from ccda_to_omop import package_constant_access


class ValueTransformTest_codemap(unittest.TestCase):
    #2.16.840.1.113883.6.1,11579-0,3019762,Measurement
    def __init__(self, *args, **kwargs):
        package_constant_access.set_allow_no_matching_concept(True)
        super().__init__(*args, **kwargs)
        self.vocab_oid = '2.16.840.1.113883.6.1'
        self.concept_code = '11579-0'
        self.expected_concept_id = 3019762
        self.expected_source_concept_id = 3019762
        self.expected_domain_id = 'Measurement'  ## ????
        mock_map = { 
            ('2.16.840.1.113883.6.1', '11579-0'): [{'target_concept_id': np.int32(3019762), 'target_domain_id': 'Measurement', 'source_concept_id': np.int32(3019762)}] 
        }
        #VT.set_codemap_dict(mock_map)
        home=pathlib.Path(__file__).parent.parent.parent.resolve()
        codemap_dict = U.create_codemap_dict_from_csv(f"{home}/resources/map.csv")
        VT.set_codemap_dict(codemap_dict)
    

    def test_concept_id(self):
        args_dict = { 'vocabulary_oid': self.vocab_oid,
                      'concept_code': self.concept_code,
                      'default': 0 }
        concept_id = VT.codemap_xwalk_concept_id(args_dict)
        self.assertEqual(concept_id, self.expected_concept_id)


    def test_domain_id(self):
        args_dict = { 'vocabulary_oid': self.vocab_oid,
                      'concept_code': self.concept_code,
                      'default': 0 }
        concept_id = VT.codemap_xwalk_domain_id(args_dict)
        self.assertEqual(concept_id, self.expected_domain_id)


    def test_source_conept_id(self):
        args_dict = { 'vocabulary_oid': self.vocab_oid,
                      'concept_code': self.concept_code,
                      'default': 0 }
        concept_id = VT.codemap_xwalk_source_concept_id(args_dict)
        self.assertEqual(concept_id, self.expected_source_concept_id)


