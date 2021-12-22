# for easy use of rabbitmq
from rabbitmq_handler import RabbitmqHandler
# for easy read/write on mongodb
from mongodb_handler import MongodbHandler

from json import dumps, loads
# for event handling
from waiting import wait

# for threading function
#from threading import Thread
import multiprocessing

# for more convenient storing dictionaries
from pandas import DataFrame

# for background waiting function, use multiproccessing
from multiprocessing import Process,Value, Manager

# for using a shared memory variables
import ctypes

# for delay use
import time

rmq_handler = RabbitmqHandler()
mdb_handler = MongodbHandler()
manager = Manager()
flags = manager.dict()

# variables to handle event proccess
setup_ready = Value(ctypes.c_bool,False)

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
    print('ctrl: test list in proggress...')
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
    print('ctrl: test list ready')
    rmq_handler.send('', 'tests_list', str(uid))

def is_setup_ready():
    # setup_ready = rmq_handler.setup_ready.value
    print('ctrl: setup_ready flag - {0}'.format(flags[1]['setup_ready']))
    return flags[1]['setup_ready']

# creating an event handler for when getting a message when setup ready
def setup_ready_event_handler():
    print('ctrl: im waiting for setup ready')
    setup_ready_lisenter = Process(target=rmq_handler.wait_for_message, args=('setup_ready',flags,))

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
    print('ctrl: im running the tests one by one')
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


if __name__ == '__main__':
    flags[1] = {'setup_ready' : False}
    controller_flow()