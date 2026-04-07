"""
Business logic constants for the CCDA-to-OMOP conversion pipeline.

Centralising these values makes them easier to find, understand, and change
without hunting through multiple modules.
"""

# ---------------------------------------------------------------------------
# Field / string handling
# ---------------------------------------------------------------------------

# Maximum length for any mapped string field before truncation.
MAX_FIELD_LENGTH = 50

# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

# HL7 compact date format length: YYYYMMDD
HL7_DATE_LENGTH = 8

# ISO 8601 date format length: YYYY-MM-DD
ISO_DATE_LENGTH = 10

# Time suffixes for building full ISO 8601 datetimes from date-only strings.
# LOW uses start-of-day; HIGH uses end-of-day.
DATETIME_LOW_SUFFIX = "T00:00:00.000Z"
DATETIME_HIGH_SUFFIX = "T23:59:59.000Z"

# ---------------------------------------------------------------------------
# Visit reconciliation
# ---------------------------------------------------------------------------

# Seconds in one day — used when converting timedelta to fractional days.
SECONDS_PER_DAY = 86400

# OMOP standard concept IDs that represent inpatient visit types.
# 9201 = "Inpatient Visit" in the Visit domain.
INPATIENT_CONCEPT_IDS = {
    9201   # Inpatient Visit
}

# Maximum duration (in days) for a valid inpatient parent visit.
# 367 gives a one-year ceiling with a small buffer for leap years.
MAX_PARENT_DURATION_DAYS = 367
