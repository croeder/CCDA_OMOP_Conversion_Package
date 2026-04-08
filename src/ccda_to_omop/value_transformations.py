import datetime
from typeguard import typechecked
from numpy import int32
from ccda_to_omop.util import cast_to_datetime
from ccda_to_omop import package_constant_access
from ccda_to_omop.constants import HL7_DATE_LENGTH, ISO_DATE_LENGTH, DATETIME_LOW_SUFFIX, DATETIME_HIGH_SUFFIX
import logging

"""
    Functions for use in DERVIED fields.
    The configuration for this type of field is:
        <new field name>: {
            'config_type': 'DERIVED',
            'FUNCTION': VT.<function_name>
            'argument_names': {
                <arg_name_1>: <field_name_1>
                ...
                <arg_name_n>: <field_name_n>
                'default': <default_value>
            }
        }
    The config links argument names to functions defined here to field names
    for the values. The code that calls these functions does the value lookup,
    so they operate on values, not field names or keys.
"""

logger = logging.getLogger(__name__)

class VocabContext:
    """Holds the vocabulary lookup maps used by transformation functions.

    A single module-level instance (_context) is used at runtime.  Tests can
    call reset() between cases to guarantee isolation without relying on
    import order or global keyword side-effects.

    Full dependency injection is not yet possible because transformation
    functions are referenced by name in metadata configs and are called with
    only args_dict.  This class is the first step: all mutable state lives
    here rather than as bare module globals, which eliminates the 'global'
    keyword and makes the state easy to inspect and reset.
    """

    def __init__(self):
        self.codemap_dict = None
        self.partner_map = None
        self.mspi_lookup_map = None


_context = VocabContext()


def reset_context():
    """Reset all vocab maps to None.  Call between test cases for isolation."""
    _context.__init__()


def set_codemap_dict(map: dict | None) -> None:
    if map is not None:
        logger.info(f"set_codemap_dict {len(map)}")
    else:
        logger.info("set_codemap_dict None map")
    _context.codemap_dict = map

def get_codemap_dict() -> dict | None:
    return _context.codemap_dict



def cast_as_string(args_dict: dict[str, any]) -> str | None:
    string_value = args_dict['input']
    type_value = args_dict['type']
    if type_value == 'ST':
        return str(string_value)
    else:
        return None


def cast_as_number(args_dict: dict[str, any]) -> int | None:
    string_value = args_dict['input']
    type_value = args_dict['type']
    if type_value == 'PQ':
        return int(string_value)
    else:
        return None


def cast_as_concept_id(args_dict: dict[str, any]) -> int32 | None:
    string_value = args_dict['input']
    type_value = args_dict['type']
    if type_value == 'CD' or type_value == 'CE':
        return int32(string_value)
    else:
        return None




############################################################################
"""
    table: codemap_xwalk
    functions: codemap_xwalk...
"""

def codemap_xwalk_concept_id(args_dict: dict[str, any]) -> int32 | None:
    """ expects: vocabulary_oid, concept_code
        returns: concept_id AS INTEGER (because that's what's in the table), not necessarily standard
                 If NMC is disallowed, it will return None instead of 0.
                 Control this via set_allow_no_macthing_concept() in package_constant_access.
        throws/raises when codemap_xwalk is None
    """

    id_value = _codemap_xwalk(args_dict['vocabulary_oid'], args_dict['concept_code'],
                'target_concept_id', args_dict.get('default'))

    if id_value is not None and (id_value != 0 or package_constant_access.get_allow_no_matching_concept()):
        logger.debug(f"codemap_xwalk_concept_id concept_id is {id_value}  for {args_dict}")
        return int32(id_value)
    else:
        logger.warning(f"codemap_xwalk_concept_id concept_id is None  for {args_dict}")
        return None


def codemap_xwalk_domain_id(args_dict: dict[str, any]) -> str | None:
    """ expects: vocabulary_oid, concept_code
        returns: always returns domain_id
        throws/raises when codemap_xwalk is None
    """
    id_value = _codemap_xwalk(args_dict['vocabulary_oid'], args_dict['concept_code'],
                'target_domain_id', args_dict.get('default'))

    if id_value is not None:
        return str(id_value)
    else:
        return None


def codemap_xwalk_source_concept_id(args_dict: dict[str, any]) -> int32 | None:
    """ expects: vocabulary_oid, concept_code
        returns: unmapped concept_id AS INTEGER (because that's what's in the table), not necessarily standard
        throws/raises when codemap_xwalk is None
    """
    id_value =  _codemap_xwalk(args_dict['vocabulary_oid'], args_dict['concept_code'],
                'source_concept_id', args_dict.get('default'))

    if id_value is not None and (id_value != 0 or package_constant_access.get_allow_no_matching_concept()):
        return int32(id_value)
    else:
        return None


