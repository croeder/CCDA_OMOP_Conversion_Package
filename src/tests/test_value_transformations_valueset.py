import unittest
import numpy as np
import ccda_to_omop.value_transformations as VT
import ccda_to_omop.util as U
import pathlib


mock_map = {
    ('2.16.840.1.113883.5.1', 'F'): [{
        'target_concept_id': np.int32(8532), 
        'source_concept_id': np.int32(8532), 
        'target_domain_id': 'Gender'}]
}
#VT.set_codemap_dict(mock_map)
home=pathlib.Path(__file__).parent.parent.parent.resolve()
codemap_dict = U.create_codemap_dict_from_csv(f"{home}/resources/map.csv")
VT.set_codemap_dict(codemap_dict)

class ValueTransformTest_valueset(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vocab_oid = '2.16.840.1.113883.5.1'
        self.concept_code = 'F'
        self.expected_concept_id = 8532
        self.expected_source_concept_id = 8532
        self.expected_domain_id = 'Gender' 

    def test_valueset_xwalk_concept_id(self):
        args_dict = { 'vocabulary_oid': self.vocab_oid,
                      'concept_code': self.concept_code,
                      'default': 0 }
        concept_id = VT.valueset_xwalk_concept_id(args_dict)
        self.assertEqual(concept_id, self.expected_concept_id)  ############3 valueset is returning strings for concept_ids
                         

    def test_valueset_xwalk_domain_id(self):
        args_dict = { 'vocabulary_oid': self.vocab_oid,
                      'concept_code': self.concept_code,
                      'default': 0 }
        domain_id = VT.valueset_xwalk_domain_id(args_dict)
        self.assertEqual(domain_id, self.expected_domain_id)


    def test_valueset_xwalk_default(self):
        args_dict = { 'vocabulary_oid': self.vocab_oid, 
                      'concept_code': 'bogus', 
                      'default': -1 }
        concept_id = VT.valueset_xwalk_concept_id(args_dict)
        self.assertEqual(concept_id, -1) 


    
