import pika
import os

# for easy read/write on mongodb
from mongodb_handler import MongodbHandler

connection = pika.BlockingConnection(
    pika.ConnectionParameters(os.getenv('RMQ_HOST')))

channel = connection.channel()

channel.queue_declare(queue='pdfs')

def on_request(ch, method, props, body):
    response = 'PDF Ready'
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=response)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='pdfs', on_message_callback=on_request)

print('report: waiting for pdf request')
channel.start_consuming()
print('report: after consume')