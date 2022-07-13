from __future__ import annotations
from abc import ABC, abstractmethod
from multiprocessing.sharedctypes import Value
import os
import time
from typing import Any, Callable, Dict, List
from dataclasses import dataclass, field
import easysnmp

from json import loads
from mongodb_handler import MongodbHandler
from rabbitmq_handler import RabbitmqHandler
from test_lib import TestFile, Test, DLEP_KEYWORD, SNMP_KEYWORD
import logging

class CannotBeParsedError(Exception):
    """Custom error which raised when a test/file cannot be parsed"""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

class CannotBeExecutedError(Exception):
    """Custom error which raised when a test cannot be executed"""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

def configure_logger_logging(logger, logging_level, logging_file) -> None:
        logger.setLevel(logging_level)
        # create formatter and add it to the handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # if there's a logging file
        if logging_file is not None:
            # create file handler that logs debug and higher level messages
            file_handler = logging.FileHandler(logging_file)
            file_handler.setLevel(logging_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            # setting logging level for the console handler
            logging_level = logging.ERROR
        # create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging_level)
        console_handler.setFormatter(formatter)
        # add the handlers to logger
        logger.addHandler(console_handler)


TEST_LINES_LENGTH = 3
TIME_DELAY = int(os.getenv('TIME_DELAY'))

class TestFilesHandler:
    '''class handling parsing and executing test files, acts as master agent when it comes to test files'''
    def __init__(self, logging_level, logging_file = None) -> None: 
        logger = logging.getLogger('test_files_handler')
        self.test_files = {}
        self.test_file_parser = TestFilesParser(logging_level=logging_level)
        self.test_file_executer = TestFilesExecuter(logging_level=logging_level)

    def parse_files(self, files: List[str]) -> None:
        self.test_file_parser.parse_files(files)
        self.test_files = self.test_file_parser.get_test_files_dict()

    def get_test_files_arranged_by_folders(self) -> Dict[str, List[str]]:
        '''returns a dict of files which succeeded the parsing as {folder1 : [path1,path2,...], folder2 : [path1,path2,...]}'''
        return self.test_file_parser.get_test_files_arranged_by_folders()

    def execute_tests_files(self, mdb_handler: MongodbHandler, rmq_handler: RabbitmqHandler, test_files_paths: str) -> None:
        '''execute test files'''
        for test_file_path in test_files_paths:
            # currently the app stub is working without the /tests/ in the begginning of the path in Configuration collection.
            # so the added '/tests/' should be removed once it get fixed by the writers of the app
            test_file = self.test_files['/tests/{}'.format(test_file_path)]
            self.test_file_executer.execute_test_file(mdb_handler=mdb_handler, 
                rmq_handler=rmq_handler, 
                test_file=test_file)


class TestFilesParser:
    def __init__(self, logging_level, logging_file = None) -> None: 
        # when adding new type of TestParser's child, add the class' name here
        self.list_test_parser_types = {DlepTestParser, SnmpTestParser}
        # here will be saved dict of [str(keyword), TestParser(child)], for example {'DLEP', DlepTestParser}
        self.dict_test_parsers = {}
        # fill the above dict, by calling the init func the test_parser child class will register itself to the dict
        for parser_class in self.list_test_parser_types:
            parser_class(parsers_dict=self.dict_test_parsers)
        self.test_files = []
        # logging
        logger = logging.getLogger('test_parser')
        configure_logger_logging(logger, logging_level, logging_file)
        self.logger = logger

    def file_to_lines(self, file: str) -> List[str]:
        with open(file, 'r') as file:
            file_lines = file.readlines()
            file_lines = [line.rstrip() for line in file_lines]
        return file_lines

    def parse_files(self, files: List[str]) -> None:
        for file in files:
            self.parse_file(file)

    def parse_test(self, test_file: TestFile, current_test_lines: List[List[str]]) -> None:
        '''parse test by given lines, in case of success, add the test into test_file's list of tests'''
        line = current_test_lines[0]
        if line[0] != 'TYPE:':
            raise CannotBeParsedError('expected TYPE command, instead got  {}'.format(' '.join(line[0])))
        # expect type
        test_type = line[1]
        # @create_test function in @TestFile returns a tuple[bool, Test]
        has_created, test = test_file.create_test(test_type=test_type)
        if not has_created:
            raise CannotBeParsedError('TYPE value {} not found in tests type'.format(' '.join(test_type)))
        # if test_type is not in self.dict_test_parser
        if not test_type in self.dict_test_parsers:
            raise CannotBeParsedError('TYPE value {} not found in test parser dict'.format(' '.join(test_type)))
        current_test_lines[:] = current_test_lines[1:]
        # test parser should get @Test and list of lines (list[list[str]]) containing 2 lines, the 2nd and 3rd lines
        parser = self.dict_test_parsers.get(test_type)
        if parser is None:
            raise CannotBeParsedError('could not find compatible parser to type {}'.format(' '.join(test_type)))
        # parsing the test
        parser.parse_test(test=test, 
            lines_to_parse=current_test_lines)
        # checking successful parsing, in case of failure an exception will be raised
        if test.check_if_test_ready():
            # add the current test into list of tests
            test_file.add_test(test)
        else:
            raise CannotBeParsedError('after parsing the test lines, the test check was not passed')
        
    def parse_file(self, file: str) -> None:
        '''parse file, in case of success, add the file into self.test_files'''
        file_lines = self.file_to_lines(file)
        test_file = TestFile(file)
        try:
            # when lines_counter reach 3, it mean we have a whole test ready to be read
            current_test_lines = []
            for line in file_lines:
                if line == '' or line[0] == '#':
                    continue
                word_list = line.split(' ')
                # removing all the '' in the list, it'll raise an exception when '' will not be exist anymore
                try:
                    word_list = [word for word in word_list if word != '']
                except:
                    pass
                current_test_lines.append(word_list)
                # when we reach the possibility of Type, Name and Test, it means we're ready to read
                if len(current_test_lines) == TEST_LINES_LENGTH:
                    self.parse_test(test_file, current_test_lines)
                    # removing all junk from before in any case, for the next test to come out
                    current_test_lines[:] = []
            # a succesful tdf file should not have spare lines
            if current_test_lines != []:
                raise CannotBeParsedError('tdf file got spare line/s')
        except CannotBeParsedError as e:
            self.logger.error('file {} cannot be parsed. error message -> {}'.format(file, e.message))
            # stopping the function in order to not add the file
            return 
        self.test_files.append(test_file)

    
    def get_test_files_arranged_by_folders(self) -> Dict[str, List[str]]:
        '''returns a dict of files which succeeded the parsing as {folder1 : [path1,path2,...], folder2 : [path1,path2,...]}'''
        dict_all_tests_files = {}
        for file in self.test_files:
            # getting the file_path
            file_path = file.get_file_name()
            # getting the subpath given the path is /tests/subpath/...
            sub_path = file_path.split('/')[2]
            self.logger.info('subpath is {} for {}'.format(sub_path, file_path))
            # in case it's the first time of seeing this sub_path, creating a list for this sub_path
            if sub_path not in dict_all_tests_files:
                dict_all_tests_files[sub_path] = []
            # append the sub_path list in the dictionary with the file_path
            dict_all_tests_files[sub_path].append(file_path)
        return dict_all_tests_files

    def get_test_files_dict(self) -> Dict[str, TestFile]:
        '''returns the next dict: {path1 : TestFile1, path2 : TestFile2, ..., pathN : TestFileN}'''
        return {test_file.get_file_name() : test_file for test_file in self.test_files}


class TestParser(ABC):
    @abstractmethod
    def __init__(self, my_keyword_type: str, dict_of_parser_commands: Dict[str, Callable]) -> None:
        self.my_keyword_type = my_keyword_type
        # the next functions in dictionary must get 2 variables; test - Test, and rest of line - list[str]
        self.dict_of_basic_commands = {'NAME:' : self.set_test_name, \
            'TEST:' : self.parse_specific_parser_keywords}
        self.dict_of_parser_commands = dict_of_parser_commands

    def get_my_keyword_type(self) -> str:
        return self.my_keyword_type

    def parse_generic_parser_keywords(self, test: Test, line: List[str]) -> None:
        if not self.is_keyword_in_dict(dict=self.dict_of_basic_commands,
            keyword=line[0]):
            raise CannotBeParsedError('keyword {} not found '.format(''.join(line[0])))  
        # select the right keyword for the first word in line, then pass the rest of the line to function
        self.dict_of_basic_commands[line[0]](test=test, line=line[1:])

    def parse_specific_parser_keywords(self, test: Test, line: List[str]) -> None:
        while len(line):
            if not self.is_keyword_in_dict(dict=self.dict_of_parser_commands,
                keyword=line[0]):
                print(self.dict_of_parser_commands)
                raise CannotBeParsedError('keyword {} not found '.format(''.join(line[0])))
            # select the right keyword for the first word in line, then pass the rest of the line to function
            self.dict_of_parser_commands[line[0]](test=test,
                line=line)

    # this function is being called by TestFilesParser for each TEST_LINES_LENGTH lines from a file
    def parse_test(self, test: Test, lines_to_parse: List[List[str]]) -> None:
        for index, line in enumerate(lines_to_parse):
            # example, length is 3, TYPE line got reduced, so we've got 2 lines by now, so the max index should be 1
            if index >= TEST_LINES_LENGTH - 1:
                raise CannotBeParsedError('cannot parse test with more than {} lines'.format(' '.join(TEST_LINES_LENGTH)))
            # calling the 'parse line' function from each line
            self.parse_generic_parser_keywords(test=test, 
                line=line)

    def set_test_name(self,test: Test, line: List[str]) -> None:
        test.name = ' '.join(line)
        
    def is_keyword_in_dict(self, dict: Dict[str, Any], keyword: str) -> bool:
        return keyword in dict

    def cut_next_words(self, word_list, num_of_words) -> None:
        after_cutting = word_list[num_of_words:]
        if after_cutting == ['']:
            word_list[:] = []
        else:
            word_list[:] = after_cutting


class DlepTestParser(TestParser):
    def __init__(self, parsers_dict : Dict[str, TestParser]) -> None:
        # the next functions in dictionary must get 2 variables; test - Test, and rest of line - list[str]
        dict_of_parser_commands = {'EXPECT' : self.set_expect,
            'SIGNAL' : self.set_signal,
            'TO_INCLUDE' : self.set_to_include,
            'TO_NOT_INCLUDE' : self.set_to_not_include}
        super().__init__(my_keyword_type=DLEP_KEYWORD, 
            dict_of_parser_commands=dict_of_parser_commands)
        # regrister DlepTestParser to parsers_dict by using {self.my_keyword_type : self}
        parsers_dict[self.my_keyword_type] = self      

    def set_expect(self, test: Test, line: List[str]) -> None:
        test.expect = True
        # next word after this is 'SIGNAL', which is not a garbage word
        self.cut_next_words(word_list=line, num_of_words=1)

    def set_signal(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'SIGNAL' keyword, then the signal itself
        test.signal = line[1]
        # removing the 'SIGNAL' keyword and the signal itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_to_include(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'TO_INCLUDE' keyword, then 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, then the item/subdataitem to include
        test.handle_include(is_need_to_include='include', item=line[2])
        # removing the 'TO_INCLUDE' keyword, the 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, and the item/subdataitem that need to be include
        self.cut_next_words(word_list=line, num_of_words=3)

    def set_to_not_include(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'TO_NOT_INCLUDE' keyword, then 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, then the item/subdataitem to not include
        test.handle_include(is_need_to_include='not include', item=line[1])
        # removing the 'TO_NOT_INCLUDE' keyword, the 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, and the item/subdataitem that need to not be include
        self.cut_next_words(word_list=line, num_of_words=3)

class SnmpTestParser(TestParser):
    def __init__(self, parsers_dict : Dict[str, TestParser]) -> None:
        # the next functions in dictionary must get 2 variables; test - Test, and rest of line - list[str]
        dict_of_parser_commands = {'EXPECT' : self.set_expect,
            'OID' : self.set_oid,
            'TO_BE' : self.set_to_be,
            'OF_TYPE' : self.set_mib_type,
            'WITH_VALUE' : self.set_mib_value}
        super().__init__(my_keyword_type=SNMP_KEYWORD,
            dict_of_parser_commands=dict_of_parser_commands)
        parsers_dict[self.my_keyword_type] = self

    def set_expect(self, test: Test, line: List[str]) -> None:
        test.expect = True
        # next word after this is 'OID', which is not a garbage word
        self.cut_next_words(word_list=line, num_of_words=1)

    def set_oid(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'OID' keyword, then the oid itself
        test.oid=line[1]
        # removing the 'OID' keyword and the oid itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_to_be(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'TO_BE' keyword, then the readonly/settable
        test.command = line[1]
        # removing the 'TO_BE' keyword and the readonly/settable
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_mib_type(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'OF_TYPE' keyword, then the type itself
        test.mib_type = line[1]
        # removing the 'OF_TYPE' keyword and the type itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_mib_value(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'WITH_VALUE' keyword, then the value expression itself
        test.mib_value = line[1]
        # removing the 'WITH_VALUE' keyword and the value expression itself
        self.cut_next_words(word_list=line, num_of_words=2)

class TestFilesExecuter:
    def __init__(self, logging_level, logging_file = None) -> None: 
        # when adding new type of TestExecuter's child, add the class' name here
        self.list_test_executer_types = {DlepTestExecuter, SnmpTestExecuter}
        # here will be saved dict of [str(keyword), Testexecuter(child)], for example {'DLEP', dlepTestExecuter}
        self.dict_test_executers = {}
        # fill the above dict, by calling the init func the test_executer child class will register itself to the dict
        for executer_class in self.list_test_executer_types:
            executer_class(executers_dict=self.dict_test_executers)
        self.dict_of_optional_results = {True : 'Pass', False : 'Fail'}
        # logging
        logger = logging.getLogger('test_executer')
        configure_logger_logging(logger, logging_level, logging_file)
        self.logger = logger

    def build_result_json(self, name: str, result: bool) -> Dict[str, str]:
        return {'name' : name, 'result' : self.dict_of_optional_results[result]}
    
    def execute_test_file(self, mdb_handler: MongodbHandler, rmq_handler: RabbitmqHandler, test_file: TestFile) -> None:
        for test in test_file.tests:
            # handling json result parts:
            # name of test-
            test_name = test.name
            # executing the test and getting result-
            test_result = self.exec_test(test=test)
            # creating result json {name : name, result : 'Pass'/'Fail'}
            json_document_result = self.build_result_json(name=test_name, result=test_result)
            result_uid = mdb_handler.insert_document('Test Results', json_document_result)
            message = 'ctrl: got result - %s' % result_uid
            self.logger.info(message)
            rmq_handler.send('', 'results', str(result_uid))
            time.sleep(TIME_DELAY / 2)

    def exec_test(self, test: Test) -> bool:
        '''returns if test pass/fail (True/False)'''
        # get the right executer, if not found raise CannotBeExecutedError
        try:
            test_executer = self.dict_test_executers[test.type]
        except KeyError:
            raise CannotBeExecutedError('could not find any TestExecuter for keyword type: {}'.format(test.type))
        result = test_executer.exec_test(test=test)
        return result


class TestExecuter(ABC):
    @abstractmethod
    def __init__(self, my_keyword_type: str) -> None:
        self.my_keyword_type = my_keyword_type

    @abstractmethod
    def exec_test(self, test: Test) -> bool:
        raise NotImplementedError()


class DlepTestExecuter(TestExecuter):
    def __init__(self, executers_dict: Dict[str, TestExecuter]) -> None:
        super().__init__(my_keyword_type=DLEP_KEYWORD)
        executers_dict[self.my_keyword_type] = self

    def exec_test(self, test: Test) -> bool:
        '''returns if test pass/fail (True/False)'''
        return True

@dataclass
class SnmpConfiguration:
    '''object for easy and readable snmp configuration'''
    auth_pass: str = field(init=True)
    priv_pass: str = field(init=True)
    user_name: str = field(init=True)
    version: str = field(init=True)
    snmpd_host: str = field(init=True)

class SnmpTestExecuter(TestExecuter):
    def __init__(self, executers_dict: Dict[str, TestExecuter]) -> None:
        super().__init__(my_keyword_type=SNMP_KEYWORD)
        executers_dict[self.my_keyword_type] = self
        self.snmp_conf = SnmpConfiguration(auth_pass = os.getenv('AUTH_PASS'),
            priv_pass = os.getenv('PRIV_PASS'),
            user_name = os.getenv('USER_NAME'),
            version=os.getenv('SNMP_VERSION'),
            snmpd_host=os.getenv('SNMPD_HOST'))
        self.command_dict = {'get' : self.send_snmpget, 'set' : self.send_snmpset}

    '''example of snmpset/get for future work'''
    '''under each line, written from where the vars are supposed to be gotten from (supplied by docker-compose or by test class var (comp / test)'''
    '''snmpset -v2c -c public snmpd:1662 NET-SNMP-TUTORIAL-MIB::nstAgentSubagentObject.0 i $x >> file.log'''
    '''          |       |         |                         |                          /   \\   '''
    '''      | comp |  comp  |   comp   |                   test                    | test | test | '''
    # snmpget -v2c -c public 192.168.16.10:1662 1.3.6.1.4.1.8072.2.4.1.1.4.0
    '''snmpget -v2c -c public snmpd:1662 MY-TUTORIAL-MIB::batteryObject.0 >> file.log'''
    def exec_test(self, test: Test) -> bool:
        '''returns if test pass/fail (True/False)'''
        # command can be send_snmpget/send_snmpset
        command_function = self.command_dict[test.command]
        value = command_function(snmp_conf=self.snmp_conf, test=test)
        test.result = self.proccess_value(value=value, test=test)
        return test.result

    def send_snmpset(self, snmp_conf: SnmpConfiguration, test: Test) -> str:
        '''setting the mib with easysnmp library'''
        '''for more about easysnmplib see https://easysnmp.readthedocs.io/en/latest/easy_api.html'''
        easysnmp.snmp_set(test.oid,
            test.mib_value,
            test.mib_type,
            hostname = snmp_conf.snmpd_host,
            version = snmp_conf.version, 
            security_level = 'auth_with_privacy',
            security_username = snmp_conf.user_name, 
            privacy_protocol = 'AES',
            privacy_password = snmp_conf.priv_pass,
            auth_protocol = 'SHA',
            auth_password = snmp_conf.auth_pass)
            # sorry for the long and shitty non-pythonic use of more than 3 arguments... here is a potato
        # return snmpget value for checking the value afterwards
        mib_value = self.send_snmpget(snmp_conf=snmp_conf, test=test)
        return mib_value
        
    def send_snmpget(self, snmp_conf: SnmpConfiguration, test: Test) -> str:
        '''getting the mib with easysnmp library'''
        '''for more about easysnmplib see https://easysnmp.readthedocs.io/en/latest/easy_api.html'''
        mib_object = easysnmp.snmp_get(test.oid,
            hostname=snmp_conf.snmpd_host,
            version=snmp_conf.version, 
            security_level = 'auth_with_privacy',
            security_username = snmp_conf.user_name, 
            privacy_protocol = 'AES',
            privacy_password = snmp_conf.priv_pass,
            auth_protocol = 'SHA',
            auth_password = snmp_conf.auth_pass)
            # as written above, sorry for the long and shitty non-pythonic use of more than 3 arguments... here is a potato
        # return snmpget value
        print(f'mib type: {mib_object.type}, mib_value: {mib_object.value}')
        return mib_object.value
        
    def proccess_value(self, value: str, test: Test) -> bool:
        '''proccessing the returned value of snmpget/snmpset command'''
        return True