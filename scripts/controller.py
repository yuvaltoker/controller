from pprint import PrettyPrinter
from rabbitmq_handler import RabbitmqHandler
from mongodb_handler import MongodbHandler
from json import dumps, loads
# for event handling (from https://stackoverflow.com/questions/6190468/how-to-trigger-function-on-value-change)
from tkinter import *
# for more convenient storing dictionaries
from pandas import DataFrame

rmq_handler = RabbitmqHandler()

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
    print('test list in proggress...')
    print('test list ready')

def test_list_ready():
    rmq_handler.send('', 'updates', 'Test List Ready')

def waiting_for_setup_ready():
    print('im waiting for setup ready')

def run_test():
    return 'uid of test'

def run_tests():
    print('im running the tests one by one')
    test_uid = run_test()
    rmq_handler('', 'results', test_uid)

def all_results_ready():
    rmq_handler.send('', 'updates', 'All Results Ready')
    link = rmq_handler.request_pdf()
    rmq_handler.send('', 'updates', link)

def controller_flow():
    make_test_list()
    test_list_ready()
    waiting_for_setup_ready()
    run_tests()
    all_results_ready()




if __name__ == '__main__':
    rabbitmq_send_msg_example()