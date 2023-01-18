#######################################
#               Imports               #
#######################################

import logging
from typing import Any, Dict, List
# for easy use of rabbitmq
from rabbitmq_handler import RabbitmqHandler
# for easy read/write on mongodb
from mongodb_handler import MongodbHandler
from json import dumps, loads
# for event handling
from waiting import wait
# for more convenient storing dictionaries
from pandas import DataFrame
# for background waiting function, use multiproccessing
from multiprocessing import Process, Manager
# for testing with TestFilesParser
from test_agent_lib import TestFilesHandler
# for reading files from path
import glob
# for delay use
import time
# for environment variables
import os

##################################
#              Code              #
##################################

logging_file = None
logging_level = logging.INFO
rmq_handler = RabbitmqHandler(logging_level)
mdb_handler = MongodbHandler()
manager = Manager()
flags = manager.dict()
TIME_DELAY = int(os.getenv('TIME_DELAY'))

# for logging
logger = logging.getLogger('ctrl')

def configure_logger_logging(logging_level: int) -> None:
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

def get_files_to_list(path: str) -> List[str]:
    return glob.glob(path)   

# create the next list from /tests/ path:
# [path1, path2, path3, ..., pathN]
# doing that by:
# stage 1: create list of all folders ['/tests/snmp', '/tests/snmp']
# stage 2: create a list of all the files in those paths, that means all the /tests/**/*.tdf
def create_basic_files_list(path: str) -> List[str]:
    # stage 1
    folders = get_files_to_list(path)
    paths = []
    # stage 2
    for folder in folders:
        paths.extend(get_files_to_list(folder + '/*.tdf'))
    return paths

# gets {'dlep' : [path1,path2,...], 'snmp' : [path1,path2,...]}
# creates available_test_suites_json
# returns available_test_suites_json
def create_available_test_suites_json(json_paths: Dict[str, List[str]]) -> Dict[str, Any]:
    test_suites = []
    for key, val in json_paths.items():
        test_suite = {}
        test_suite['Name'] = key
        test_suite['Tests Files'] = val

        # insert() takes 2 arguments, so in order to insert to the end, we'll give position as the end of the list
        test_suites.insert(len(test_suites), test_suite)
    available_test_suites = {'ConfigType' : 'AvailableTestSuites', 'TestSuites' : test_suites}
    return available_test_suites

# first function to be called
# this function handles reading test files and parsing them, inserts @available_test_suites to mongoDB and sends over rabbitmq the uid of the inserted document
# returning parsed test files list as {'path1' : [subpath1,subpath2,...], 'path2' : [subpath1,subpath2,...], ...}
def make_test_list(test_files_handler: TestFilesHandler) -> Dict[str, List[str]]:
    message = 'ctrl: test list in proggress...'
    logger.info(message)
    tests_path = '/tests/*'
    # creating list of all test files from path
    all_files = create_basic_files_list(tests_path)
    #filtering bad files
    test_files_handler.parse_files(all_files)
    # next line returns a dict of files which succeeded the parsing as {'path1' : [subpath1,subpath2,...], 'path2' : [subpath1,subpath2,...], ...}
    parsed_files_json = test_files_handler.get_test_files_arranged_by_folders()
    logger.info('parsed_files_json: {}'.format(parsed_files_json))
    available_test_suites = create_available_test_suites_json(parsed_files_json)
    # insert the json into mongoDB
    uid = mdb_handler.insert_document('Configuration', available_test_suites)  
    message = 'ctrl: test list ready'
    logger.info(message)
    # sends over rabbitmq the uid of the inserted document
    rmq_handler.send('', 'tests_list', str(uid))
    # returning full parsed @TestFile list for later use of running tests
    return parsed_files_json

def is_setup_ready() -> bool:
    message = 'ctrl: setup_ready flag - {0}'.format(flags[1]['setup_ready'])
    logger.debug(message)
    return flags[1]['setup_ready']

def is_pdfs_ready() -> bool:
    message = 'ctrl: pdfs flag - {0}'.format(flags[1]['pdfs_ready'])
    logger.debug(message)
    return flags[1]['pdfs_ready']

# creating an event handler - waiting for a message of setup ready
def setup_ready_event_handler() -> None:
    message = 'ctrl: im waiting for setup ready'
    logger.info(message)
    setup_ready_lisenter = Process(target=rmq_handler.wait_for_message, args=('setup_ready',flags,))

    setup_ready_lisenter.start()
    wait(lambda: is_setup_ready(), waiting_for="setup to be ready")
    setup_ready_lisenter.terminate()

def pdfs_ready_event_handler() -> str:
    message = 'ctrl: im waiting for pdfs ready'
    logger.info(message)
    pdfs_ready_lisenter = Process(target=rmq_handler.request_pdf, args=(flags,))

    pdfs_ready_lisenter.start()
    wait(lambda: is_pdfs_ready(), waiting_for="pdfs to be ready")
    pdfs_ready_lisenter.terminate()
    message = 'ctrl: got callback from report-generator'
    logger.info(message)
    return flags[1]['pdf_link']

def run_tests(test_files_handler: TestFilesHandler) -> None:
    # getting filtered document by ConfigType, then getting
    chosen_paths = mdb_handler.get_one_filtered_with_fields('Configuration', {'ConfigType': 'TestConfig'}, {})['SuitesToRun']
    logger.info(chosen_paths)
    device_id = mdb_handler.get_one_filtered_with_fields('Configuration', {'ConfigType': 'TestConfig'}, {})['SelectedDevice']
    device_ip = mdb_handler.get_one_filtered_with_fields('Devices', {'_id': device_id}, {})['ip']
    test_files_handler.execute_tests_files(mdb_handler=mdb_handler, 
        rmq_handler=rmq_handler, 
        test_files_paths=chosen_paths,
        device_ip=device_ip)
    message = 'ctrl: done running tests'
    logger.info(message)

def all_results_ready() -> None:
    message = 'ctrl: sending all results ready'
    logger.info(message)
    rmq_handler.send('', 'all_results_ready', '')
    link = pdfs_ready_event_handler()
    logger.info(link)
    time.sleep(TIME_DELAY)
    message = 'ctrl: sending pdf ready'
    logger.info(message)
    rmq_handler.send('', 'pdf_ready', link)
    
def controller_flow() -> None:
    test_files_handler = TestFilesHandler(logging_level=logging_level)
    parsed_testfile_list = make_test_list(test_files_handler=test_files_handler)
    setup_ready_event_handler()
    time.sleep(TIME_DELAY)
    run_tests(test_files_handler=test_files_handler)
    time.sleep(TIME_DELAY)
    all_results_ready()

def main() -> None:
    flags[1] = {'setup_ready' : False, 'pdfs_ready' : False, 'pdf_link' : ''}
    configure_logger_logging(logging_level=logging_level)
    controller_flow()


if __name__ == '__main__':
    main()