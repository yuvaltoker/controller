# for event handling
from waiting import wait

# for background waiting function, use multiproccecing
from multiprocessing import Process, Value, Manager, Queue

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


rmq_handler = RabbitmqHandler()
mdb_handler = MongodbHandler()
manager = Manager()
flags = manager.dict()
queue = Queue(-1)

def app_listener_configurer():
    root = logging.getLogger()
    h = handlers.RotatingFileHandler('apptest.log', 'a', 300, 10)
    f = logging.Formatter('%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s')
    h.setFormatter(f)
    root.addHandler(h)

# This is the listener process top-level loop: wait for logging events
# (LogRecords)on the queue and handle them, quit when you get a None for a
# LogRecord.
def app_listener_process(queue, configurer):
    configurer()
    while True:
        try:
            record = queue.get()
            if record is None:  # We send this as a sentinel to tell the listener to quit.
                break
            logger = logging.getLogger()
            if record['level'] is 'debug':
                logger.debug(record['message'])
            if record['level'] is 'info':
                logger.info(record['message'])
            if record['level'] is 'warning':
                logger.warning(record['message'])
            if record['level'] is 'error':
                logger.error(record['message'])
            if record['level'] is 'critical':
                logger.critical(record['message'])
        except Exception:
            import sys, traceback
            #print('Whoops! Problem:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def can_i_start_running():
    #print('app: tests_list_ready flag - {0}'.format(flags[1]['tests_list_ready']))
    message = 'app: tests_list_ready flag - {0}'.format(flags[1]['tests_list_ready'])
    queue.put({'level' : 'debug', 'message' : message})
    return flags[1]['tests_list_ready'] and flags[1]['device_ids_ready']

def are_all_results_ready():
    return flags[1]['all_results_ready']

def is_pdf_ready():
    #print('app: pdf_ready flag - {0}'.format(flags[1]['pdf_ready']))
    message = 'app: pdf_ready flag - {0}'.format(flags[1]['pdf_ready'])
    queue.put({'level' : 'debug', 'message' : message})
    return flags[1]['pdf_ready']

def create_setup():
    #print('app: creating setup...')
    message = 'app: creating setup...'
    queue.put({'level' : 'info', 'message' : message})
    time.sleep(1)
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

    #print('app: sending set up ready')
    message = 'app: sending set up ready'
    queue.put({'level' : 'info', 'message' : message})
    rmq_handler.send('', 'setup_ready', str(uid))   

# creating an event handler for when getting a message when test list ready and got devices
def before_running_event_handler():
    #print('app: im waiting for test list and devices ready')
    message = 'app: im waiting for test list and devices ready'
    queue.put({'level' : 'info', 'message' : message})
    tests_list_ready_listener = Process(target=rmq_handler.wait_for_message, args=('tests_list', flags, queue))

    # device_ids__ready_listener = Process(target=rmq_handler.wait_for_message, args=('device_ids', flags, queue))

    tests_list_ready_listener.start()
    # device_ids__ready_listener.start()
    wait(lambda: can_i_start_running(), timeout_seconds=120, waiting_for="test list and device list to be ready")
    time.sleep(3)
    tests_list_ready_listener.terminate()
    # device_ids__ready_listener.terminate()

def results_event_handler():
    #print('app: im waiting for results ready')
    message = 'app: im waiting for results ready'
    queue.put({'level' : 'info', 'message' : message})
    results_listener = Process(target=rmq_handler.wait_for_message, args=('results', flags, queue))
    all_results_ready_listener = Process(target=rmq_handler.wait_for_message, args=('all_results_ready', flags, queue))

    results_listener.start()
    all_results_ready_listener.start()
    wait(lambda: are_all_results_ready(), timeout_seconds=120, waiting_for="all results to be ready")
    time.sleep(3)
    results_listener.terminate()
    all_results_ready_listener.terminate()

def getting_pdf_event_handler():
    #print('app: im waiting for pdf ready')
    message = 'app: im waiting for pdf ready'
    queue.put({'level' : 'info', 'message' : message})
    pdf_ready_listener = Process(target=rmq_handler.wait_for_message, args=('pdf_ready', flags, queue))

    pdf_ready_listener.start()
    wait(lambda: is_pdf_ready(), timeout_seconds=120, waiting_for="pdf to be ready")
    time.sleep(3)
    pdf_ready_listener.terminate()


def app_flow():
    before_running_event_handler()
    create_setup()
    results_event_handler()
    getting_pdf_event_handler()
    print('app: controller thanks for everything, you may need to think of another name though')
    # the next line ends the process listener
    queue.put_nowait(None)

if __name__ == '__main__':
    flags[1] = {'tests_list_ready' : False, 'device_ids_ready' : True, 'all_results_ready' : False, 'pdf_ready' : False}

    listener = Process(target=app_listener_process,
                                       args=(queue, app_listener_configurer))
    listener.start()

    app_flow()
