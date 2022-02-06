# this file will include- TestFile(?), DlepTest, SnmpTest


class TestFile:
    def __init__(self):
        self.dlep_tests = []
        self.snmp_tests = []
        self.current_test = None

    def check_if_current_test_ready(self):
        return self.current_test.check_if_test_ready()

    def add_test(self):
        if self.current_test.get_test_type() == 'DLEP':
            self.dlep_tests.append(self.current_test)
        elif self.current_test.get_test_type() == 'SNMP':
            self.snmp_tests.append(self.current_test)

    def set_test_name(self, name):
        self.current_test.set_name(name)

    def create_dlep_test(self, test_word_list):
        self.current_test = DlepTest(test_word_list, self.current_name_of_test)

    def create_snmp_test(self, test_word_list):
        self.current_test = SnmpTest(test_word_list, self.current_name_of_test)

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
        self.current_test.set_mib_type(mib_value)

    def delete_test(self, test):
        if test in self.dlep_tests:
            self.dlep_tests.remove(test)
        elif test in self.snmp_tests:
            self.snmp_tests.remove(test)


class DlepTest:
    def __init__(self, test_word_list):
        self.test_word_list = test_word_list
        self.name = ''
        self.signal = ''
        self.is_need_to_include = ''
        self.is_data_item_need_to_include = ''
        # weather to include or to not include, what item?
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
        if self.is_need_to_include == '':
            self.is_need_to_include = is_need_to_include
            self.item = item_to_include
        else:
            self.is_data_item_need_to_include = is_need_to_include
            self.sub_data_item = item_to_include

    def build_test(self):
        self.full_test = '{}, {}, {}'.format(self.signal, self.data_item)

    def get_test(self):
        return self.full_test
    
    def check_if_test_ready(self):
        pass
    


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

    def build_test(self):
        self.full_test = '{}, {}, {}'.format(self.oid, self.command, self.value)

    def get_test(self):
        return self.full_test

    def check_if_test_ready(self):
        pass