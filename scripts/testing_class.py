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
    test_suites = {}
    for folder in folders_list:
        folder_name = str(folder[7:])
        test_suites[folder_name] = get_files_to_list(folder+'/*')

    print(test_suites)

    

if __name__ == "__main__":
    folder_read_to_json('/tests/*')

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

