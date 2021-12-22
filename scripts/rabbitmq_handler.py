#!/usr/local/bin/python

# for rabbitmq use
import pika

# for access of environment variables
import os

import logging
import uuid

import sys

import time

import ctypes

import functools

from multiprocessing import Value

class RabbitmqHandler:
    def __init__(self):
        self.queue_names = os.getenv('QUEUE_NAMES').split(',')
        #self.queue_names = ['updates', 'results', 'pdfs']

        self.rabbitmq_host = os.getenv('RMQ_HOST')
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(self.rabbitmq_host))
        self.channel = self.connection.channel()
        
        # declaring the queues
        for queue_name in self.queue_names:
            result = self.channel.queue_declare(queue=queue_name)
            if queue_name == 'pdfs':
                self.callback_queue_pdfs = result.method.queue
                self.channel.basic_consume(queue=self.callback_queue_pdfs, on_message_callback=self.on_response_pdf, auto_ack=True)


        # declaring state for when tests_list_ready
        self.tests_list_ready = Value(ctypes.c_bool,False)
        # declaring state for when device_ids_ready
        self.device_ids_ready = Value(ctypes.c_bool,True)
        # declaring state for when setup_ready
        self.setup_ready = Value(ctypes.c_bool,False)    
        # declaring state for when all_results_ready
        self.all_results_ready = Value(ctypes.c_bool,False)
        # declaring state for when pdf_ready
        self.pdf_ready = Value(ctypes.c_bool,False)
        
        
    def on_response_pdf(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    # send rpc message in order to collect a 'pdf ready' notification from the report generator
    def request_pdf(self):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='pdfs',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue_pdfs,
                correlation_id=self.corr_id),
            body='')
        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def send(self, msg_exchange, msg_routing_key, msg_body):
        self.channel.basic_publish(
            exchange=msg_exchange,
            routing_key=msg_routing_key,
            body=msg_body)

    def make_tests_list_ready(self, ch, method, properties, body, flags):
        print('rmq_handler: test list ready - %s' %body)
        sys.stdout.flush()
        time.sleep(1)
        # changing the specific flag's state
        temp_list = flags[1]
        temp_list['tests_list_ready'] = True
        flags[1] = temp_list

        print('tests_list_ready flag - %s' % flags[1]['tests_list_ready'])
        self.tests_list_ready = Value(ctypes.c_bool,True)
        #print(self.tests_list_ready)

    def make_device_ids_ready(self, ch, method, properties, body, flags):
        print('rmq_handler: device ids ready - %s' %body)
        sys.stdout.flush()
        time.sleep(1)
        # changing the specific flag's state
        temp_list = flags[1]
        temp_list['device_ids'] = True
        flags[1] = temp_list

        self.device_ids_ready = Value(ctypes.c_bool,True)

    def make_setup_ready(self, ch, method, properties, body, flags):
        print('rmq_handler: setup ready - %s' %body)
        sys.stdout.flush()
        time.sleep(1)
        # changing the specific flag's state
        temp_list = flags[1]
        temp_list['setup_ready'] = True
        flags[1] = temp_list

        self.setup_ready = Value(ctypes.c_bool,True)

    def print_result(self, ch, method, properties, body):
        print('rmq_handler: got result - %s' %body)
        sys.stdout.flush()

    def make_all_results_ready(self, ch, method, properties, body, flags):
        print('rmq_handler: all results ready - %s' %body)
        sys.stdout.flush()
        time.sleep(1)
        # changing the specific flag's state
        temp_list = flags[1]
        temp_list['all_results_ready'] = True
        flags[1] = temp_list

        self.all_results_ready = Value(ctypes.c_bool,True)

    def make_pdf_ready(self, ch, method, properties, body, flags):
        print('rmq_handler: pdf ready - %s' %body)
        sys.stdout.flush()
        time.sleep(1)
        # changing the specific flag's state
        temp_list = flags[1]
        temp_list['pdf_ready'] = True
        flags[1] = temp_list

        self.pdf_ready = Value(ctypes.c_bool,True)

    def wait_for_message(self, routing_key, flags):
        if routing_key == 'tests_list':
            self.channel.basic_consume(queue=routing_key,
                            auto_ack=True,
                            on_message_callback=lambda ch, method, properties, body: self.make_tests_list_ready(ch, method, properties, body, flags))

        if routing_key == 'setup_ready':
            self.channel.basic_consume(queue=routing_key,
                            auto_ack=True,
                            on_message_callback=lambda ch, method, properties, body: self.make_setup_ready(ch, method, properties, body, flags))

        if routing_key == 'device_ids':
            self.channel.basic_consume(queue=routing_key,
                            auto_ack=True,
                            on_message_callback=lambda ch, method, properties, body: self.make_device_ids_ready(ch, method, properties, body, flags))

        if routing_key == 'results':
            self.channel.basic_consume(queue=routing_key,
                            auto_ack=True,
                            on_message_callback=lambda ch, method, properties, body: self.print_result(ch, method, properties, body))

        if routing_key == 'all_results_ready':
            self.channel.basic_consume(queue=routing_key,
                            auto_ack=True,
                            on_message_callback=lambda ch, method, properties, body: self.make_all_results_ready(ch, method, properties, body, flags))

        if routing_key == 'pdf_ready':
            self.channel.basic_consume(queue=routing_key,
                            auto_ack=True,
                            on_message_callback=lambda ch, method, properties, body: self.make_pdf_ready(ch, method, properties, body, flags))
       
        self.channel.start_consuming()