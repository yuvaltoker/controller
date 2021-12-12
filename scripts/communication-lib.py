#!/usr/local/bin/python

# for rabbitmq use
import pika

# for access of environment variables
import os

import logging
import uuid

class rabbitmq_handler(object):
    def __init__(self):
        self.queue_names = ['updates', 'results', 'pdfs']

        self.rabbitmq_host = os.getenv('RMQ_HOST')
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(self.rabbitmq_host))
        self.channel = self.connection.channel()

        # declaring the queues
        for queue_name in self.queue_names:
            result = self.channel.queue_declare(queue=queue_name, exclusive=True)
            if queue_name == 'pdfs':
                self.callback_queue = result.method.queue
                self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response_pdf, auto_ack=True)
        
    def on_response_pdf(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def send(self, msg_exchange, msg_routing_key):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange=msg_exchange,
            routing_key=msg_routing_key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body="WORK!")
        while self.response is None:
            self.connection.process_data_events()
        return self.response

def _setup_logger():    
        logger=logging.getLogger("controller")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.DEBUG)
        return logger