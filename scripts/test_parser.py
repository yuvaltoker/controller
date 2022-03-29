from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from tests import TestFile, Test
import logging

class CannotBeParsedError(Exception):
    """Custom error which raised when a test/file cannot be parsed"""
    def __init__(self, message: str) -> None:
        self.message = message
        super.__init__(message)

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

    def file_to_lines(self, file: str) -> list[str]:
        with open(file, 'r') as file:
            file_lines = file.readlines()
            file_lines = [line.rstrip() for line in file_lines]
        return file_lines

    def parse_files(self, files: list[str]) -> None:
        for file in files:
            self.parse_file(file)

    def parse_test(self, test_file: TestFile, current_test_lines: list[list[str]]) -> None:
        '''parse test by given lines, in case of success, add the test into test_file's list of tests'''
        line = current_test_lines[0]
        if line[0] != 'TYPE:':
            raise CannotBeParsedError('expected TYPE command, instead got  {}'.format(' '.join(line[0])))
        # expect type
        type = line[1]
        # @create_test function in @TestFile returns a tuple[bool, Test]
        has_created, test = test_file.create_test(test_type=type)
        if not has_created:
            raise CannotBeParsedError('TYPE value {} not found in tests type'.format(' '.join(type)))
        # if type is not in self.dict_test_parser
        if not type in self.dict_test_parsers:
            raise CannotBeParsedError('TYPE value {} not found in test parser dict'.format(' '.join(type)))
        current_test_lines[:] = current_test_lines[:1]
        # test parser should get @Test and list of lines (list[list[str]]) containing 2 lines, the 2nd and 3rd lines
        parser = self.dict_test_parsers[type](test, current_test_lines)
        # parsing the test
        test = parser.parse_test(test=test, lines_to_parse=current_test_lines)
        # checking successful parsing, in case of failure an exception will be raised
        if test.check_if_test_ready():
            # add the current test into list of tests
            test_file.add_test(test)
        
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
            self.logger.error('file {} cannot be parsed. error message -> {}'.format(file, e.get_message()))
        self.test_files.append(test_file)

@dataclass
class ParsingTestStates(Enum):
    """Represents the state of test parsing"""
    STAGE_TYPE = auto()
    STAGE_NAME = auto()
    STAGE_TEST = auto()


class TestParser(ABC):
    @abstractproperty
    def dict_of_parser_commands(self) -> dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def __init__(self, my_keyword_type: str) -> None:
        self.my_keyword_type = my_keyword_type
        # the next functions in dictionary must get 2 variables; test - Test, and rest of line - list[str]
        self.dict_of_basic_commands = {'NAME:' : self.set_test_name, \
            'TEST:' : self.parse_my_own_keywords}
        self.current_parsing_state = ParsingTestStates.STAGE_NAME
        #self.current_dict_of_commands = self.dict_of_basic_commands

    def parse_basic_keywords(self, test: Test, line: list[str]) -> None:
        if not self.is_keyword_in_dict(dict=self.dict_of_basic_commands,
            keyword=line[0]):
            raise CannotBeParsedError('keyword {} not found '.format(''.join(line[0])))  
        # select the right keyword for the first word in line, then pass the rest of the line to function
        self.dict_of_basic_commands[line[0]](line[:1])

    # this function is being called by TestFilesParser for each TEST_LINES_LENGTH lines from a file
    def parse_test(self, test: Test, lines_to_parse: list[list[str]]) -> None:
        for index, line in enumerate(lines_to_parse):
            # example, length is 3, TYPE line got reduced, so we've got 2 lines by now, so the max index should be 1
            if index >= TEST_LINES_LENGTH - 1:
                raise CannotBeParsedError('cannot parse test with more than {} lines'.format(' '.join(TEST_LINES_LENGTH)))
            # calling the 'parse line' function fro each line
            self.parse_basic_keywords(test=test, line=line)

    def set_test_name(self,test: Test, name: list[str]) -> None:
        test.set_name(name=' '.join(name))
        self.current_parsing_state = ParsingTestStates.STAGE_TEST

    @abstractmethod
    def parse_my_own_keywords(self, test: Test, lines_to_parse: list[str]) -> None:
        raise NotImplementedError()
        
    def is_keyword_in_dict(self, dict: dict[str, Any], keyword: str) -> bool:
        return keyword in dict

    def cut_next_words(self, word_list, num_of_words) -> None:
        after_cutting = word_list[num_of_words:]
        if after_cutting == ['']:
            word_list[:] = []
        else:
            word_list[:] = after_cutting