def _codemap_xwalk(vocabulary_oid, concept_code, column_name, default):

    if get_codemap_dict() is None:
        logger.error("codemap_dict is not initialized in ccda_to_omop/value_transformations.py for value_transformations.py")
        raise Exception("codemap_dict is not initialized in ccda_to_omop/value_transformations.py for value_transformations.py")
    codemap_xwalk_mapping_dict= get_codemap_dict()

    if (vocabulary_oid, concept_code) in codemap_xwalk_mapping_dict:
        mapping_rows = codemap_xwalk_mapping_dict[(vocabulary_oid, concept_code)]
    else:
        logger.warning(f"value_transformations.py _codemap_xwalk vocabulary_id:\"{vocabulary_oid}\" ,{type(vocabulary_oid)}, code:\"{concept_code}\", {type(concept_code)}  not present or not found")
        return default

    if mapping_rows is None:
        logger.warning(f"codemap_dict mapping_rows is None  for vocab:{vocabulary_oid} code:{concept_code} column_name:{column_name} default:{default}")
        return default

    if len(mapping_rows) < 1:
        logger.warning(f"codemap_dict mapping_rows is <1 for vocab:{vocabulary_oid} code:{concept_code} column_name:{column_name} default:{default}")
        return default

    if len(mapping_rows) > 1:
        logger.warning(f"_codemap_xwalk(): more than one  concept for  \"{column_name}\" from  \"{vocabulary_oid}\" \"{concept_code}\", chose the first")

    column_value = None
    if column_name in mapping_rows[0]:
        column_value = mapping_rows[0][column_name]
    else:
        logger.error(f"value_transformations.py _codemap_xwalk doens't have the column{column_name}....{mapping_rows[0]}")
        logger.error("f (cont) {mapping_rows}")

    # if NMC is disallowed, and there is a default specified, return the default
    if column_value is not None and column_value == 0 and not package_constant_access.get_allow_no_matching_concept():
        return default

    return column_value


############################################################################

def visit_xwalk_concept_id(args_dict: dict[str, any]) -> int32 | None:
    return codemap_xwalk_concept_id(args_dict)

def visit_xwalk_domain_id(args_dict: dict[str, any]) -> str | None:
    return codemap_xwalk_domain_id(args_dict)

def visit_xwalk_source_concept_id(args_dict: dict[str, any]) -> int32 | None:
    return codemap_xwalk_source_concept_id(args_dict)

def _visit_xwalk(vocabulary_oid, concept_code, column_name, default):
    return _codemap_xwalk(vocabulary_oid, concept_code, column_name, default)

############################################################################

def valueset_xwalk_concept_id(args_dict: dict[str, any]) -> int32 | None:
    return codemap_xwalk_concept_id(args_dict)

def valueset_xwalk_domain_id(args_dict: dict[str, any]) -> str | None:
    return codemap_xwalk_domain_id(args_dict)

def valueset_xwalk_source_concept_id(args_dict: dict[str, any]) -> int32 | None:
    return codemap_xwalk_source_concept_id(args_dict)

def _valueset_xwalk(vocabulary_oid, concept_code, column_name, default=None):
    return _codemap_xwalk(vocabulary_oid, concept_code, column_name, default)

############################################################################


@typechecked
def extract_day_of_birth(args_dict : dict[str, any]) -> int32:
    # assumes input is a datetime
    date_object = args_dict['date_object']
    if date_object is not None:
        return int32(date_object.day)
    return None


@typechecked
def extract_month_of_birth(args_dict : dict[str, any]) -> int32:
    # assumes input is a datetime
    date_object = args_dict['date_object']
    if date_object is not None:
        return int32(date_object.month)
    return None


@typechecked
def extract_year_of_birth(args_dict : dict[str, any]) -> int32:
    # assumes input is a datetime
    date_object = args_dict['date_object']
    if date_object is not None:
        return int32(date_object.year)
    return None


def concat_field_list_names(args_dict: dict[str, any], data_dict: dict[str, any]) -> str:
    '''
        A DERIVED2 style function.
        Looks for a argument with the name of 'args' under the 'argument_list'
        brought in from the parse configuration. That list is a list of keys
        whose data we're interested in fetching from the data_dict.

        args_dict: the field's paragraph in the parse configuration
        data_dict: the dictionary of values being built up for an OMOP row
           by the parse configuration where all this comes from.

        Returns: a joined list of the keys. The data_dict is unused.
    '''
    args_key = 'argument_list'
    if not args_dict:
        return f"no args dict \"{args_dict}\" "
    if args_key not in args_dict.keys():
        return f"no  \"{args_key}\" in args dict {args_dict}"
    if 'key_list' not in args_dict['argument_list'].keys():
        return f"no  \"key_list\" in args dict {args_dict}"

    return  "|".join(args_dict['argument_list']['key_list'])


