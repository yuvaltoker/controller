import pika
import os

# for event handling
from waiting import wait

connection = pika.BlockingConnection(
    pika.ConnectionParameters(os.getenv('RMQ_HOST')))

channel = connection.channel()

channel.queue_declare(queue='updates')
channel.queue_declare(queue='setup_ready')

# variables to handle event proccess
test_list_ready = False
all_results_ready = False

def is_variable_ready(var):
    return var

def send(msg_exchange, msg_routing_key, msg_body):
    channel.basic_publish(
            exchange=msg_exchange,
            routing_key=msg_routing_key,
            body=msg_body)

def make_test_list_ready(ch, method, properties, body):
    if body == 'Test List Ready':
        test_list_ready = True


def wait_for_test_list(routing_key):
    channel.basic_consume(queue=routing_key,
                        auto_ack=True,
                        on_message_callback=make_test_list_ready)
    channel.start_consuming()

def handle_results(ch, method, properties, body):
    print(body)
    if body == 'All Results Ready':
        all_results_ready = True

def wait_for_results(routing_key):
    # waiting for results
    channel.basic_consume(queue=routing_key,
                        auto_ack=True,
                        on_message_callback=handle_results)
    channel.start_consuming()


if __name__ == '__main__':
    wait_for_test_list('updates')
    wait(lambda: is_variable_ready(test_list_ready), timeout_seconds=120, waiting_for="test list to be ready")
    send('', 'setup_ready', 'Setup Ready')
    wait_for_results('updates')
    wait(lambda: is_variable_ready(all_results_ready), timeout_seconds=120, waiting_for="all results to be ready")
    print('controller thanks for everything, you may need to think of another name though')
