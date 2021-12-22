# for event handling
from waiting import wait

# for background waiting function, use multiproccecing
from multiprocessing import Process, Value, Manager

# for using a shared memory variables
import ctypes

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


def can_i_start_running():
    # tests_list_ready = flags['tests_list_ready']
    # device_ids_ready = rmq_handler.device_ids_ready.value
    print('app: tests_list_ready flag - {0}'.format(flags[1]['tests_list_ready']))
    return flags[1]['tests_list_ready']

def are_all_results_ready():
    return flags[1]['all_results_ready']

def is_pdf_ready():
    print('app: pdf_ready flag - {0}'.format(flags[1]['pdf_ready']))
    return flags[1]['pdf_ready']

def create_setup():
    print('app: creating setup...')
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

    print('app: sending set up ready')
    rmq_handler.send('', 'setup_ready', str(uid))   

# creating an event handler for when getting a message when test list ready and got devices
def before_running_event_handler():
    print('app: im waiting for test list and devices ready')
    tests_list_ready_listener = Process(target=rmq_handler.wait_for_message, args=('tests_list', flags,))

    # device_ids__ready_listener = Process(target=rmq_handler.wait_for_message, args=('device_ids', flags,))

    tests_list_ready_listener.start()
    # device_ids__ready_listener.start()
    wait(lambda: can_i_start_running(), timeout_seconds=120, waiting_for="test list and device list to be ready")
    time.sleep(3)
    tests_list_ready_listener.terminate()
    # device_ids__ready_listener.terminate()

def results_event_handler():
    print('app: im waiting for results ready')
    results_listener = Process(target=rmq_handler.wait_for_message, args=('results', flags,))
    all_results_ready_listener = Process(target=rmq_handler.wait_for_message, args=('all_results_ready', flags,))

    results_listener.start()
    all_results_ready_listener.start()
    wait(lambda: are_all_results_ready(), timeout_seconds=120, waiting_for="all results to be ready")
    time.sleep(3)
    results_listener.terminate()
    all_results_ready_listener.terminate()

def getting_pdf_event_handler():
    print('app: im waiting for pdf ready')
    pdf_ready_listener = Process(target=rmq_handler.wait_for_message, args=('pdf_ready', flags,))

    pdf_ready_listener.start()
    wait(lambda: is_pdf_ready(), timeout_seconds=120, waiting_for="pdf to be ready")
    time.sleep(3)
    pdf_ready_listener.terminate()


def app_flow():
    # variables to handle event proccess
    # tests_list_ready = Value(ctypes.c_bool,False)
    # device_ids_ready = Value(ctypes.c_bool,False)
    # all_results_ready = Value(ctypes.c_bool,False)
    # pdf_ready = Value(ctypes.c_bool,False)

    # a dictionary stores the states that handles the events
    #flags = manager.dict({'tests_list_ready' : False, 'device_ids_ready' : False, 'all_results_ready' : False, 'pdf_ready' : False})

    # try to work with manager dictionary as https://stackoverflow.com/questions/32822013/python-share-values say.
    # maybe the dictionary should be in rabbitmq instance, thus should be accessible via app-test.

    before_running_event_handler()
    create_setup()
    results_event_handler()
    getting_pdf_event_handler()
    print('app: controller thanks for everything, you may need to think of another name though')

if __name__ == '__main__':
    flags[1] = {'tests_list_ready' : False, 'device_ids_ready' : False, 'all_results_ready' : False, 'pdf_ready' : False}
    app_flow()
