import glob
import json

def get_files_to_list(path):
    all_files = []
    for file in glob.glob(path):
        all_files.append(file)
    return all_files

def main():
    json_available_test_suites = folder_read_to_json('/tests/*')
    print(json_available_test_suites)

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

