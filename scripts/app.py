# for event handling
from waiting import wait

# for background waiting function, use multiproccecing
from multiprocessing import Process, Manager

# for using a shared memory variables
import ctypes

import logging
from logging import handlers

# for easy use of rabbitmq
from rabbitmq_handler import RabbitmqHandler
# for easy read/write on mongodb
from mongodb_handler import MongodbHandler

from json import dumps, loads

import time


logging_file = None
logging_level = logging.DEBUG
rmq_handler = RabbitmqHandler(logging_level)
mdb_handler = MongodbHandler()
manager = Manager()
flags = manager.dict()

# for logging
logger = logging.getLogger('app')

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

def can_i_start_running():
    message = 'app: tests_list_ready flag - %s' % flags[1]['tests_list_ready']
    logger.debug(message)
    return (flags[1]['tests_list_ready'] and flags[1]['device_ids_ready'])

def are_all_results_ready():
    return flags[1]['all_results_ready']

def is_pdf_ready():
    message = 'app: pdf_ready flag - {0}'.format(flags[1]['pdf_ready'])
    logger.debug(message)
    return flags[1]['pdf_ready']

def create_setup():
    message = 'app: creating setup...'
    logger.info(message)
    #time.sleep(1)
    json_document_setup_example = '''{
	    "ConfigType": "TestConfig",
	    "RadioType": "NNN",
	    "TesterName": "John Doe",
	    "TestReason": "New version release",
	    "SelectedDevice": "<uid>",
	    "TimeStamp": "26-04-2021 14:15:16.297",
	    "SuitesToRun": [
	    	"dlep/dlep-8175.tdf",
	    	"dlep/dlep-8703.tdf"
	    ]
    }
    '''
    uid = mdb_handler.insert_document('Configuration', loads(json_document_setup_example))
    message = 'app: sending set up ready'
    logger.info(message)
    rmq_handler.send('', 'setup_ready', str(uid))   

# creating an event handler for when getting a message when test list ready and got devices
def before_running_event_handler():

    message = 'app: im waiting for test list and devices ready'
    logger.info(message)
    tests_list_ready_listener = Process(target=rmq_handler.wait_for_message, args=('tests_list', flags,))
    #device_ids__ready_listener = Process(target=rmq_handler.wait_for_message, args=('device_ids', flags,))

    tests_list_ready_listener.start()
    #device_ids__ready_listener.start()
    wait(lambda: can_i_start_running(), timeout_seconds=120, waiting_for="test list and device list to be ready")
    #time.sleep(3)
    tests_list_ready_listener.terminate()
    #device_ids__ready_listener.terminate()

def results_event_handler():
    message = 'app: im waiting for results ready'
    logger.info(message)
    results_listener = Process(target=rmq_handler.wait_for_message, args=('results', flags,))
    all_results_ready_listener = Process(target=rmq_handler.wait_for_message, args=('all_results_ready', flags,))

    results_listener.start()
    all_results_ready_listener.start()
    wait(lambda: are_all_results_ready(), timeout_seconds=120, waiting_for="all results to be ready")
    #time.sleep(3)
    results_listener.terminate()
    all_results_ready_listener.terminate()

def getting_pdf_event_handler():
    message = 'app: im waiting for pdf ready'
    logger.info(message)
    pdf_ready_listener = Process(target=rmq_handler.wait_for_message, args=('pdf_ready', flags,))

    pdf_ready_listener.start()
    wait(lambda: is_pdf_ready(), timeout_seconds=120, waiting_for="pdf to be ready")
    #time.sleep(3)
    pdf_ready_listener.terminate()


def app_flow():
    before_running_event_handler()
    create_setup()
    results_event_handler()
    getting_pdf_event_handler()
    print('app: controller thanks for everything, you may need to think of another name though')

if __name__ == '__main__':
    flags[1] = {'tests_list_ready' : False, 'device_ids_ready' : True, 'all_results_ready' : False, 'pdf_ready' : False}

    configure_logger_logging(logging_level)

    app_flow()
