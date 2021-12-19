# for event handling
from waiting import wait

# for background waiting function, use multiproccecing
from multiprocessing import Process,Value

# for using a shared memory variables
import ctypes

# for easy use of rabbitmq
from rabbitmq_handler import RabbitmqHandler
# for easy read/write on mongodb
from mongodb_handler import MongodbHandler

from json import dumps, loads


rmq_handler = RabbitmqHandler()
mdb_handler = MongodbHandler()

# variables to handle event proccess
test_list_ready = Value(ctypes.c_bool,False)
device_ids_ready = Value(ctypes.c_bool,False)
all_results_ready = Value(ctypes.c_bool,False)
pdf_ready = Value(ctypes.c_bool,False)


def can_i_start_running():
    test_list_ready = Value(ctypes.c_bool,rmq_handler.test_list_ready)
    device_ids_ready = Value(ctypes.c_bool,rmq_handler.device_ids_ready)
    return test_list_ready and device_ids_ready

def are_all_results_ready():
    all_results_ready = Value(ctypes.c_bool,rmq_handler.all_results_ready)
    return all_results_ready

def is_pdf_ready():
    pdf_ready = Value(ctypes.c_bool,rmq_handler.pdf_ready)
    return pdf_ready

def create_setup():
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
    uid = mdb_handler.insert_document('Test Results', loads(json_document_setup_example))

    print('app: sending set up ready')
    rmq_handler.send('', 'setup_ready', uid)
    return uid    

# creating an event handler for when getting a message when test list ready and got devices
def before_running_event_handler():
    print('app: im waiting for test list and devices ready')
    test_list_ready_listener = Process(target=rmq_handler.wait_for_message, args=('test_list_ready',))
    print('app: after creating the wait_for_message thread for test list')

    # device_ids__ready_listener = Process(target=rmq_handler.wait_for_message, args=('device_ids',))
    # print('app: after creating the wait_for_message thread for device ids')

    test_list_ready_listener.start()
    # device_ids__ready_listener.start()
    print('app: after starting before running listeners (test_list and device_ids)')
    wait(lambda: can_i_start_running(), timeout_seconds=120, waiting_for="test list and device list to be ready")
    test_list_ready_listener.terminate()
    # device_ids__ready_listener.terminate()

def results_event_handler():
    print('app: im waiting for results ready')
    results_listener = Process(target=rmq_handler.wait_for_message, args=('results',))
    print('app: after creating the wait_for_message thread for results')

    all_results_ready_listener = Process(target=rmq_handler.wait_for_message, args=('all_results_ready',))
    print('app: after creating the wait_for_message thread for all results')

    results_listener.start()
    all_results_ready_listener.start()
    print('app: after starting results listeners (results and all_results_ready)')
    wait(lambda: are_all_results_ready(), timeout_seconds=120, waiting_for="all results to be ready")
    results_listener.terminate()
    all_results_ready_listener.terminate()

def getting_pdf_event_handler():
    print('app: im waiting for pdf ready')
    pdf_ready_listener = Process(target=rmq_handler.wait_for_message, args=('pdf_ready',))
    print('app: after creating the wait_for_message thread for pdf_ready')

    pdf_ready_listener.start()
    print('app: after starting pdf_ready listener')
    wait(lambda: is_pdf_ready(), timeout_seconds=120, waiting_for="pdf to be ready")
    pdf_ready_listener.terminate()


def app_flow():
    before_running_event_handler()
    create_setup()
    results_event_handler()
    getting_pdf_event_handler()
    print('app: controller thanks for everything, you may need to think of another name though')

if __name__ == '__main__':
    app_flow()
