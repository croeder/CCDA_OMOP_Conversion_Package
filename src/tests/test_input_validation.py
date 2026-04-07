"""
Tests for validate_ccda_document() and parse_doc() input validation
in data_driven_parse.py.
"""

import os
import tempfile
import unittest
from lxml import etree as ET

import ccda_to_omop.data_driven_parse as DDP

RESOURCES_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', 'resources'
)

VALID_CCDA = b"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <component>
    <structuredBody>
      <component>
        <section>
          <title>Results</title>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
"""

WRONG_ROOT = b"""<?xml version="1.0" encoding="UTF-8"?>
<SomeOtherDocument xmlns="urn:hl7-org:v3">
</SomeOtherDocument>
"""

MISSING_SECTIONS = b"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <component>
    <nonXMLBody>
      <text>plain text body</text>
    </nonXMLBody>
  </component>
</ClinicalDocument>
"""


class TestValidateCcdaDocument(unittest.TestCase):

    def _tree(self, xml_bytes):
        return ET.ElementTree(ET.fromstring(xml_bytes))

    def test_valid_ccda_returns_no_errors(self):
        tree = self._tree(VALID_CCDA)
        errors = DDP.validate_ccda_document("test.xml", tree)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_wrong_root_element_returns_error(self):
        tree = self._tree(WRONG_ROOT)
        errors = DDP.validate_ccda_document("test.xml", tree)
        self.assertEqual(len(errors), 1)
        self.assertIn("not a valid CCDA document", errors[0])

    def test_missing_sections_returns_error(self):
        tree = self._tree(MISSING_SECTIONS)
        errors = DDP.validate_ccda_document("test.xml", tree)
        self.assertEqual(len(errors), 1)
        self.assertIn("no structuredBody/component/section", errors[0])

    def test_error_includes_file_path(self):
        tree = self._tree(WRONG_ROOT)
        errors = DDP.validate_ccda_document("my_doc.xml", tree)
        self.assertIn("my_doc.xml", errors[0])

    def test_real_sample_file_passes(self):
        path = os.path.join(RESOURCES_DIR, 'bare-minimum_Results.xml')
        if not os.path.exists(path):
            self.skipTest("Sample file not found")
        tree = ET.parse(path)
        errors = DDP.validate_ccda_document(path, tree)
        self.assertEqual(errors, [], f"Real sample should pass validation: {errors}")


class TestParseDocXmlSyntaxError(unittest.TestCase):

    def test_malformed_xml_raises(self):
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False, mode='wb') as f:
            f.write(b"<not valid xml <<< >>>")
            tmp_path = f.name
        try:
            from ccda_to_omop.metadata import get_meta_dict
            meta = get_meta_dict()
            with self.assertRaises(ET.XMLSyntaxError):
                DDP.parse_doc(tmp_path, meta, '')
        finally:
            os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
