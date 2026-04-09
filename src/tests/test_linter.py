
import unittest
import logging
from lxml import etree as ET
import ccda_to_omop.metadata as MD
from ccda_to_omop.domain_dataframe_column_types import domain_dataframe_column_types
from ccda_to_omop.ddl import domain_name_to_table_name

# Namespace map used in all CCDA XPath expressions
NS = {
    'hl7': 'urn:hl7-org:v3',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'sdtc': 'urn:hl7-org:sdtc',
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)



class Linter(unittest.TestCase):
    """ This unit test checks for errors in the parse configurations.
        It tests each field independently for required parameters and makes
        sure there are no stray extras that slipped in.

        It tests for linkages beteween fields, making sure that DERIVED, DERIVED2, 
        HASH and PRIORITY types are making reference to fields that are defined.

        The structure here is a bit unusual for typical unit tests because 
        the top-level tests are created dynamicaly from the config dictionary.
        At the bottom of this file is a loop that defines a function _test_method
        once for each config. The setattr call renames it with the name of the configuration.

        Then within each such function, a number of tests are called, including 
        check_parameters_by_field_type that runs through each field within a parse config.

        Be sure and check the stdout when diagnosing failures.
    """

    # FIELD LEVEL functions used by check_parameters_by_field_type()
    def required_params(self, field_config, required_params):
        all_good=True
        for fname in required_params:
            if fname not in field_config.keys() :
                print(f'ERROR: missing requried field {fname} in {field_config}')
                print(f"    {field_config}")
                all_good=False
        self.assertTrue(all_good) 
    

    def no_stray_params(self, field_config, required_params, optional_params):
        all_good=True
        ok_params = set(optional_params).union(set(required_params))
        all_params = set(field_config.keys())
        stray_params = all_params.difference(ok_params)
        if len(stray_params) > 0:
            all_good=False
            print(f"ERROR: stray field {stray_params} in {field_config}")
        self.assertEqual(len(stray_params), 0)


    def _test_FIELD(self, config_dict, field_config):  # good
        required_params=['config_type', 'element', 'attribute']
        optional_params=['data_type', 'order', 'priority']
        self.required_params(field_config, required_params)
        self.no_stray_params(field_config, required_params, optional_params)

        legit_data_types = ['DATE', 'DATETIME', 'DATETIME_HIGH', 'DATETIME_LOW', 'LONG', 'INTEGER', 'BIGINTHASH', 'TEXT', 'FLOAT']
        if 'data_type' in field_config.keys():
            if field_config['data_type'] not in legit_data_types:
                print(f"ERROR: \"{field_config['data_type']}\" is not a legit data_type value." )
                print(f"    {field_config}" )
            self.assertTrue(field_config['data_type'] in legit_data_types)

    
    def _test_NONE(self, config_dict, field_config): # good
        required_params=['config_type', ]
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority']
        self.no_stray_params(field_config, required_params, optional_params)


    def _test_DERIVED(self, config_dict, field_config): # good
        required_params = ['config_type', 'FUNCTION', 'argument_names']
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority', 'length']
        self.no_stray_params(field_config, required_params, optional_params)
        # confirm the arguments of the argument names, the values in that dict are also field names
        # But, we can't distinguish  arguments that take field names from those that take
        # constants, so we add some common constants here.
        legit_args = list(config_dict.keys())
        for arg_name, arg_val in field_config['argument_names'].items():
            if arg_name != 'default' and arg_val not in legit_args:
                #print(f"ERROR: argument \"{arg_name}\" value \"{arg_val}\"  in this config")
                logger.error(f"ERROR: argument \"{arg_name}\" value \"{arg_val}\"  in this config {config_dict['cfg_name']['constant_value']}")
                self.assertTrue(arg_val in legit_args)

        # Check default values. Should just remove them outright
        legit_defaults = [0, -1, None] 
        if 'default' in field_config['argument_names'].keys():
            default_value = field_config['argument_names']['default']
            if default_value not in legit_defaults:
                print(f"Warning: \"{default_value}\" is a dubious default value ")

        function_args_dict = {
             'codemap_xwalk_concept_id': ['vocabulary_oid', 'concept_code', 'default'],
             'codemap_xwalk_domain_id': ['vocabulary_oid', 'concept_code', 'default'],
             'codemap_xwalk_source_concept_id': ['vocabulary_oid', 'concept_code', 'default'],
             'concat_field_list_names': ['argument_list'], # then key_list
             'concat_field_list_values': [ 'argument_list'] ,# then key_list
             'concat_fields': ['first_field', 'second_field' ] ,
             'extract_day_of_birth': ['date_object' ],
             'extract_month_of_birth': ['date_ojbect' ],
             'extract_year_of_birth' : ['date_object' ],
             'valueset_xwalk_concept_id': ['vocabulary_oid', 'concept_code', 'default' ], 
             'visit_xwalk_concept_id': ['vocabulary_oid', 'concept_code', 'default' ], 
             'visit_xwalk_domain_id': ['vocabulary_oid', 'concept_code', 'default' ], 
             'visit_xwalk_source_concept_id': ['vocabulary_oid', 'concept_code', 'default' ], 
             'get_data_partner_id': ['filename'],
             'map_filename_to_mspi': ['filename']
        }
        available_field_names = config_dict.keys()
        function_name = field_config['FUNCTION'].__name__
        for required_arg in function_args_dict[function_name]:
            present_arg_dict = field_config['argument_names']
            present_args = present_arg_dict.keys()
            if required_arg not in present_args:
                print(f"ERROR: argument {required_arg} missing for function {function_name}")
            else:
                if present_arg_dict[required_arg]  not in available_field_names and required_arg != 'default':
                    print(f"ERROR {required_arg} missing from available_field_names")
                    self.assertTrue(present_arg_dict[required_arg] in available_field_names and required_arg != 'default')
                #else:
                #    print(f"  debug {required_arg} IS IN there ")


    def _test_DERIVED2(self, config_dict, field_config): # good
        required_params=['config_type', 'FUNCTION', 'argument_list']
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority']
        self.no_stray_params(field_config, required_params, optional_params)
        # TODO/CANT DO hard to test for the right arguments becuase it's in the function being called
        # However, the argument_list (why?) must have a key_list, whose values are fields
        if 'key_list' in field_config['argument_list']:
            for field_name in field_config['argument_list']['key_list']:
                if field_name not in config_dict.keys():
                    print(f"ERROR: {field_name} not found in key_list of argument_list of {field_config}" )
                    self.assertTrue(field_name in config_dict.keys())
                #else:
                #    print(f"OK {field_name}  found in key_list of argument_list " )
        else:
            print(f"ERROR: 'key_list' missing in argument_list of DERIVED2 field {field_config}")
            self.assertTrue('key_list' in field_config['argument_list'])
        # TODO: Check that arguments required by a function are present


    #def _test_MAPPED(self, config_dict, field_config): in branch CR_651
    #    required_params=['config_type', 'config_type', 'config_type', ]
    #    self.required_params(field_config, required_params)
    #    optional_params=['order', 'priority']
    #    self.no_stray_params(field_config, required_params, optional_params)
        # TODO: Check that arguments required by a function are present


    def _test_PK(self, config_dict, field_config): # not used, they are all hashes now
        required_params=['config_type', ]
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority']
        self.no_stray_params(field_config, required_params, optional_params)


    def _test_FK(self, config_dict, field_config): # good
        required_params = ['config_type', 'FK']
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority']
        self.no_stray_params(field_config, required_params, optional_params)
        # X Check that the field has a matching configured PK or HASH
        # That's a run-time thing. This field must be in the pk_dict when processing
        # in data_driven_parse. It can't happen here.


    def _test_HASH(self, config_dict, field_config): # good
        required_params = ['config_type', 'fields']
        self.required_params(field_config, required_params)
        # TODO confirm each field is in the hash
        optional_params=['order', 'priority']
        self.no_stray_params(field_config, required_params, optional_params)

        legit_args = list(config_dict.keys())
        for arg_val in field_config['fields']:
            if arg_val not in legit_args:
                print(f"ERROR: field {arg_val} is not present in this config")
                self.assertTrue(arg_val in legit_args)


    def _test_ROOT(self, config_dict, field_config): # good
        required_params = ['config_type', 'element', 'expected_domain_id']
        self.required_params(field_config, required_params)
        optional_params=[] # probably not ['order', 'priority']
        self.no_stray_params(field_config, required_params, optional_params)


    # vestigal field that should just be a DERIVED field type
    def _test_DOMAIN(self, config_dict, field_config):
        required_params=['config_type', ]
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority']
        self.no_stray_params(field_config, required_params, optional_params)
        print(f"ERROR: deprecated domain field in {field_config}, use DERIVED")
        self.assertTrue(False)


    def _test_PRIORITY(self, config_dict, field_config):
        required_params=['config_type']
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority'] 
        self.no_stray_params(field_config, required_params, optional_params)
        # TODO check that the fields referred to exist, has to happen more globaly elsewhere


    def _test_FILENAME(self, config_dict, field_config): # good
        required_params=['config_type' ]
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority']
        self.no_stray_params(field_config, required_params, optional_params)


    def _test_CONSTANT(self, config_dict, field_config): # good
        required_params = ['config_type', 'constant_value']
        self.required_params(field_config, required_params)
        optional_params=['order', 'priority', 'length']
        self.no_stray_params(field_config, required_params, optional_params)
        # fields that are '', 'n/a', 'None' or even None could be bad news
        bad_news = ['', 'n/a', 'None', None, 0, -1]
        if field_config['constant_value'] in bad_news:
            print(f"Warning: CONSTANT field has dubious value \"{field_config['constant_value']}\"")
            #self.assertTrue(field_config['constant_value'] not in bad_news)


    # CONFIG level checks
    def check_xpath_syntax(self, config, config_name):
        """Validate XPath syntax on all element fields using lxml.etree.XPath()."""
        for field_name, field_config in config.items():
            config_type = field_config.get('config_type')
            if config_type in ('FIELD', 'PK', 'ROOT') and 'element' in field_config:
                xpath_expr = field_config['element']
                try:
                    ET.XPath(xpath_expr, namespaces=NS)
                except ET.XPathSyntaxError as e:
                    print(f"ERROR: invalid XPath in {config_name}/{field_name}: {xpath_expr!r} — {e}")
                    self.fail(f"XPath syntax error in {config_name}/{field_name}: {e}")


    def check_circular_dependencies(self, config, config_name):
        """Detect circular dependencies in DERIVED and FK field references."""
        # Build adjacency: field -> set of fields it depends on
        deps = {}
        for field_name, field_config in config.items():
            config_type = field_config.get('config_type')
            if config_type == 'DERIVED':
                deps[field_name] = set(
                    v for k, v in field_config.get('argument_names', {}).items()
                    if k != 'default' and v in config
                )
            elif config_type == 'FK':
                # FK targets reference the pk_dict (populated by another config),
                # not a field in this config — skip to avoid false self-loop positives.
                deps[field_name] = set()
            elif config_type == 'HASH':
                deps[field_name] = set(
                    f for f in field_config.get('fields', []) if f in config
                )
            else:
                deps[field_name] = set()

        # DFS cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {f: WHITE for f in deps}

        def dfs(node, path):
            color[node] = GRAY
            for neighbor in deps.get(node, set()):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    cycle = ' -> '.join(path + [neighbor])
                    print(f"ERROR: circular dependency in {config_name}: {cycle}")
                    self.fail(f"Circular dependency in {config_name}: {cycle}")
                elif color[neighbor] == WHITE:
                    dfs(neighbor, path + [neighbor])
            color[node] = BLACK

        for field_name in list(deps.keys()):
            if color[field_name] == WHITE:
                dfs(field_name, [field_name])


    def check_parameters_by_field_type(self, config, config_name):
        """Check each field in a config, branch out by field type"""
        for field_name in config.keys():
            if 'config_type' not in config[field_name]:
                print(f"ERROR: config {config_name} has no config_type key: {config[field_name]} ")
                self.assertTrue('config_type'  in config[field_name])
            config_type = config[field_name]['config_type']
            #print(f"    field:{field_name}  type:{config_type}")
            match config_type:
                case 'CONSTANT':
                    self._test_CONSTANT(config, config[field_name])
                case 'FILENAME':
                    self._test_FILENAME(config, config[field_name])
                case 'PRIORITY':
                    self._test_PRIORITY(config, config[field_name])
                case 'DOMAIN':
                    self._test_DOMAIN(config, config[field_name])
                case 'ROOT':
                    self._test_ROOT(config, config[field_name])
                case 'HASH':
                    self._test_HASH(config, config[field_name])
                case 'FK':
                    self._test_FK(config, config[field_name])
                case 'PK':
                    self._test_PK(config, config[field_name])
                #case 'MAPPED':
                #    self._test_MAPPED(config, config[field_name])
                case 'DERIVED':
                    self._test_DERIVED(config, config[field_name])
                case 'DERIVED2':
                    self._test_DERIVED2(config, config[field_name])
                case 'NONE':
                    self._test_NONE(config, config[field_name])
                case 'FIELD':
                    self._test_FIELD(config, config[field_name])


    def check_priority_chains(self, config, config_name):
        """ Checks to make sure there is a priority field that goes with the param
            here that sys the field in question is part of the named priority chain. 
        """
        priority_fields = [ field_name for field_name, field_config in config.items() if field_config['config_type'] == 'PRIORITY'  ]
        for p_field_name in priority_fields:
            has_at_least_one = False
            for field_name in config.keys():
                field_config = config[field_name]
                if 'priority' in field_config.keys():
                    if field_config['priority'][0] == p_field_name:
                        has_at_least_one = True
            if not has_at_least_one:
                print(f"ERROR: priority field {p_field_name} does not have at least one participating field in {config_name}")
            #else:
            #    print(f"DEBUG: priority field {p_field_name} DOES have at least one participating field in {config_name}")
            self.assertTrue(has_at_least_one)


    def check_for_domain_id(self, config_name):
        """ Checks to see that the config has a domain_id field.
            Particulars of the field depending on type are checked elsewhere.
            This just makes sure a domain_id field is present.
        """
        meta_dict = MD.get_meta_dict()
        config_dict = meta_dict[config_name]
        if config_name not in meta_dict:
            print(f"ERROR:  {config_name} not available")
            self.assertTrue(False)

        domainless_domains = ['Care_Site', 'Location', 'Person', 'Provider'] 
        if 'expected_domain_id' not in config_dict['root']:
            print(f'ERROR:  the root part of {config_name} is missing an expected_domain_id field.')
            self.assertTrue(False)
        if 'domain_id' not in config_dict and config_dict['root']['expected_domain_id'] not in domainless_domains:
            print(f'ERROR:  {config_name} is missing a domain_id field.')
            self.assertTrue('domain_id' in config_dict)



    def check_required_fields(self, config_dict, config_name):
        """ For a given config's domain, this checks that the list of 
            fields specified in a config is the same as the list of
            fileds in OMOP
        """
        #domain_name = config_dict[config_name]['root']['expected_domain_id']

        domain_name = config_dict['root']['expected_domain_id']
        table_name= domain_name_to_table_name[domain_name]
        required_config_fields_set = set(domain_dataframe_column_types[table_name])
        present_config_fields_set = {k for k in config_dict.keys() if 'order' in config_dict[k]}

        intersection = required_config_fields_set.intersection(present_config_fields_set)
        if len(present_config_fields_set) != len(intersection):
            logger.error(f"{config_name} missing fields: {required_config_fields_set - present_config_fields_set}")
            logger.error(f"{config_name} extra fields: {present_config_fields_set - required_config_fields_set}")
        self.assertEqual(len(present_config_fields_set), len(intersection))
    
       

