
import unittest


class TestFails(unittest.TestCase):
    def test_fails(self):
        self.assertTrue(False)

    def test_raises(self):
        raise Exception("failure test")    