class DlepTestParser(TestParser):
    def __init__(self, parsers_dict : dict[str, TestParser]) -> None:
        super().__init__('DLEP')
        parsers_dict[self.my_keyword_type] = self
        # the next functions in dictionary must get 2 variables; test - Test, and rest of line - list[str]
        self.dict_of_parser_commands = {'SIGNAL' : self.set_signal,
            'TO_INCLUDE' : self.set_to_include,
            'TO_NOT_INCLUDE' : self.set_to_not_include}

    def parse_my_own_keywords(self, test: Test, line: list[str]) -> None:
        while len(line):
            if self.is_keyword_in_dict(dict=self.dict_of_parser_commands,
                keyword=line[0]):
                raise CannotBeParsedError('keyword {} not found '.format(''.join(line[0])))
            # select the right keyword for the first word in line, then pass the rest of the line to function
            self.dict_of_parser_commands[line[0]](test=test,
                line=line)

    def set_signal(self, test, line: list[str]) -> None:
        # first word in list contains the 'SIGNAL' keyword, then the signal itself
        test.set_signal(signal=line[1])
        # removing the 'SIGNAL' keyword and the signal itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_to_include(self, test, line: list[str]) -> None:
        # first word in list contains the 'TO_INCLUDE' keyword, then the item to include
        test.set_include(is_need_to_include='include', item=line[1])
        # removing the 'TO_INCLUDE' keyword and the item that need to be include
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_to_not_include(self, test, line: list[str]) -> None:
        # first word in list contains the 'TO_NOT_INCLUDE' keyword, then the item to include
        test.set_include(is_need_to_include='not include', item=line[1])
        # removing the 'TO_NOT_INCLUDE' keyword and the item that need to not be include
        self.cut_next_words(word_list=line, num_of_words=2)

class SnmpTestParser(TestParser):
    def __init__(self, parsers_dict : dict[str, TestParser]) -> None:
        super().__init__('SNMP')
        parsers_dict[self.my_keyword_type] = self
        self.dict_of_parser_commands = {'OID' : self.set_oid,
            'TO_BE' : self.set_to_be,
            'OF_TYPE' : self.set_mib_type,
            'WITH_VALUE' : self.set_mib_value}

    def parse_my_own_keywords(self, test: Test, line: list[str]) -> None:
        pass