def concat_field_list_values(args_dict: dict[str, any], data_dict: dict[str, any]) -> str:
    '''
        A DERIVED2 style function.
        Looks for a argument with the name of 'args' under the 'argument_list'
        brought in from the parse configuration. That list is a list of keys
        whose data we're interested in fetching from the data_dict.

        args_dict: the field's paragraph in the parse configuration
        data_dict: the dictionary of values being built up for an OMOP row
           by the parse configuration where all this comes from.

        Returns: a joined list of the data values associated with those keys.
    '''
    if not args_dict:
        return f"no args dict \"{args_dict}\" "
    if 'argument_list' not in args_dict.keys():
        return f"no  argument_list in args dict {args_dict}"
    if 'key_list' not in args_dict['argument_list'].keys():
        return f"no  \"key_list\" in args dict {args_dict}"

    return "|".join(map(str, map(lambda x: data_dict[x], args_dict['argument_list']['key_list'] )))




def concat_fields(args_dict: dict[str, any]) -> str:
    """
      A DERIVED style function.
      input key "delimiter" is a character to use to separate the fields
      following items in dict are the names of keys in the values to concat

      returns one string, the concatenation of values corresponding to args 2-n, using arg 1 as a delimieter
    """
    delimiter = '|'


    if (args_dict['first_field'] is None) and (args_dict['second_field'] is None):
        return ''
    elif (args_dict['first_field'] is None) and (args_dict['second_field'] is not None):
        return args_dict['second_field']
    elif (args_dict['first_field'] is not None) and (args_dict['second_field'] is None):
        return args_dict['first_field']
    else :
        values_to_concat = [ args_dict['first_field'], args_dict['second_field'] ]
        return delimiter.join(values_to_concat)

####################################################################################################

def set_partner_map(m: dict | None) -> None:
    """Initializes the partner map on the executor."""
    _context.partner_map = m

def get_partner_map() -> dict | None:
    return _context.partner_map

def get_data_partner_id(args_dict: dict[str, any]) -> int32:
    """
    Returns Data Partner ID. Defaults to 0 if filename is not in map.
    Strictly returns an integer per the component contract.
    """
    fname = args_dict.get('filename')
    mapping = get_partner_map()
    if mapping is None:
        raise ValueError("Data partner id map is missing")
    # We don't catch errors here; if mapping[fname] is garbage,
    # int32() will raise an error 'loudly' as requested.
    return int32(mapping.get(fname, 0))


def set_mspi_map(m: dict | None) -> None:
    """Initializes the MSPI (person_id) map on the executor."""
    _context.mspi_lookup_map = m

def get_mspi_map() -> dict | None:
    return _context.mspi_lookup_map

def map_filename_to_mspi(args_dict: dict[str, any]) -> int:
    """
    Returns MSPI (person_id). Defaults to 0 if filename is not in map.
    Raises if the MSPI map has not been initialized.
    """
    fname = args_dict.get('filename')
    mapping = get_mspi_map()
    if mapping is None:
        raise ValueError("MSPI map is missing")
    # If filename is missing, returns 0.
    # If value exists but isn't an integer, int() will raise a ValueError.
    return int(mapping.get(fname, 0))


@typechecked
def transform_datetime_low(args) -> datetime.datetime | None:
    """
    Transforms a date-only string into a full ISO 8601 datetime defaulting to 00:00:00.

    This function assumes the input is either in ISO 8601 (YYYY-MM-DD) or HL7 (YYYYMMDD)
    format. We can make this assumption because this transformation is typically
    called after 'parseutils.parser' has already standardized the raw input.
    """
    val = args.get('input_value')
    if not val:
        return args.get('default')

    val_str = str(val).strip()
    # HL7 format (YYYYMMDD)
    if len(val_str) == HL7_DATE_LENGTH and val_str.isdigit():
        return cast_to_datetime(f"{val_str[:4]}-{val_str[4:6]}-{val_str[6:]}{DATETIME_LOW_SUFFIX}")
    # ISO 8601 format (YYYY-MM-DD)
    if len(val_str) == ISO_DATE_LENGTH and '-' in val_str:
        return cast_to_datetime(f"{val_str}{DATETIME_LOW_SUFFIX}")

    return cast_to_datetime(val_str)

@typechecked
def transform_datetime_high(args) -> datetime.datetime | None:
    """
    Transforms a date-only string into a full ISO 8601 datetime defaulting to 23:59:59.

    This function assumes the input is either in ISO 8601 (YYYY-MM-DD) or HL7 (YYYYMMDD)
    format. We can make this assumption because this transformation is typically
    called after 'parseutils.parser' has already standardized the raw input.
    """
    val = args.get('input_value')
    if not val:
        return args.get('default')

    val_str = str(val).strip()
    # HL7 format (YYYYMMDD)
    if len(val_str) == HL7_DATE_LENGTH and val_str.isdigit():
        return cast_to_datetime(f"{val_str[:4]}-{val_str[4:6]}-{val_str[6:]}{DATETIME_HIGH_SUFFIX}")
    # ISO 8601 format (YYYY-MM-DD)
    if len(val_str) == ISO_DATE_LENGTH and '-' in val_str:
        return cast_to_datetime(f"{val_str}{DATETIME_HIGH_SUFFIX}")

    return cast_to_datetime(val_str)
