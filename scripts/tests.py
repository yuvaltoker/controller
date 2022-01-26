# this file will include- TestFile(?), DlepTest, SnmpTest


class TestFile:
    def __init__(self):
        self.dlep_tests = []
        self.snmp_tests = []
        self.name = ''
        self.is_name_set = False
        self.current_test = None

    def set_name(self, name):
        self.name = name
        self.is_name_set = True

    def create_dlep_test(self, test_word_list):
        self.current_test = DlepTest(test_word_list)

    def create_snmp_test(self, test_word_list):
        self.current_test = SnmpTest(test_word_list)

    def delete_test(self, test):
        if test in self.dlep_tests:
            self.dlep_tests.remove(test)
        elif test in self.snmp_tests:
            self.snmp_tests.remove(test)


class DlepTest:
    def __init__(self, test_word_list):
        self.test_word_list = test_word_list
        self.signal = ''
        self.command = ''
        self.data_item = ''
        self.full_test = ''

    def set_signal(self, signal):
        self.signal = signal

    def set_command(self, command):
        self.command = command

    def set_data_item(self, data_item):
        self.data_item = data_item

    def build_test(self):
        self.full_test = '{}, {}, {}'.format(self.signal, self.command, self.data_item)

    def get_test(self):
        return self.full_test
    


class SnmpTest:
    def __init__(self, test_word_list):
        self.test_word_list = test_word_list
        self.oid = ''
        # command can be set/get
        self.command = ''
        self.value = ''
        self.full_test = ''

    def set_command(self, command):
        self.command = command

    def set_oid(self, oid):
        self.oid = oid

    def set_value(self, value):
        self.value = value

    def build_test(self):
        self.full_test = '{}, {}, {}'.format(self.oid, self.command, self.value)

    def get_test(self):
        return self.full_test