#######################################
#               Imports               #
#######################################

import logging
from logging import handlers

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
time_delay = int(os.getenv('TIME_DELAY'))

# for logging
logger = logging.getLogger('ctrl')

def configure_logger_logging(logging_level):
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

# first function to be called
def make_test_list():
    message = 'ctrl: test list in proggress...'
    logger.info(message)
    time.sleep(time_delay)
    json_document_test_suits_example = '''{
	"ConfigType": "AvailableTestSuites",
	"TestSuites": [
		    {
		    	"Name": "dlep",
		    	"Tests": [
		    		"dlep/dlep-8175.tdf",
		    		"dlep/dlep-8703.tdf"
		    	]
		    },
		    {
		    	"Name": "snmp",
		    	"Tests": [
		    		"snmp/battery-MIB.tdf",
		    		"snmp/network-MIB.tdf"
		    	]
		    }
	    ]
    }'''
    uid = mdb_handler.insert_document('Configuration', loads(json_document_test_suits_example))  
    message = 'ctrl: test list ready'
    logger.info(message)
    rmq_handler.send('', 'tests_list', str(uid))

def is_setup_ready():
    message = 'ctrl: setup_ready flag - {0}'.format(flags[1]['setup_ready'])
    logger.debug(message)
    return flags[1]['setup_ready']

def is_pdfs_ready():
    message = 'ctrl: pdfs flag - {0}'.format(flags[1]['pdfs_ready'])
    logger.debug(message)
    return flags[1]['pdfs_ready']

# creating an event handler - waiting for a message of setup ready
def setup_ready_event_handler():
    message = 'ctrl: im waiting for setup ready'
    logger.info(message)
    setup_ready_lisenter = Process(target=rmq_handler.wait_for_message, args=('setup_ready',flags,))

    setup_ready_lisenter.start()
    wait(lambda: is_setup_ready(), waiting_for="setup to be ready")
    setup_ready_lisenter.terminate()

def pdfs_ready_event_handler():
    message = 'ctrl: im waiting for pdfs ready'
    logger.info(message)
    pdfs_ready_lisenter = Process(target=rmq_handler.request_pdf, args=(flags,))

    pdfs_ready_lisenter.start()
    wait(lambda: is_pdfs_ready(), waiting_for="pdfs to be ready")
    pdfs_ready_lisenter.terminate()
    message = 'ctrl: got callback from report-generator'
    logger.info(message)
    return flags[1]['pdf_link']

def run_test():
    json_document_result_example = '''{
	    "name": "Check if the signal Peer_Offer includes data item Peer_Type",
	    "result": "Pass/Fail"
    }
    '''
    uid = mdb_handler.insert_document('Test Results', loads(json_document_result_example))
    return uid

def run_tests(num_of_tests):
    message = 'ctrl: im running the tests one by one'
    logger.info(message)
    for index in range(num_of_tests):
        test_uid = run_test()
        message = 'ctrl: got result - %s' % test_uid
        logger.info(message)
        rmq_handler.send('', 'results', str(test_uid))
        time.sleep(time_delay / 2)
    message = 'ctrl: done running tests'
    logger.info(message)

def all_results_ready():
    message = 'ctrl: sending all results ready'
    logger.info(message)
    rmq_handler.send('', 'all_results_ready', '')
    link = pdfs_ready_event_handler()
    logger.info(link)
    time.sleep(time_delay)
    message = 'ctrl: sending pdf ready'
    logger.info(message)
    rmq_handler.send('', 'pdf_ready', link)
    
def controller_flow():
    make_test_list()
    setup_ready_event_handler()
    time.sleep(time_delay)
    run_tests(3)
    time.sleep(time_delay)
    all_results_ready()

def main():
    flags[1] = {'setup_ready' : False, 'pdfs_ready' : False, 'pdf_link' : ''}
    configure_logger_logging(logging_level)
    controller_flow()


if __name__ == '__main__':
    main()