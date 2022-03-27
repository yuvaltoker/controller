# this file will include- TestFile, DlepTest, SnmpTest

# for easy read/write on mongodb
from typing import Any
from mongodb_handler import MongodbHandler
from test_parser import DlepTestParser, SnmpTestParser
from abc import ABC, abstractmethod


class Test(ABC):
    @abstractmethod
    def __init__(self, type: str) -> None:
        self.type = type
        self.name = ''

    # the meaning of the next function is when creating new type of test (@DlepTest, @SnmpTest, etc...) this function has to be override
    @abstractmethod
    def check_if_test_ready(self) -> None:
        """An Excepton will be raised when child of Test will not implement this method"""
        raise NotImplementedError()

    def get_type(self) -> str:
        return self.type

    @abstractmethod
    def exec_test(self) -> None:
        raise NotImplementedError()

class DlepTest(Test):
    def __init__(self, type: str) -> None:
        super().__init__(type)
        self.signal = ''
        self.is_signal_need_to_include = ''
        self.is_data_item_need_to_include = ''
        # whether to include or to not include, what item?
        self.data_item = ''
        self.sub_data_item = ''

    def set_signal(self, signal: str) -> None:
        self.signal = signal

    def set_include(self, is_need_to_include: str, item_to_include: str) -> None:
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

    def exec_test(self) -> None:
        pass
    

class SnmpTest(Test):
    def __init__(self, type: str) -> None:
        super().__init__(type)
        self.oid = ''
        # command can be READONLY/SETTABLE (get/set)
        self.command = ''
        self.mib_type = ''
        self.mib_value = ''
        self.full_test = ''

    def set_oid(self, oid: str) -> None:
        self.oid = oid

    def set_command(self, command: str) -> None:
        if command == 'READONLY':
            self.command = 'get'
        elif command == 'SETTABLE':
            self.command = 'set'

    def set_mib_type(self, mib_type: str) -> None:
        self.mib_type = mib_type

    def set_mib_value(self, mib_value: str) -> None:
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

    def exec_test(self) -> None:
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