from cgi import test
import glob
import json
import logging

from test_parser import TestsParser

logging_file = None
logging_level = logging.DEBUG

def get_files_to_list(path):
    all_files = []
    for file in glob.glob(path):
        all_files.append(file)
    return all_files

# takes all /tests/**/.tdf
def folder_read_to_json(path):
    available_test_suites = {'ConfigType' : 'AvailableTestSuites', 'TestSuites' : []}
    folders_list = get_files_to_list(path)
    test_suites = []
    for index, folder in enumerate(folders_list):
        test_suite = {}
        folder_name = str(folder[7:])
        test_suite['Name'] = folder_name
        test_suite['Tests'] = get_files_to_list(folder+'/*.tdf')
        # add test suite to test suites
        test_suites.insert(index, test_suite)

    available_test_suites['TestSuites'] = test_suites
    return json.dumps(available_test_suites)

def parse_files(files):
    test_parser = TestsParser(logging_level)
    test_parser.parse_files(files)
    

def main():
    # takes all the /tests/**/.tdf files
    json_available_test_suites = folder_read_to_json('/tests/*')
    print(json_available_test_suites)
    test_files_paths = []
    for test_suite in json_available_test_suites['TestSuites']:
        for test_file in test_suite['Tests']:
            test_files_paths.append(test_file)
    #parse_files(test_files_paths)
    test_parser = TestsParser(logging_level)
    test_parser.parse_files(test_files_paths)
    # next line returns a dict of files which succeeded the parsing as {'dlep' : [path1,path2,...], 'snmp' : [path1,path2,...]}
    parsed_files = test_parser.get_test_files_after_parsing()
    # remove all the non-exist files after parsing
    for inxed1, test_suite in enumerate(json_available_test_suites['TestSuites']):
        for index2, test_file in enumerate(json_available_test_suites[inxed1]['Tests']):
            if not test_file in parsed_files['dlep'] and not test_file in parsed_files['snmp']:
                del json_available_test_suites[inxed1]['Tests'][index2]
    print(json_available_test_suites)

    #parse_file('/tests/dlep/dlep-8703.tdf')



if __name__ == "__main__":
    main()

    '''{
	"_id": <random>,
	"ConfigType": "AvailableTestSuites",
	"TestSuites": [
		{
			"Name": "dlep",
			"Tests": [
				"dlep/dlep-8175.tdf",
				"dlep/dlep-8703.tdf",
			],
		},
		{
			"Name": "snmp",
			"Tests": [
				"snmp/battery-MIB.tdf",
				"snmp/network-MIB.tdf",
			]
		}
	]
}'''

