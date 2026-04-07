
import pandas as pd
import logging
import sys
import os

ALLOW_NO_MATCHING_CONCEPT=False


MIN_PYTHON = (3, 10)
if sys.version_info < MIN_PYTHON:
    sys.exit(f"Python version {MIN_PYTHON}  or later is required.")


# Library code should not configure logging. Per Python logging best practices,
# we attach a NullHandler so that log records are discarded unless the
# application configures a handler. Applications should call
# logging.basicConfig() (or equivalent) before using this package.
logging.getLogger(__name__).addHandler(logging.NullHandler())

# NOTE: The global dictionaries and their setters/getters
# have been moved to value_transformations.py
