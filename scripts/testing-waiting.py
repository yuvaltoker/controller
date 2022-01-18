# for event handling
from waiting import wait
import time

import pika
import os

from testing_class import Testing

import multiprocessing

setup = False

def is_setup_ready():
    return testing.setup_ready
    
def running_fun(var):
    while True:
        print(var)
        time.sleep(3)

def wait_for_results(routing_key):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(os.getenv('RMQ_HOST')))

    channel = connection.channel()

    channel.queue_declare(queue='updates')
    # waiting for results
    print('app: waiting for results ready (in wait functin)')
    channel.basic_consume(queue=routing_key,
                        auto_ack=True,
                        on_message_callback=running_fun)
    channel.start_consuming()

def main():
    # testing = Testing()
    # wait(lambda: is_setup_ready(), timeout_seconds=120, waiting_for="setup to be ready")
    # print('yep, im all fine')

    #wait_thread = Thread(target=wait_for_results,args=('updates',))

    #wait_thread = multiprocessing.Process(target=running_fun, args=('yes, im being printed rn',))
    wait_thread = multiprocessing.Process(target=wait_for_results, args=('updates',))
    wait_thread.start()

    while True:
        print('22222222222222222')
        time.sleep(3)

if __name__ == '__main__':
    main()
