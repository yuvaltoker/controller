# this file will include- TestFile, DlepTest, SnmpTest

# for easy read/write on mongodb
from typing import Any
from mongodb_handler import MongodbHandler
from test_parser import DlepTestParser, SnmpTestParser
from abc import ABC, abstractmethod

'''
class TestFile:
    def __init__(self, file_name):
        self.dlep_tests = []
        self.snmp_tests = []
        self.tests = []
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

    def exec_all_tests(self):
        pass
'''


class Test(ABC):
    @abstractmethod
    def __init__(self, type: str):
        self.type = type
        self.name = ''

    # the meaning of the next function is when creating new type of test (@DlepTest, @SnmpTest, etc...) this function has to be override
    @abstractmethod
    def check_if_test_ready(self):
        raise NotImplementedError()

    def get_type(self) -> str:
        return self.type

class DlepTest(Test):
    def __init__(self, type: str):
        super().__init__(type)
        self.signal = ''
        self.is_signal_need_to_include = ''
        self.is_data_item_need_to_include = ''
        # whether to include or to not include, what item?
        self.data_item = ''
        self.sub_data_item = ''

    def set_signal(self, signal: str):
        self.signal = signal

    def set_include(self, is_need_to_include: str, item_to_include: str):
        if self.is_signal_need_to_include == '':
            self.is_signal_need_to_include = is_need_to_include
            self.data_item = item_to_include
        else:
            self.is_data_item_need_to_include = is_need_to_include
            self.sub_data_item = item_to_include

    def test_to_json(self) -> dict[str, Any]:
        json_test = {}
        json_test['Type'] = self.type
        json_test['Name'] = self.name
        json_test['Test'] = {'Signal' : self.signal}
        json_test['Test'][self.is_signal_need_to_include] = {'Data Item' : self.data_item}
        if self.is_data_item_need_to_include != '':
            json_test['Test'][self.is_signal_need_to_include][self.is_data_item_need_to_include] = {'Sub Data Item' : self.sub_data_item}
        return json_test

    def get_test(self) -> dict[str, Any]:
        return self.test_to_json()
    
    def check_if_test_ready(self) -> bool:
        if self.name != '' and self.signal != '' and self.is_signal_need_to_include != '' and self.data_item != '':
            if self.is_data_item_need_to_include != '' and self.sub_data_item == '':
                return False
            return True
        return False

    def exec_test(self):
        pass
    

class SnmpTest(Test):
    def __init__(self, type: str):
        super().__init__(type)
        self.oid = ''
        # command can be READONLY/SETTABLE (get/set)
        self.command = ''
        self.mib_type = ''
        self.mib_value = ''
        self.full_test = ''

    def set_oid(self, oid: str):
        self.oid = oid

    def set_command(self, command: str):
        if command == 'READONLY':
            self.command = 'get'
        elif command == 'SETTABLE':
            self.command = 'set'

    def set_mib_type(self, mib_type: str):
        self.mib_type = mib_type

    def set_mib_value(self, mib_value: str):
        self.mib_value = mib_value

    def test_to_json(self) -> dict[str, Any]:
        json_test = {}
        json_test['Type'] = self.type
        json_test['Name'] = self.name
        json_test['Test'] = {'Oid' : self.oid, 'To be' : self.command, 'Mib type' : self.mib_type}
        if self.mib_value != '':
            json_test['Test']['Mib value'] = self.mib_value
        return json_test

    def get_test(self) -> dict[str, Any]:
        return self.test_to_json()

    def check_if_test_ready(self) -> bool:
        if self.name != '' and self.oid != '' and self.command != '' and self.mib_type != '':
            return True
        return False

    def exec_test(self):
        pass

class TestFile:
    def __init__(self, file_name: str):
        self.test_types = {'DLEP' : DlepTest, 'SNMP' : SnmpTest}
        self.tests = []
        self.file_name = file_name

    def create_test(self, test_type: str) -> tuple[bool, Test]:
        if test_type not in self.test_types:
            return False, None 
        # example for the next line is DlepTest(type, DlepTestParser)
        return True, self.test_types[test_type](test_type)

    def add_test(self, test: Test):
        self.tests.append(test)