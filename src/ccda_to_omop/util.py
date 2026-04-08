
from collections import defaultdict
import logging
from typeguard import typechecked
from dateutil.parser import parse
import csv
import datetime
import pandas as pd
from numpy import int32, int64

# Canonical type alias for a single OMOP output record dictionary.
# int32 is included because numpy vocabulary lookups return int32 concept IDs.
OMOPRecord = dict[str, None | str | float | int | int32 | int64 | datetime.datetime | datetime.date]

logger = logging.getLogger(__name__)
"""
    These three functions create dictionaries from the vocabulary xwalk
    pandas dataframes.
    Each dictionary, given vocabulary and code, provides each of
    source_concept_id, target_domain_id, or target_concept_id.
    It does this by returning a row-like dictionary with those field names
    as keys.
    The columns in the source datasets differ. Read carefully.
    Only the codemap provides the source_concept_id. The others just the two
    target fields.

    Each key may have more than one value.
    {
        (vocab, code) : [
            {   'source_concept_id': None,
                'target_domain_id': row['target_domain_id'],
                'target_concept_id': row['target_concept_id']
            }
        ]
    }
"""

def create_codemap_dict_from_csv(map_csv_filepath: str) -> dict:
    """ creates a dictionary (code_system, code) --> {source_concept_id: n, target_domain_id: m, target_concept_id: o}
        from a CSV file:
           OID, code, codeSystem, target_id, target_domain
    """
    concept_map = {}
    with open(map_csv_filepath) as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if len(row) < 5 or not row[0].strip():
                continue
            oid, code, _, concept_id, domain = [r.strip() for r in row[:5]]
            concept_map[(oid, code)] = {
                'source_concept_id': int(concept_id),
                'target_concept_id': int(concept_id),
                'target_domain_id': domain,
            }
    return concept_map


def create_codemap_dict(codemap_df: pd.DataFrame) -> dict:
    """ creates a dictionary (code_system, code) --> {source_concept_id: n, target_domain_id: m, target_concept_id: o}
        from a spark dataframe
    """
    logger.info(f"w xwalk create_codemap_dict {type(codemap_df)} {len(codemap_df)}")
    codemap_dict = defaultdict(list)
    for _, row in codemap_df.iterrows():
        code_system = row['src_vocab_code_system']
        if code_system is not None and isinstance(code_system, str):
            code_system = code_system.strip()
        code = row['src_code']
        if code is not None and isinstance(code_system, str):
            code = code.strip()
        codemap_dict[(code_system,  code)].append({
            'source_concept_id': row['source_concept_id'],  # dont' strip() integers
            'target_domain_id': row['target_domain_id'].strip(),
            'target_concept_id': row['target_concept_id']  # don't strip() integers
        })

    return codemap_dict




@typechecked
def cast_to_date(string_value: str) -> datetime.date | None:
    """Parse a date string and return a datetime.date.

    TODO: does CCDA always use YYYYMMDD?
    https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-USRealmDateTimeInterval-definitions.html
    doc says YYYYMMDD... examples show ISO-8601. Should use a regex and detect parse failure.
    TODO: when is it date and when datetime?
    """

    try:
        datetime_val = parse(string_value, ignoretz=True)
        return datetime_val.date()
    except Exception as x:
        logger.warning(f"ERROR couldn't parse {string_value} as date. Exception:{x}")
        return None


@typechecked
def cast_to_datetime(string_value: str) -> datetime.datetime | None:
    try:
        datetime_val = parse(string_value, ignoretz=True)
        return datetime_val
    except Exception as x:
        logger.warning(f"ERROR couldn't parse {string_value} as datetime. {x}")
        return None
        # return  datetime.date.fromisoformat("1970-01-01T00:00:00"
