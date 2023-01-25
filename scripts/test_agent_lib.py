from __future__ import annotations
from abc import ABC, abstractmethod
import os
from ssl import Purpose
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple
from dataclasses import dataclass, field

from json import loads
from rabbitmq_handler import RabbitmqHandler
from mongodb_handler import MongodbHandler
from test_lib import TestFile, Test, DLEP_KEYWORD, SNMP_KEYWORD
import logging
import easysnmp
#from easysnmp import EasySNMPTimeoutError, EasySNMPConnectionError, EasySNMPError, EasySNMPNoSuchObjectError, EasySNMPNoSuchInstanceError, EasySNMPNoSuchNameError, EasySNMPBadValueError

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

    def execute_tests_files(self, mdb_handler: MongodbHandler, rmq_handler: RabbitmqHandler, test_files_paths: str, device_ip: str) -> None:
        '''execute test files'''
        for test_file_path in test_files_paths:
            test_file = self.test_files['{}'.format(test_file_path)]
            self.test_file_executer.execute_test_file(mdb_handler=mdb_handler, 
                rmq_handler=rmq_handler, 
                test_file=test_file,
                device_ip=device_ip)


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
                if line == '':
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
        # plus, cutting the "" at the start and at the end of the word
        test.signal = line[1][1:-1]
        # removing the 'SIGNAL' keyword and the signal itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_to_include(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'TO_INCLUDE' keyword, then 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, then the item/subdataitem to include
        test.handle_include(is_need_to_include='include', item=line[2][1:-1])
        # removing the 'TO_INCLUDE' keyword, the 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, and the item/subdataitem that need to be include
        self.cut_next_words(word_list=line, num_of_words=3)

    def set_to_not_include(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'TO_NOT_INCLUDE' keyword, then 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, then the item/subdataitem to not include
        test.handle_include(is_need_to_include='not include', item=line[2][1:-1])
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
        # plus, cutting the "" at the start and at the end of the word
        test.oid = line[1][1:-1]
        # removing the 'OID' keyword and the oid itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_to_be(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'TO_BE' keyword, then the readonly/settable
        test.set_command(line[1])
        # removing the 'TO_BE' keyword and the readonly/settable
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_mib_type(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'OF_TYPE' keyword, then the type itself
        test.mib_type = line[1]
        # removing the 'OF_TYPE' keyword and the type itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_mib_value(self, test: Test, line: List[str]) -> None:
        # first word in list contains the 'WITH_VALUE' keyword, then the value expression itself
        # plus, cutting the "" at the start and at the end of the word
        test.mib_value = line[1][1:-1]
        # removing the 'WITH_VALUE' keyword and the value expression itself
        self.cut_next_words(word_list=line, num_of_words=2)

class TestFilesExecuter:
    def __init__(self, logging_level, logging_file = None) -> None: 
        # when adding new type of TestExecuter's child, add the class' name here
        self.list_test_executer_types = {DlepTestExecuter, SnmpTestExecuter}
        # here will be saved dict of [str(keyword), Testexecuter(child)], for example {'DLEP', DlepTestExecuter}
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
    
    def execute_test_file(self, mdb_handler: MongodbHandler, rmq_handler: RabbitmqHandler, test_file: TestFile, device_ip: str) -> None:
        for test in test_file.tests:
            # handling json result parts:
            # name of test-
            test_name = test.name
            # executing the test and getting result-
            test_result = self.exec_test(test=test, mdb_handler=mdb_handler, device_ip=device_ip)
            # creating result json {name : name, result : 'Pass'/'Fail'}
            json_document_result = self.build_result_json(name=test_name, result=test_result)
            result_uid = mdb_handler.insert_document('Test Results', json_document_result)
            message = 'ctrl: got result - %s' % result_uid
            self.logger.info(message)
            rmq_handler.send('', 'results', str(result_uid))
            time.sleep(TIME_DELAY / 2)

    def exec_test(self, test: Test, mdb_handler: MongodbHandler, device_ip: str) -> bool:
        '''returns if test pass/fail (True/False)'''
        # get the right executer, if not found raise CannotBeExecutedError
        try:
            test_executer = self.dict_test_executers[test.get_test_type()]
        except KeyError:
            raise CannotBeExecutedError('could not find any TestExecuter for keyword type: {}'.format(test.get_test_type()))
        result = test_executer.exec_test(test=test, mdb_handler=mdb_handler, device_ip=device_ip)
        return result


class TestExecuter(ABC):
    @abstractmethod
    def __init__(self, my_keyword_type: str) -> None:
        self.my_keyword_type = my_keyword_type

    @abstractmethod
    def exec_test(self, test: Test, mdb_handler: MongodbHandler) -> bool:
        raise NotImplementedError()


class DlepTestExecuter(TestExecuter):
    def __init__(self, executers_dict: Dict[str, TestExecuter]) -> None:
        super().__init__(my_keyword_type=DLEP_KEYWORD)
        executers_dict[self.my_keyword_type] = self

    def exec_test(self, test: Test, mdb_handler: MongodbHandler, device_ip: str) -> bool:
        '''returns if test pass/fail (True/False)'''
        has_passed = True
        #message_by_signal = mdb_handler.get_all_documents_in_list('DlepMessage')
        message_by_signal = mdb_handler.get_find_one('DlepMessage', 'MessageType', '{}'.format(test.signal))
        #message_by_signal = mdb_handler.get_find_one('Configuration', 'MessageType', 'Peer_Discovery')
        # is there is not a signal of test.signal -> failed
        if message_by_signal is None:
            return False


        # is test has the attribute include
        if test.is_signal_need_to_include != '':
            is_include = test.is_signal_need_to_include == 'include'
            # from the list of data items, is there any data item with 'Name' of test.data_item?
            all_data_items = message_by_signal['DataItems']
            correct_data_items = [item for item in all_data_items if 'Name' in item and item['Name'] == test.data_item]
            has_data_item = correct_data_items is not None and correct_data_items != []
            # if both 'include' and has data item or 'not_include' and has not data item
            # i.e if both true or both false (the opposite of xor)
            has_passed =  not (is_include ^ has_data_item)

            # is data_item has the attribute include
            if has_passed and test.is_data_item_need_to_include != '':
                if correct_data_items == []:
                    # situation like this is happenning when consequence of NOT_INCLUDE and then INCLUDE accurs
                    return False
                is_include = test.is_data_item_need_to_include == 'include'
                # the [0] thing is becasue we're getting a list containing only the dictionary, so the dict on first index (0)
                all_sub_data_items = correct_data_items[0]['SubDataItems']
                correct_sub_data_items = [sub_data_item for sub_data_item in all_sub_data_items if 'Name' in sub_data_item and sub_data_item['Name'] == test.sub_data_item]
                has_sub_data_item = correct_sub_data_items is not None and correct_sub_data_items != []
                # if both 'include' and has data item or 'not_include' and has not data item
                # i.e if both true or both false (the opposite of xor)
                has_passed =  not (is_include ^ has_sub_data_item)

        return has_passed
        


@dataclass
class SnmpQuery:
    '''object for easy managment of snmp get/set query'''
    oid: str
    mib_type: str
    mib_value: str

@dataclass
class SnmpConfiguration:
    '''object for easy and readable snmp configuration'''
    security_level: str
    privacy_protocol: str
    auth_protocol: str
    auth_pass: str
    priv_pass: str
    user_name: str
    version: int


class SnmpTestExecuter(TestExecuter):
    def __init__(self, executers_dict: Dict[str, TestExecuter]) -> None:
        super().__init__(my_keyword_type=SNMP_KEYWORD)
        executers_dict[self.my_keyword_type] = self
        self.snmp_conf = SnmpConfiguration(auth_pass=os.getenv('AUTH_PASS'),
            priv_pass=os.getenv('PRIV_PASS'),
            user_name=os.getenv('USER_NAME'),
            security_level='auth_with_privacy',
            privacy_protocol='AES',
            auth_protocol='SHA',
            version=3)
        self.command_dict = {'get' : self.snmpget, 'set' : self.snmpset, 'only_get' : self.only_snmpget}

    '''example of snmpset/get for future work'''
    '''under each line, written from where the vars are supposed to be gotten from (supplied by docker-compose or by test class var (comp / test)'''
    '''snmpset -v2c -c public snmpd:1662 NET-SNMP-TUTORIAL-MIB::nstAgentSubagentObject.0 i $x >> file.log'''
    '''          |       |         |                         |                          /   \\   '''
    '''      | comp |  comp  |   comp   |                   test                    | test | test | '''
    '''snmpget -v2c -c public snmpd:1662 MY-TUTORIAL-MIB::batteryObject.0 >> file.log'''
    # sending snmpget request:
    # { "method":"GET","destination":"snmpd:1662","oid":"1.3.6.1.4.1.8073.1.1.4.0","name":"bla","type":"snmpRequest","time":"132","hash":"" }
    # sending snmpset request
    #{ "method":"SET","destination":"snmpd:1662","oid":"1.3.6.1.4.1.8073.1.1.4.0","name":"bla","type":"snmpRequest","time":"132","hash":"12321", "value":"2", "dataType":"i" }
    
    def exec_test(self, test: Test, mdb_handler: MongodbHandler, device_ip: str) -> bool:
        '''returns if test pass/fail (True/False)'''
        # snmp tests must contain mib type
        if test.mib_type == '':
            return False

        # when testing we want the ip to be the snmpd ip
        # when on production we want the device_ip to be taken from DB, and that is being handled on controller.py
        # in other words, when testing we changed device_ip to be snmpd, otherwise we dont change anything 
        state = os.getenv('STATE')
        if state == 'testing':
            device_ip = 'snmpd'
        # command can be send_snmpget/send_snmpset
        port = '1662'
        snmpd_location = '{}:{}'.format(device_ip, port)
        # when creating the snmpquery, the mib_type and mib_value of test is either '' when it is command='get', or with values when command='set'
        snmp_query = SnmpQuery(test.oid,
            test.mib_type,
            test.mib_value)
        has_passed = self.command_dict[test.command](snmp_query=snmp_query, snmpd_location=snmpd_location, mdb_handler=mdb_handler)
        return has_passed

    def insert_snmp_json(self, type: str, method: str, destination: str,
        oid: str, name: str, time: str,status: str,
        mdb_handler: MongodbHandler) -> None:
        '''inserts information of the snmp request into the "rri" db into "SnmpMessage" collection'''
        snmp_json = {}
        snmp_json['type'] = type
        snmp_json['method'] = method
        snmp_json['destination'] = destination
        snmp_json['oid'] = oid
        snmp_json['name'] = name
        snmp_json['time'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        snmp_json['status'] = status
        # insert the json into mongoDB
        mdb_handler.insert_document('SnmpMessage', snmp_json)  
        
    # For future use, the snmp_set and snmp_get of easysnmp can throw the following Errors:
    # EasySNMPTimeoutError, EasySNMPConnectionError, EasySNMPError, EasySNMPNoSuchObjectError, 
    # EasySNMPNoSuchInstanceError, EasySNMPNoSuchNameError, EasySNMPBadValueError
    def snmpget(self, snmp_query: SnmpQuery, snmpd_location: str, mdb_handler: MongodbHandler) -> bool:
        '''handles the case of command=READABLE'''
        mib_value, mib_type, status = self.send_snmpget(snmp_conf=self.snmp_conf, snmp_query=snmp_query, snmpd_location=snmpd_location, mdb_handler=mdb_handler)
        if status == False or snmp_query.mib_type != mib_type:
            return False
        if snmp_query.mib_value != '':
            if mib_type == 'ECTET_STRING':
                if snmp_query.mib_value != mib_value:
                    return False
            elif mib_type == 'INTEGER':
                if snmp_query.mib_value.startswith('>'):
                    if not (mib_value > int(snmp_query.mib_value[1:])):
                        return False
                elif snmp_query.mib_value.startswith('='):
                    if not (mib_value == int(snmp_query.mib_value[1:])):
                        return False
                elif snmp_query.mib_value.startswith('<'):
                    if not (mib_value < int(snmp_query.mib_value[1:])):
                        return False
                else:
                    return False
        return True
        
    def snmpset(self, snmp_query: SnmpQuery, snmpd_location: str, mdb_handler: MongodbHandler) -> bool:
        '''handles the case of command=SETTABLE'''
        '''to preserve it's original value we will first store the value, then set it twice, once with random value, later with the original value'''
        # storing the original value in mib_value
        mib_value, mib_type, status = self.send_snmpget(snmp_conf=self.snmp_conf, snmp_query=snmp_query, 
            snmpd_location=snmpd_location, mdb_handler=mdb_handler)
        if status == False:
            # taking into account that if a mib is settable he is also gettable
            return False
        # preparing the next value into snmp_query.mib_value, the value will be integer so that it will handle both str&&int cases
        snmp_query.mib_value = '123'
        result = self.send_snmpset(snmp_conf=self.snmp_conf, snmp_query=snmp_query, snmpd_location=snmpd_location, mdb_handler=mdb_handler)
        if result == False:
            return False
        # setting the original value back
        snmp_query.mib_value = mib_value
        result = self.send_snmpset(snmp_conf=self.snmp_conf, snmp_query=snmp_query, snmpd_location=snmpd_location, mdb_handler=mdb_handler)
        return True

    def only_snmpget(self, snmp_query: SnmpQuery, snmpd_location: str, mdb_handler: MongodbHandler) -> bool:
        '''handles the case of command=READONLY'''
        '''we will call readable function, if it works then we will try to set, if it sets then failed, if not then success'''
        result = self.snmpget(snmp_query=snmp_query, snmpd_location=snmpd_location)
        if result is False:
            return False
        result = self.snmpset(snmp_query=snmp_query, snmpd_location=snmpd_location)
        return not result

    def send_snmpset(self, snmp_conf: SnmpConfiguration ,snmp_query: SnmpQuery, snmpd_location: str, mdb_handler: MongodbHandler) -> bool:
        '''snmp_set of easysnmp lib returns True/False, and Failed("F")/Success("S")'''
        status='S'
        name='unknown'
        # getting time stamp just before the request is sent
        request_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        try:
            mib_object = easysnmp.snmp_set(oid=snmp_query.oid, value=snmp_query.mib_value, data_type=snmp_query.mib_type,
                hostname=snmpd_location, version=snmp_conf.version, 
                security_level=snmp_conf.security_level, security_username=snmp_conf.user_name, 
                privacy_protocol=snmp_conf.privacy_protocol, privacy_password=snmp_conf.priv_pass,
                auth_protocol=snmp_conf.auth_protocol, auth_password=snmp_conf.auth_pass)
            name = mib_object.oid_index.label
        except (easysnmp.exceptions.EasySNMPTimeoutError, easysnmp.exceptions.EasySNMPConnectionError, easysnmp.exceptions.EasySNMPNoSuchObjectError, 
            easysnmp.exceptions.EasySNMPNoSuchInstanceError, easysnmp.exceptions.EasySNMPNoSuchNameError, easysnmp.exceptions.EasySNMPBadValueError) as e:
            status='F'
        # getting time stamp right after the request is sent
        response_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        # inserts both request and response to db
        self.insert_snmp_json(type='snmpRequest', method='set', destination=snmpd_location,
            oid=snmp_query.oid, name=name, time=request_time,
            status=status, mdb_handler=mdb_handler)
        self.insert_snmp_json(type='snmpResponse', method='set', destination=snmpd_location,
            oid=snmp_query.oid, name=name, time=response_time,
            status=status, mdb_handler=mdb_handler)

        if status == 'S':
            return True
        return False

    def send_snmpget(self, snmp_conf: SnmpConfiguration ,snmp_query: SnmpQuery, snmpd_location: str, mdb_handler: MongodbHandler) -> Tuple[str, str, bool]:
        '''snmp_get of easysnmp lib returns mib value, mib type, and Failed("F")/Success("S")'''
        status='S'
        name='unknown'
        # getting time stamp just before the request is sent
        request_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        try:
            mib_object = easysnmp.snmp_get(oid=snmp_query.oid, hostname=snmpd_location, version=snmp_conf.version, 
                security_level=snmp_conf.security_level, security_username=snmp_conf.user_name, 
                privacy_protocol=snmp_conf.privacy_protocol, privacy_password=snmp_conf.priv_pass,
                auth_protocol=snmp_conf.auth_protocol, auth_password=snmp_conf.auth_pass)
            name = mib_object.oid_index.label
        except (easysnmp.exceptions.EasySNMPTimeoutError, easysnmp.exceptions.EasySNMPConnectionError, easysnmp.exceptions.EasySNMPNoSuchObjectError, 
            easysnmp.exceptions.EasySNMPNoSuchInstanceError, easysnmp.exceptions.EasySNMPNoSuchNameError, easysnmp.exceptions.EasySNMPBadValueError) as e:
            status='F'
        # getting time stamp right after the request is sent
        response_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        # inserts both request and response to db
        self.insert_snmp_json(type='snmpRequest', method='get', destination=snmpd_location,
            oid=snmp_query.oid, name=name, time=request_time,
            status=status, mdb_handler=mdb_handler)
        self.insert_snmp_json(type='snmpResponse', method='get', destination=snmpd_location,
            oid=snmp_query.oid, name=name, time=response_time,
            status=status, mdb_handler=mdb_handler)

        if status == 'S':
            return mib_object.value, mib_object.snmp_type, True
        return mib_object.value, mib_object.snmp_type, False
        
