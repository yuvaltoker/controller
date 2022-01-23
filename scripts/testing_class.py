import glob
import json

def get_files_to_list(path):
    all_files = []
    for file in glob.glob(path):
        all_files.append(file)
    return all_files

def main():
    path_of_tests = '/tests/snmp/*'
    files_list = []
    files_list = files_list + get_files_to_list(path_of_tests)
    if '/tests/dlep' in files_list:
        files_list.remove('/tests/dlep')
    print(files_list)

# suppose to take all /tests/**/.tdf
def folder_read_to_json(path):
    available_test_suites = {'ConfigType' : 'AvailableTestSuites', 'TestSuites' : []}
    folders_list = get_files_to_list(path)
    test_suites = []
    for index, folder in enumerate(folders_list):
        test_suite = {}
        folder_name = str(folder[7:])
        test_suite.update({'Name' : folder_name})
        test_suite.update({'Tests' : get_files_to_list(folder+'/*')})
        #test_suite['Tests'] = get_files_to_list(folder+'/*')
        #test_suite['Name'] = folder_name
        # add test suite to test suites
        test_suites.insert(index, test_suite)


    print(test_suites)
    available_test_suites['TestSuites'] = test_suites
    return json.dumps(available_test_suites)

    

if __name__ == "__main__":
    json_available_test_suites = folder_read_to_json('/tests/*')
    print(json_available_test_suites)

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

