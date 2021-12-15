import pika
import os

# for event handling
from waiting import wait

# for threading waiting function
#from threading import Thread
from multiprocessing import Process, Manager, Value

manager = Manager()


connection = pika.BlockingConnection(
    pika.ConnectionParameters(os.getenv('RMQ_HOST')))

channel = connection.channel()

channel.queue_declare(queue='updates')
channel.queue_declare(queue='setup_ready')

# variables to handle event proccess
test_list_ready = Value(ctypes.c_bool,False)
all_results_ready = Value(ctypes.c_bool,False)

def is_variable_ready(var):
    return var

def send(msg_exchange, msg_routing_key, msg_body):
    channel.basic_publish(
            exchange=msg_exchange,
            routing_key=msg_routing_key,
            body=msg_body)

def make_test_list_ready(ch, method, properties, body):
    print('app: %s' % body)
    if body == 'Test List Ready':
        print('app: %s' % body)
        global test_list_ready
        test_list_ready = Value(ctypes.c_bool,False)
        print('app: test_list_ready = %s'% (str(test_list_ready)))


def wait_for_test_list(routing_key):
    print('app: waiting for test list ready (in wait functin)')
    channel.basic_consume(queue=routing_key,
                        auto_ack=True,
                        on_message_callback=make_test_list_ready)
    channel.start_consuming()

def handle_results(ch, method, properties, body):
    print('app: %s' % body)
    if body == 'All Results Ready':
        global all_results_ready
        all_results_ready = Value(ctypes.c_bool,False)

def wait_for_results(routing_key):
    # waiting for results
    print('app: waiting for results ready (in wait functin)')
    channel.basic_consume(queue=routing_key,
                        auto_ack=True,
                        on_message_callback=handle_results)
    channel.start_consuming()

def main():
    print('app: waiting for test list ready')

    #wait_thread = Thread(target=wait_for_test_list,args=('updates',))
    wait_thread = Process(target=wait_for_test_list, args=('updates',))
    wait_thread.start()
    print('app: waiting for test list ready (after wait functin)')

    wait(lambda: is_variable_ready(test_list_ready), timeout_seconds=120, waiting_for="test list to be ready")
    wait_thread.terminate()
    
    print('app: sending set up ready')
    send('', 'setup_ready', 'Setup Ready')
    
    #wait_thread = Thread(target=wait_for_results,args=('updates',))
    wait_thread = Process(target=wait_for_results, args=('updates',))
    wait_thread.start()

    wait(lambda: is_variable_ready(all_results_ready), timeout_seconds=120, waiting_for="all results to be ready")
    wait_thread.terminate()
    print('app: controller thanks for everything, you may need to think of another name though')

if __name__ == '__main__':
    main()
