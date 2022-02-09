
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

    def get_message(self):
        return self.message

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
        self.dict_of_basic_commands = {'TYPE:' : self.set_test_type, \
                                    'NAME:' : self.set_test_name, \
                                    'TEST:' : self.start_reading_test}
        self.dict_of_test_type = {'DLEP' : self.create_dlep_test, \
                                'SNMP' : self.create_snmp_test}
        self.dict_of_dlep_commands = {'SIGNAL' : self.set_signal, 'TO_INCLUDE' : self.set_to_include, 'TO_NOT_INCLUDE' : self.set_to_not_include}
        self.dict_of_snmp_commands = {'OID' : self.set_oid, 'TO_BE' : self.set_to_be, 'OF_TYPE' : self.set_mib_type, 'WITH_VALUE' : self.set_mib_value}
        self.current_dict_of_commands = self.dict_of_basic_commands
        self.current_test_type = ''
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
                # removing all the '' in the list, it'll raise an exception when '' will not be exist anymore
                try:
                    word_list = [word for word in word_list if word != '']
                except:
                    pass
                self.logger.debug(word_list)
                # while there is at least 1 word in line
                while len(word_list) and word_list[0] != '':  
                    # this function can raise an exception
                    self.logger.debug(word_list)
                    self.cut_and_parse_into_variables(test_file, word_list)
                if test_file.check_if_current_test_ready():
                    # add the current test into list of tests
                    test_file.add_test()
                    
            self.test_files.append(test_file)
            tests_jsons = test_file.get_tests_jsons()
            for test_json in tests_jsons:
                self.logger.info(test_json)
        except CannotBeParsedError as e:
            self.logger.warning('file {} cannot be parsed. error message -> {}'.format(file, e.get_message()))

    
    def cut_and_parse_into_variables(self, test_file, word_list):
        if word_list[0] in self.current_dict_of_commands:
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
        #word_list[:] = word_list[1:]
        self.cut_next_words(word_list, 1)
        # call to function by the given key-word 
        self.current_dict_of_commands[function_to_call](test_file, word_list)

    def cut_next_words(self, word_list, num_of_words):
        after_cutting = word_list[num_of_words:]
        if after_cutting == ['']:
            word_list[:] = []
        else:
            word_list[:] = after_cutting

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
                all_tests_files['dlep'].append(test_file)
                
            if test_file.has_snmp_tests():
                if not found_snmp:
                    all_tests_files['snmp'] = []
                    found_snmp = True
                all_tests_files['snmp'].append(test_file)
        return all_tests_files
            

    #############################
    # basic commands' functions #
    #############################
    
    # after calling 'TYPE:'
    def set_test_type(self, test_file, word_list):
        # redirect the list of commands to read from dictionary of test type
        self.current_dict_of_commands = self.dict_of_test_type
        # there is not another cutting here, the next time cut_and_parse_into_variables will be called
        # it will call to the right function from the self.dict_of_test_type

    # create dlep test as type says 'DLEP'
    def create_dlep_test(self, test_file, word_list):
        test_file.create_dlep_test(word_list)
        self.current_dict_of_commands = self.dict_of_basic_commands
        self.current_test_type = 'DLEP'

    # create snmp test as type says 'SNMP'
    def create_snmp_test(self, test_file, word_list):
        test_file.create_snmp_test(word_list)
        self.current_dict_of_commands = self.dict_of_basic_commands
        self.current_test_type = 'SNMP'

    # sets name of current test as the words after 'NAME:' says
    def set_test_name(self, test_file, word_list):
        test_file.set_test_name(' '.join(word_list))
        word_list[:] = []

    # after calling 'TEST:'
    def start_reading_test(self, test_file, word_list):
        # cutting the 'EXPECT' part
        self.cut_next_words(word_list, 1)
        # changing dictionary of commands into the correct one
        if self.current_test_type == 'DLEP':
            self.current_dict_of_commands = self.dict_of_dlep_commands
        elif self.current_test_type == 'SNMP':
            self.current_dict_of_commands = self.dict_of_snmp_commands

    ############################
    # dlep commands' functions #
    ############################

    def set_signal(self, test_file, word_list):
        # next string should be signal
        test_file.set_signal(word_list[0])
        # cut the used signal which was already saved
        self.cut_next_words(word_list, 1)

    def set_to_include(self, test_file, word_list):
        # set test to include, than what to include? (next string should be DATA_ITEM or SUB_DATA_ITEM and then the item itself)
        test_file.set_include('To include', word_list[1])
        # cut the used item which was already saved
        self.cut_next_words(word_list, 2)

    def set_to_not_include(self, test_file, word_list):
        # set test to not include, than what to include? (next string should be DATA_ITEM or SUB_DATA_ITEM and then the item itself)
        test_file.set_include('To not include', word_list[1])
        # cut the used item which was already saved
        self.cut_next_words(word_list, 2)

    ############################
    # snmp commands' functions #
    ############################

    def set_oid(self, test_file, word_list):
        # next string should be oid
        test_file.set_oid(word_list[0])
        # cut the used oid which was already saved
        self.cut_next_words(word_list, 1)

    def set_to_be(self, test_file, word_list):
        # next string should be READONLY/SETTABLE
        test_file.set_to_be(word_list[0])
        # cut the used READONLY/SETTABLE which was already saved
        self.cut_next_words(word_list, 1)

    def set_mib_type(self, test_file, word_list):
        # next string should be INTEGER/OCTET_STRING
        test_file.set_mib_type(word_list[0])
        # cut the used INTEGER/OCTET_STRING which was already saved
        self.cut_next_words(word_list, 1)

    def set_mib_value(self, test_file, word_list):
        # next string should be the value we're suppose to expect
        test_file.set_mib_value(word_list[0])
        # cut the used value which was already saved
        self.cut_next_words(word_list, 1)


