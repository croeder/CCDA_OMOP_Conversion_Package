# Unit tests are disabled by default. Please refer to the README.md for instructions on how to enable them.
# import pytest
from Chris_Project.utils import add_one

from Chris_Project.bar import baz

def test_baz():
    baz()
    
def test_add_one():
    assert add_one(1) == 2
