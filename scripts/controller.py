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
from multiprocessing import Process,Value,Manager,Queue

# for using a shared memory variables
import ctypes

# for delay use
import time

##################################
#              Code              #
##################################

rmq_handler = RabbitmqHandler()
mdb_handler = MongodbHandler()
manager = Manager()
flags = manager.dict()
queue = Queue(-1)

def controller_listener_configurer():
    root = logging.getLogger()
    h = handlers.RotatingFileHandler('ctrltest.log', 'a', 300, 10)
    f = logging.Formatter('%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s')
    h.setFormatter(f)
    root.addHandler(h)

# This is the listener process top-level loop: wait for logging events
# (LogRecords)on the queue and handle them, quit when you get a None for a
# LogRecord.
def controller_listener_process(queue, configurer):
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

def rabbitmq_send_msg_example():
    print('im the rabbitmq example')
    rmq_handler = RabbitmqHandler()
    print(rmq_handler.request_pdf())

def mongodb_tests():
    print('im the mongodb example')
    mdb_handler = MongodbHandler()
 
    # json_document_string = '{"item_name" : "AAB", "max_discount" : "10%", "batch_number" : "AAAAA", "price" : "900", "category" : "kitchen appliance"}'
    # json_document_string = '[{"item_name" : "AA", "max_discount" : "10%", "batch_number" : "AAAAA", "price" : "900", "category" : "kitchen appliance"},{"item_name" : "AA", "max_discount" : "10%", "batch_number" : "AAAAA", "price" : "900", "category" : "kitchen appliance"}]'
    # mdb_handler.insert_document('example_collection', loads(json_document_string))

    # collection = mdb_handler.get_collection('example_collection')
    # if collection != None:
    #     print(collection) 
    mdb_handler.print_documents(mdb_handler.get_all_documents('example_collection'))

# first function to be called
def make_test_list():
    #print('ctrl: test list in proggress...')
    message = 'ctrl: test list in proggress...'
    queue.put({'level' : 'info', 'message' : message})
    time.sleep(1)
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
    #print('ctrl: test list ready')
    message = 'ctrl: test list ready'
    queue.put({'level' : 'info', 'message' : message})
    rmq_handler.send('', 'tests_list', str(uid))

def is_setup_ready():
    # setup_ready = rmq_handler.setup_ready.value
    #print('ctrl: setup_ready flag - {0}'.format(flags[1]['setup_ready']))
    message = 'ctrl: setup_ready flag - {0}'.format(flags[1]['setup_ready'])
    queue.put({'level' : 'debug', 'message' : message})
    return flags[1]['setup_ready']

# creating an event handler for when getting a message when setup ready
def setup_ready_event_handler():
    #print('ctrl: im waiting for setup ready')
    message = 'ctrl: im waiting for setup ready'
    queue.put({'level' : 'info', 'message' : message})
    setup_ready_lisenter = Process(target=rmq_handler.wait_for_message, args=('setup_ready',flags,queue,))

    setup_ready_lisenter.start()
    wait(lambda: is_setup_ready(), timeout_seconds=120, waiting_for="setup to be ready")
    time.sleep(3)
    setup_ready_lisenter.terminate()

def run_test():
    json_document_result_example = '''{
	    "name": "Check if the signal Peer_Offer includes data item Peer_Type",
	    "result": "Pass/Fail"
    }
    '''
    uid = mdb_handler.insert_document('Test Results', loads(json_document_result_example))
    return uid

def run_tests(num_of_tests):
    #print('ctrl: im running the tests one by one')
    message = 'ctrl: im running the tests one by one'
    queue.put({'level' : 'info', 'message' : message})
    for index in range(num_of_tests):
        test_uid = run_test()
        rmq_handler.send('', 'results', str(test_uid))
        time.sleep(1)
    
def all_results_ready():
    rmq_handler.send('', 'all_results_ready', '')
    time.sleep(3)
    link = rmq_handler.request_pdf()
    time.sleep(3)
    rmq_handler.send('', 'pdf_ready', link)
    

def controller_flow():
    make_test_list()
    setup_ready_event_handler()
    time.sleep(1)
    run_tests(3)
    time.sleep(3)
    all_results_ready()
    # the next line ends the process listener
    queue.put_nowait(None)

def main():
    flags[1] = {'setup_ready' : False}
    
    listener = Process(target=controller_listener_process,
                                       args=(queue, controller_listener_configurer))
    listener.start()

    controller_flow()


if __name__ == '__main__':
    main()