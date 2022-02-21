from cgi import test
import glob
import json
import logging

from test_parser import TestsParser

logging_file = None
logging_level = logging.INFO

def get_files_to_list(path):
    all_files = []
    for file in glob.glob(path):
        all_files.append(file)
    return all_files

# create the next list from /tests/ path:
# [path1, path2, path3, ..., pathN]
# doing that by:
# stage 1: create list of all folders ['/tests/snmp', '/tests/snmp']
# stage 2: create a list of all the files in those paths, that means all the /tests/**/*.tdf
def create_basic_files_list(path):
    # stage 1
    folders = get_files_to_list(path)
    paths = []
    # stage 2
    for folder in folders:
        paths.extend(get_files_to_list(folder + '/*.tdf'))
    print(folders)
    print(paths)
    return paths


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

# gets {'dlep' : [path1,path2,...], 'snmp' : [path1,path2,...]}
# creates available_test_suites_json
# returns the created json
def create_available_test_suites_json(json_paths):
    test_suites = []
    for key, val in json_paths.items():
        test_suite = {}
        test_suite['Name'] = key
        print(val)
        test_suite['Tests Files'] = val

        #test_suite['Tests'].extend(paths)
        # insert() takes 2 arguments, so in order to insert to the end, we'll give position as the end of the list
        test_suites.insert(len(test_suites), test_suite)
    available_test_suites = {'ConfigType' : 'AvailableTestSuites', 'TestSuites' : test_suites}
    return available_test_suites
    

def parse_files(files):
    test_parser = TestsParser(logging_level)
    test_parser.parse_files(files)
    

def main():
    all_files = create_basic_files_list('/tests/*')
    test_parser = TestsParser(logging_level)
    test_parser.parse_files(all_files)
    # next line returns a dict of files which succeeded the parsing as {'dlep' : [path1,path2,...], 'snmp' : [path1,path2,...]}
    parsed_files_json = test_parser.get_test_files_after_parsing()
    print('parsed_files_json: {}'.format(parsed_files_json))
    available_test_suites = create_available_test_suites_json(parsed_files_json)
    print(available_test_suites)
    '''
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
    
    print(json_available_test_suites)
    '''
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

