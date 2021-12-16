from pprint import PrettyPrinter
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

# for background waiting function, use multiproccecing
from multiprocessing import Process,Value

# for using a shared memory variables
import ctypes

rmq_handler = RabbitmqHandler()

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
    print('ctrl: test list ready')

def test_list_ready():
    rmq_handler.send('', 'updates', 'Test List Ready')

def is_setup_ready():
    setup_ready = Value(ctypes.c_bool,rmq_handler.setup_ready)
    return setup_ready

# creating an event handler for when getting a message when setup ready
def setup_ready_event_handler():
    print('ctrl: im waiting for setup ready')
    #wait_thread = Thread(target=rmq_handler.wait_for_message, args=('setup_ready',))
    wait_thread = multiprocessing.Process(target=rmq_handler.wait_for_message, args=('setup_ready',))
    print('ctrl: after creating the wait_for_message thread')
    wait_thread.start()

    print('ctrl: after starting the wait_for_message thread')
    wait(lambda: is_setup_ready(), timeout_seconds=120, waiting_for="setup to be ready")
    wait_thread.terminate()

def run_test(test_NO):
    return 'Test NO.%d' % test_NO

def run_tests(num_of_tests):
    print('ctrl: im running the tests one by one')
    for index in range(num_of_tests):
        test_uid = run_test(index)
        rmq_handler.send('', 'results', test_uid)
    
def all_results_ready():
    rmq_handler.send('', 'updates', 'All Results Ready')
    link = rmq_handler.request_pdf()
    rmq_handler.send('', 'updates', link)

def controller_flow():
    make_test_list()
    test_list_ready()
    setup_ready_event_handler()
    run_tests(3)
    all_results_ready()


if __name__ == '__main__':
    controller_flow()