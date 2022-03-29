from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable
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
            self.logger.error('file {} cannot be parsed. error message -> {}'.format(file, e.get_message()))
        self.test_files.append(test_file)


class TestParser(ABC):
    @abstractmethod
    def __init__(self, my_keyword_type: str, dict_of_parser_commands: dict[str, Callable]) -> None:
        self.my_keyword_type = my_keyword_type
        # the next functions in dictionary must get 2 variables; test - Test, and rest of line - list[str]
        self.dict_of_basic_commands = {'NAME:' : self.set_test_name, \
            'TEST:' : self.parse_specific_parser_keywords}
        self.dict_of_parser_commands = dict_of_parser_commands
        #self.current_dict_of_commands = self.dict_of_basic_commands

    def parse_generic_parser_keywords(self, test: Test, line: list[str]) -> None:
        if not self.is_keyword_in_dict(dict=self.dict_of_basic_commands,
            keyword=line[0]):
            raise CannotBeParsedError('keyword {} not found '.format(''.join(line[0])))  
        # select the right keyword for the first word in line, then pass the rest of the line to function
        self.dict_of_basic_commands[line[0]](line[:1])

    def parse_specific_parser_keywords(self, test: Test, line: list[str]) -> None:
        while len(line):
            if self.is_keyword_in_dict(dict=self.dict_of_parser_commands,
                keyword=line[0]):
                raise CannotBeParsedError('keyword {} not found '.format(''.join(line[0])))
            # select the right keyword for the first word in line, then pass the rest of the line to function
            self.dict_of_parser_commands[line[0]](test=test,
                line=line)

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
        # the next functions in dictionary must get 2 variables; test - Test, and rest of line - list[str]
        dict_of_parser_commands = {'SIGNAL' : self.set_signal,
            'TO_INCLUDE' : self.set_to_include,
            'TO_NOT_INCLUDE' : self.set_to_not_include}
        super().__init__(my_keyword_type='DLEP', 
            dict_of_parser_commands=dict_of_parser_commands)
        parsers_dict[self.my_keyword_type] = self      

    def set_signal(self, test: Test, line: list[str]) -> None:
        # first word in list contains the 'SIGNAL' keyword, then the signal itself
        test.set_signal(signal=line[1])
        # removing the 'SIGNAL' keyword and the signal itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_to_include(self, test: Test, line: list[str]) -> None:
        # first word in list contains the 'TO_INCLUDE' keyword, then 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, then the item/subdataitem to include
        test.set_include(is_need_to_include='include', item=line[2])
        # removing the 'TO_INCLUDE' keyword, the 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, and the item/subdataitem that need to be include
        self.cut_next_words(word_list=line, num_of_words=3)

    def set_to_not_include(self, test: Test, line: list[str]) -> None:
        # first word in list contains the 'TO_NOT_INCLUDE' keyword, then 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, then the item/subdataitem to not include
        test.set_include(is_need_to_include='not include', item=line[1])
        # removing the 'TO_NOT_INCLUDE' keyword, the 'DATA_ITEM'/'SUB_DATA_ITEM' keyword, and the item/subdataitem that need to not be include
        self.cut_next_words(word_list=line, num_of_words=3)

class SnmpTestParser(TestParser):
    def __init__(self, parsers_dict : dict[str, TestParser]) -> None:
        # the next functions in dictionary must get 2 variables; test - Test, and rest of line - list[str]
        dict_of_parser_commands = {'OID' : self.set_oid,
            'TO_BE' : self.set_to_be,
            'OF_TYPE' : self.set_mib_type,
            'WITH_VALUE' : self.set_mib_value}
        super().__init__(my_keyword_type='SNMP',
            dict_of_parser_commands=dict_of_parser_commands)
        parsers_dict[self.my_keyword_type] = self

    def set_oid(self, test: Test, line: list[str]) -> None:
        # first word in list contains the 'OID' keyword, then the oid itself
        test.set_oid(signal=line[1])
        # removing the 'OID' keyword and the oid itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_to_be(self, test: Test, line: list[str]) -> None:
        # first word in list contains the 'TO_BE' keyword, then the readonly/settable
        test.set_to_be(signal=line[1])
        # removing the 'TO_BE' keyword and the readonly/settable
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_mib_type(self, test: Test, line: list[str]) -> None:
        # first word in list contains the 'OF_TYPE' keyword, then the type itself
        test.set_mib_type(signal=line[1])
        # removing the 'OF_TYPE' keyword and the type itself
        self.cut_next_words(word_list=line, num_of_words=2)

    def set_mib_value(self, test: Test, line: list[str]) -> None:
        # first word in list contains the 'WITH_VALUE' keyword, then the value expression itself
        test.set_mib_value(signal=line[1])
        # removing the 'WITH_VALUE' keyword and the value expression itself
        self.cut_next_words(word_list=line, num_of_words=2)