'''
class TestFilesParser:
    def __init__(self, logging_level, logging_file = None):

        self.dict_of_parsers = {'DLEP' : DlepTestParser, 'SNMP' : SnmpTestParser}
        self.current_parser = None
        self.dict_of_basic_commands = {'TYPE:' : self.set_test_type, \
                                    'NAME:' : self.set_test_name, \
                                    'TEST:' : self.start_reading_test}
        self.dict_of_test_type = {'DLEP' : self.create_dlep_test, \
                                'SNMP' : self.create_snmp_test}
        
        
        self.dict_of_states = {'TYPE' : False, 'NAME' : False, 'TEST' : False}
        self.current_dict_of_commands = self.dict_of_basic_commands
        self.current_test_type = ''
        self.test_files = []
        # logging
        logger = logging.getLogger('test_parser')
        configure_logger_logging(logger, logging_level, logging_file)
        self.logger = logger

    def get_test_files(self):
        return self.test_files

    def reset_dict_of_states(self):
        self.dict_of_states['TYPE'] = False
        self.dict_of_states['NAME'] = False
        self.dict_of_states['TEST'] = False

    def file_to_lines(self, file):
        with open(file, 'r') as file:
            file_lines = file.readlines()
            file_lines = [line.rstrip() for line in file_lines]
        return file_lines

    def parse_files(self, files):
        for file in files:
            self.parse_file(file)
            self.reset_dict_of_states()

    def parse_file(self, file):
        file_lines = self.file_to_lines(file)
        test_file = TestFile(file)
        try:
            for line in file_lines:
                # ignores empty lines
                if line == '':
                    continue
                word_list = line.split(' ')
                # removing all the '' in the list, it'll raise an exception when '' will not be exist anymore
                try:
                    word_list = [word for word in word_list if word != '']
                except:
                    pass
                # while there is at least 1 word in line
                while len(word_list) and word_list[0] != '':  
                    # this function can raise an exception
                    self.cut_and_parse_into_variables(test_file, word_list)
                if test_file.check_if_current_test_ready():
                    # add the current test into list of tests
                    test_file.add_test()
                    # reset the dictionary of states for the next tests
                    self.reset_dict_of_states()
                # if we've already read the TEST line, but the test is not ready, it means the test failed to be parsed, thus we don't want the file
                elif self.dict_of_states['TEST'] is True:
                    raise CannotBeParsedError('could not parse one of {} tests'.format(test_file.get_file_name()))
                    
            if test_file.has_dlep_tests() or test_file.has_snmp_tests():
                self.test_files.append(test_file)
                tests_jsons = test_file.get_tests_jsons()
                self.logger.info('File {} tests:'.format(test_file.get_file_name()))
                for test_json in tests_jsons:
                    self.logger.info(test_json)
        except CannotBeParsedError as e:
            self.logger.error('file {} cannot be parsed. error message -> {}'.format(file, e.get_message()))
            self.reset_dict_of_states()

    def cut_and_parse_into_variables(self, test_file, word_list):
        if word_list[0] in self.current_dict_of_commands:
            self.call_fuction_by_list(test_file, word_list)
        elif word_list[0] in self.current_parser.dict_of_parser_commands:
            self.call_fuction_by_list(test_file, word_list)
        elif word_list[0] == 'TYPE:':
            # in case we started a new test
            self.current_dict_of_commands = self.dict_of_basic_commands
            self.call_fuction_by_list(test_file, word_list)
        else:
            raise CannotBeParsedError('cannot find a command for -> {}'.format(' '.join(word_list[0])))

    def call_fuction_by_list(self, test_file, word_list):
        function_to_call = word_list[0]
        # the first word's cutting happens here, word_list[1:]
        self.cut_next_words(word_list, 1)
        # call to function by the given key-word 
        if self.current_parser is None:
            self.current_dict_of_commands[function_to_call](test_file, word_list)
        else:
            self.current_parser

    # returns a dict of files which succeeded the parsing as {'dlep' : [path1,path2,...], 'snmp' : [path1,path2,...]}
    def get_test_files_after_parsing(self):
        all_tests_files = {}
        found_dlep = False
        found_snmp = False
        for test_file in self.test_files:
            if test_file.has_dlep_tests():
                if not found_dlep:
                    all_tests_files['dlep'] = []
                    found_dlep = True
                all_tests_files['dlep'].append(test_file.get_file_name())
                
            if test_file.has_snmp_tests():
                if not found_snmp:
                    all_tests_files['snmp'] = []
                    found_snmp = True
                all_tests_files['snmp'].append(test_file.get_file_name())
        return all_tests_files
            

    #############################
    # basic commands' functions #
    #############################
    
    # after calling 'TYPE:'
    def set_test_type(self, test_file, word_list):
        # redirect the list of commands to read from dictionary of test type
        self.dict_of_states['TYPE'] = True
        self.current_parser = self.dict_of_parsers[word_list[0]]
        cut_next_words(word_list, 1)
        self.current_dict_of_commands = self.current_parser.dict_of_parser_commands()
        # there is not another cutting here, the next time cut_and_parse_into_variables will be called
        # it will call to the right function from the parser.sict_of_parser_commands

    

    # create snmp test as type says 'SNMP'
    def create_snmp_test(self, test_file, word_list):
        test_file.create_snmp_test(word_list)
        self.current_dict_of_commands = self.dict_of_basic_commands
        self.current_test_type = 'SNMP'

    # sets name of current test as the words after 'NAME:' says
    def set_test_name(self, test_file, word_list):
        self.dict_of_states['NAME'] = True
        test_file.set_test_name(' '.join(word_list))
        word_list[:] = []

    # after calling 'TEST:'
    def start_reading_test(self, test_file, word_list):
        self.dict_of_states['TEST'] = True
        # cutting the 'EXPECT' part
        self.cut_next_words(word_list, 1)
        # changing dictionary of commands into the correct one
        if self.current_test_type == 'DLEP':
            self.current_dict_of_commands = self.dict_of_dlep_commands
        elif self.current_test_type == 'SNMP':
            self.current_dict_of_commands = self.dict_of_snmp_commands



'''
'''
class DlepTestParser:
    # create dlep test as type says 'DLEP'
    def create_dlep_test(test_file, word_list):
        test_file.create_dlep_test(word_list)
        current_dict_of_commands = dict_of_basic_commands
        current_test_type = 'DLEP'

    # returns the number of words which should be cut before the next calling function
    def set_signal(test_file, word_list):
        # next string should be signal
        test_file.set_signal(word_list[0])
        # cut the used signal which was already saved
        return 1

    # returns the number of words which should be cut before the next calling function
    def set_to_include(test_file, word_list):
        # set test to include, than what to include? (next string should be DATA_ITEM or SUB_DATA_ITEM and then the item itself)
        test_file.set_include('To include', word_list[1])
        # cut the used item which was already saved
        return 2

    # returns the number of words which should be cut before the next calling function
    def set_to_not_include(self, test_file, word_list):
        # set test to not include, than what to include? (next string should be DATA_ITEM or SUB_DATA_ITEM and then the item itself)
        test_file.set_include('To not include', word_list[1])
        # cut the used item which was already saved
        return 2

    # static variables:
    dict_of_parser_commands = {'SIGNAL' : set_signal, 'TO_INCLUDE' : set_to_include, 'TO_NOT_INCLUDE' : set_to_not_include}


class SnmpTestParser:
    # returns the number of words which should be cut before the next calling function
    def set_oid(self, test_file, word_list):
        # next string should be oid
        test_file.set_oid(word_list[0])
        # cut the used oid which was already saved
        cut_next_words(word_list, 1)

    def set_to_be(self, test_file, word_list):
        # next string should be READONLY/SETTABLE
        test_file.set_to_be(word_list[0])
        # cut the used READONLY/SETTABLE which was already saved
        cut_next_words(word_list, 1)

    def set_mib_type(self, test_file, word_list):
        # next string should be INTEGER/OCTET_STRING
        test_file.set_mib_type(word_list[0])
        # cut the used INTEGER/OCTET_STRING which was already saved
        cut_next_words(word_list, 1)

    def set_mib_value(self, test_file, word_list):
        # next string should be the value we're suppose to expect
        test_file.set_mib_value(word_list[0])
        # cut the used value which was already saved
        cut_next_words(word_list, 1)

    # static variables:
    dict_of_parser_commands = {'OID' : set_oid, 'TO_BE' : set_to_be, 'OF_TYPE' : set_mib_type, 'WITH_VALUE' : set_mib_value}
'''