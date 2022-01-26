
from tests import TestFile
import logging

# define Python user-defined exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass

class CannotBeParsedError(Error):
    def __init__(self, message):
        self.message = message
        super(CannotBeParsedError, self).__init__(message)

def configure_logger_logging(logger, logging_level, logging_file):
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

class TestsParser:
    def __init__(self, logging_level, logging_file = None):
        # self.list_of_basic_commands includes the key words/signs which later help cutting the test into small pieces 
        self.dict_of_basic_commands = {'NAME:' : self.set_test_name, \
                                    'TEST:' : self.start_reading_test, \
                                    'EXPECT' : self.expect_something}
        self.dict_of_test_type = {'(DLEP)' : self.create_dlep_test, \
                                '(SNMP)' : self.create_snmp_test}
        self.dict_of_dlep_commands = {'SIGNAL', 'TO_INCLUDE', 'DATA_ITEM'}
        self.dict_of_snmp_commands = {'OID', 'TO_BE', 'SETTABLE', 'OF_TYPE', 'INTEGER', 'STRING', 'READONLY', 'WITH_VALUE'}
        self.current_dict_of_commands = self.dict_of_basic_commands
        self.tests = []
        self.test_files = []
        # logging
        logger = logging.getLogger('test_parser')
        configure_logger_logging(logger, logging_level, logging_file)
        self.logger = logger

    def file_to_lines(self, file):
        with open(file, 'r') as file:
            file_lines = file.readlines()
            file_lines = [line.rstrip() for line in file_lines]
        return file_lines

    def parse_files(self, files):
        for file in files:
            self.parse_file(file)

    def parse_file(self, file):
        file_lines = self.file_to_lines(file)
        test_file = TestFile()
        try:
            for line in file_lines:
                word_list = line.split(' ')
                self.logger.debug(word_list)
                while len(word_list):
                    # this function can raise an exception
                    self.logger.debug(word_list)
                    self.cut_and_parse_into_variables(test_file, word_list)
            self.test_files.append(test_file)
        except CannotBeParsedError as e:
            self.logger.warning('file {} cannot be parsed. error message -> {}'.format(file, e.__str__))

    
    def cut_and_parse_into_variables(self, test_file, word_list):
        if word_list[0] in self.current_dict_of_commands:
            function_to_call = word_list[0]
            # the first word's cutting happens here, word_list[1:]
            word_list[:] = word_list[1:]
            # call to function by the given key-word 
            self.current_dict_of_commands[function_to_call](test_file, word_list)
        else:
            raise CannotBeParsedError('cannot find a command for -> {}'.format(' '.join(word_list[0])))
            

    def set_test_name(self, test_file, word_list):
        if not test_file.is_name_set:
            test_file.set_name(' '.join(word_list))
        else:
            raise CannotBeParsedError('another name is given for test file {}'.format(' '.join(word_list[1:])))
        # returns empty list, cause the whole name has been read
        word_list[:] = []

    def start_reading_test(self, test_file, word_list):
        # redirect the list of commands to read from dictionary of test type
        self.current_dict_of_commands = self.dict_of_test_type
        # there is not another cutting here, the next time cut_and_parse_into_variables will be called
        # it will call to the right function from the self.dict_of_test_type

    def create_dlep_test(self, test_file, word_list):
        test_file.create_dlep_test(word_list)

    def create_snmp_test(self, test_file, word_list):
        test_file.create_snmp_test(word_list)
        

    def expect_something(self, test_file, word_list):
        self.logger.debug('im in expect_something')



