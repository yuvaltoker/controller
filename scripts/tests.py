# this file will include- TestFile, DlepTest, SnmpTest


class TestFile:
    def __init__(self, file_name):
        self.dlep_tests = []
        self.snmp_tests = []
        self.file_name = file_name
        self.current_test = None

    def check_if_current_test_ready(self):
        return self.current_test.check_if_test_ready()

    def add_test(self):
        if self.current_test.get_test_type() == 'DLEP':
            self.dlep_tests.append(self.current_test)
        elif self.current_test.get_test_type() == 'SNMP':
            self.snmp_tests.append(self.current_test)

    def get_file_name(self):
        return self.file_name

    def get_dlep_tests(self):
        return self.dlep_tests

    def get_snmp_tests(self):
        return self.snmp_tests

    def has_dlep_tests(self):
        if len(self.dlep_tests):
            return True
        return False

    def has_snmp_tests(self):
        if len(self.snmp_tests):
            return True
        return False

    def set_test_name(self, name):
        self.current_test.set_name(name)

    def create_dlep_test(self, test_word_list):
        self.current_test = DlepTest(test_word_list)

    def create_snmp_test(self, test_word_list):
        self.current_test = SnmpTest(test_word_list)

    # for dlep test, as hit the 'TO_INCLUDE' or 'TO_NOT_INCLUDE'
    def set_include(self, is_need_to_include, item_to_include):
        self.current_test.set_include(is_need_to_include, item_to_include)

    # for dlep test, as hit the 'SIGNAL'
    def set_signal(self, signal):
        self.current_test.set_signal(signal)

    # for snmp, as hit the 'OID'
    def set_oid(self, oid):
        self.current_test.set_oid(oid)

    # for snmp, as hit the 'READONLY'/'SETTABLE'
    def set_to_be(self, command):
        self.current_test.set_command(command)

    # for snmp, as hit the 'INTEGER'/'OCTET_STRING'
    def set_mib_type(self, mib_type):
        self.current_test.set_mib_type(mib_type)

    # for snmp, as hit the value
    def set_mib_value(self, mib_value):
        self.current_test.set_mib_value(mib_value)

    def delete_test(self, test):
        if test in self.dlep_tests:
            self.dlep_tests.remove(test)
        elif test in self.snmp_tests:
            self.snmp_tests.remove(test)

    def get_test(self, test):
        return test.get_test()

    def get_tests_jsons(self):
        all_tests = []
        dlep_tests_to_strings = [self.get_test(test) for test in self.dlep_tests]
        snmp_tests_to_strings = [self.get_test(test) for test in self.snmp_tests]
        all_tests.extend(dlep_tests_to_strings)
        all_tests.extend(snmp_tests_to_strings)
        return all_tests



class DlepTest:
    def __init__(self, test_word_list):
        self.test_word_list = test_word_list
        self.name = ''
        self.signal = ''
        self.is_signal_need_to_include = ''
        self.is_data_item_need_to_include = ''
        # whether to include or to not include, what item?
        self.data_item = ''
        self.sub_data_item = ''
        self.full_test = ''

    def get_test_type(self):
        return 'DLEP'

    def set_name(self, name):
        self.name = name

    def set_signal(self, signal):
        self.signal = signal

    def set_include(self, is_need_to_include, item_to_include):
        if self.is_signal_need_to_include == '':
            self.is_signal_need_to_include = is_need_to_include
            self.data_item = item_to_include
        else:
            self.is_data_item_need_to_include = is_need_to_include
            self.sub_data_item = item_to_include

    def test_to_json(self):
        json_test = {}
        json_test['Type'] = self.get_test_type()
        json_test['Name'] = self.name
        json_test['Test'] = {'Signal' : self.signal}
        json_test['Test'][self.is_signal_need_to_include] = {'Data Item' : self.data_item}
        if self.is_data_item_need_to_include != '':
            json_test['Test'][self.is_signal_need_to_include][self.is_data_item_need_to_include] = {'Sub Data Item' : self.sub_data_item}
        return json_test

    def get_test(self):
        return self.test_to_json()
    
    def check_if_test_ready(self):
        if self.name != '' and self.signal != '' and self.is_signal_need_to_include != '' and self.data_item != '':
            if self.is_data_item_need_to_include != '' and self.sub_data_item == '':
                return False
            return True
        return False
    


class SnmpTest:
    def __init__(self, test_word_list):
        self.test_word_list = test_word_list
        self.name = ''
        self.oid = ''
        # command can be READONLY/SETTABLE (get/set)
        self.command = ''
        self.mib_type = ''
        self.mib_value = ''
        self.full_test = ''

    def get_test_type(self):
        return 'SNMP'

    def set_name(self, name):
        self.name = name

    def set_oid(self, oid):
        self.oid = oid

    def set_command(self, command):
        if command == 'READONLY':
            self.command = 'get'
        elif command == 'SETTABLE':
            self.command = 'set'

    def set_mib_type(self, mib_type):
        self.mib_type = mib_type

    def set_mib_value(self, mib_value):
        self.mib_value = mib_value

    def test_to_json(self):
        json_test = {}
        json_test['Type'] = self.get_test_type()
        json_test['Name'] = self.name
        json_test['Test'] = {'Oid' : self.oid, 'To be' : self.command, 'Mib type' : self.mib_type}
        if self.mib_value != '':
            json_test['Test']['Mib value'] = self.mib_value
        return json_test

    def get_test(self):
        return self.test_to_json()

    def check_if_test_ready(self):
        if self.name != '' and self.oid != '' and self.command != '' and self.mib_type != '':
            return True
        return False