
import prototype_2.value_transformations as VT
import prototype_2.data_driven_parse as DDP
from lxml import etree as ET


def test_simple_field():
    ns = {
        # '': 'urn:hl7-org:v3',  # default namespace
        'hl7': 'urn:hl7-org:v3',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'sdtc': 'urn:hl7-org:sdtc'
    }

    XML_text="""
        <grouping_element>
            <simple_element>
                <value value="simple text" />
            </simple_element>
        </grouping_element>
    """

    output_dict = {}
    config_name="TEST"
    #root_path="./grouping_element/simple_element" 
    root_path="./simple_element" 

    try:
        tree=ET.fromstring(XML_text)
        root_element_list = tree.xpath(root_path, namespaces=ns)

        config_dict = {
            'text_field': { 
                'config_type': 'FIELD',
                'element': 'value',
                'attribute': 'value',
                'order': 202
            },
        }

        error_fields_set = set()
        pk_dict={}
        print(f"\nstarting simple {len(root_element_list)}")
        for root_element in root_element_list:
            DDP.do_basic_fields(output_dict, root_element, root_path, config_name, config_dict, error_fields_set, pk_dict)
            print(f"dict: {output_dict}")
            assert output_dict['text_field'] == 'simple text'
        print("done")
    except Exception as e:
        print(e)
        assert False
        raise e

def test_simple_field_that_needs_stripped():
    ns = {
        # '': 'urn:hl7-org:v3',  # default namespace
        'hl7': 'urn:hl7-org:v3',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'sdtc': 'urn:hl7-org:sdtc'
    }

    XML_text="""
        <grouping_element>
            <simple_element>
                <value value=" simple text " />
            </simple_element>
        </grouping_element>
    """

    output_dict = {}
    config_name="TEST"
    root_path="./simple_element" 

    try:
        tree=ET.fromstring(XML_text)
        root_element_list = tree.xpath(root_path, namespaces=ns)

        config_dict = {
            'text_field': { 
                'config_type': 'FIELD',
                'element': 'value',
                'attribute': 'value',
                'order': 202
            },
        }

        error_fields_set = set()
        pk_dict={}
        print(f"\nstarting simple {len(root_element_list)}")
        for root_element in root_element_list:
            DDP.do_basic_fields(output_dict, root_element, root_path, config_name, config_dict, error_fields_set, pk_dict)
            print(f"dict: {output_dict}")
            assert output_dict['text_field'] == 'simple text'
        print("done")
    except Exception as e:
        print(e)
        assert False
        raise 

def test_code_field():
    ns = {
        # '': 'urn:hl7-org:v3',  # default namespace
        'hl7': 'urn:hl7-org:v3',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'sdtc': 'urn:hl7-org:sdtc'
    }
                #<hl7:value[@xsi:type="CE"] code="123" />
    XML_text="""
        <grouping_element>
            <code_element>
                <value type="CE" code="123" />
            </code_element>
        </grouping_element>
    """

    output_dict = {}
    config_name="TEST"
    root_path="code_element" 

    try:
        tree=ET.fromstring(XML_text)
        root_element_list = tree.xpath(root_path, namespaces=ns)

        config_dict = {
            'text_field': { 
                'config_type': 'FIELD',
                'element': 'value',
                #'attribute': 'hl7:value',
                #'attribute': 'hl7:value[@type="CE"]',
                'attribute': 'code',
                'order': 202
            },
        }

        error_fields_set = set()
        pk_dict={}
        print(f"\nstarting code {len(root_element_list)}")
        for root_element in root_element_list:
            DDP.do_basic_fields(output_dict, root_element, root_path, config_name, config_dict, error_fields_set, pk_dict)
            print(f"dict: {output_dict}")
            assert output_dict['text_field'] == '123'
        print("done")

    except Exception as e:
        print(e)
        assert False

        
def test_text_field():
    ns = {
        # '': 'urn:hl7-org:v3',  # default namespace
        'hl7': 'urn:hl7-org:v3',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'sdtc': 'urn:hl7-org:sdtc'
    }

    XML_text="""
        <grouping_element>
            <text_element>
                <value>multi-line
                       element</value>
            </text_element>
        </grouping_element>
    """
    the_text="""multi-line
                       element"""

    output_dict = {}
    config_name="TEST"
    root_path="text_element" 

    try:
        tree=ET.fromstring(XML_text)
        root_element_list = tree.xpath(root_path, namespaces=ns)

        config_dict = {
            'text_field': { 
                'config_type': 'FIELD',
                'element': 'value',
                'attribute': '#text',
                'order': 202
            },
        }

        error_fields_set = set()
        pk_dict={}
        print(f"\nstarting text {len(root_element_list)}")
        for root_element in root_element_list:
            DDP.do_basic_fields(output_dict, root_element, root_path, config_name, config_dict, error_fields_set, pk_dict)
            print(f"dict: {output_dict}")
            assert output_dict['text_field'] == the_text
        print('done')

    except Exception as e:
        print(e)
        assert False
        raise e



def test_quant_field():
    ns = {
        # '': 'urn:hl7-org:v3',  # default namespace
        'hl7': 'urn:hl7-org:v3',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'sdtc': 'urn:hl7-org:sdtc'
    }
                # <hl7:value xsi:type="PQ" value="93" />
    XML_text="""
        <grouping_element>
            <quantity_element>
                <value type="PQ" value="93" />
            </quantity_element>
        </grouping_element>
    """

    output_dict = {}
    config_name="TEST"
    root_path="quantity_element" 

    try:
        tree=ET.fromstring(XML_text)
        root_element_list = tree.xpath(root_path, namespaces=ns)

                # 'element': 'hl7:value',
        config_dict = {
            'text_field': { 
                'config_type': 'FIELD',
                'element': 'value',
                'attribute': 'value',
                'order': 202
            },
        }

        error_fields_set = set()
        pk_dict={}
        print(f"\nstarting quant {len(root_element_list)}")
        for root_element in root_element_list:
            DDP.do_basic_fields(output_dict, root_element, root_path, config_name, config_dict, error_fields_set, pk_dict)
            print(f"dict: {output_dict}")
            assert output_dict['text_field'] == '93'
        print("done")

    except Exception as e:
        print(e)
        assert False
        raise e
        

 