# These fail as a way of testing this testing code
# Include by uncommented a line below where this is added to metadata.
more_metadata = {
    'TESTCASE_1': {
        'root': {
           'config_type':'ROOT',
           # missing expected_domain_id
           # messing element 
        },
        'A': {
            'config_type': 'FIELD',
            # missing 'element'
            # missing 'attribute'
        },
        'B': {
            'config_type': 'DERIVED',
            'FUNCTION': None,
            'argument_names': {
                'x': 'A',
                'y': 'Z' # which doesn't exist
            },
            'priority':'does not exist'
        },
        'domain': { }
    },
    'TESTCASE_2': {
        'root': {
           'config_type':'ROOT',
           # missing expected_domain_id
           # messing element 
        },
        'A': {
            'config_type': 'FIELD',
            # missing 'element'
            # missing 'attribute'
        },
        'B': {
            'config_type': 'DERIVED',
            'FUNCTION': None,
            'argument_names': {
                'x': 'A',
                'y': 'Z' # which doesn't exist
            },
            'priority':'does not exist'
        },
        'domain': { }
    }
}

meta_dict = MD.get_meta_dict()
# ### meta_dict = meta_dict | more_metadata

# The tests you see when you run normally come from functions in the
# test class. They are created dynamically here for each configuration
# dict in the meta_dict.
# Trick found via google, no SO page to cite though.
# Try google with this question: 
# "In python unittest can I dynamically create tests, or do they each need their own function?"
for config_name in  meta_dict.keys():
    # redefines the _test_method for each config name, with a different default argumetn
    # python-man's currying?
    if config_name != 'VISITDETAIL_visit_occurrence':
        def _test_method(self, config_name=config_name):
            config_dict = meta_dict[config_name]
            print(f"\ntesting {config_name}")
            self.check_for_domain_id(config_name)
            self.check_priority_chains(config_dict, config_name)
            self.check_parameters_by_field_type(config_dict, config_name)
            self.check_xpath_syntax(config_dict, config_name)
            self.check_circular_dependencies(config_dict, config_name)
            self.check_required_fields(config_dict, config_name)
        # changes the name of the _test_method just created, effectively creating a new function.
        setattr(Linter, f"test_{config_name}", _test_method)
    

    
