import pika
import os

connection = pika.BlockingConnection(
    pika.ConnectionParameters(os.getenv('RMQ_HOST')))

channel = connection.channel()

channel.queue_declare(queue='pdfs')

def on_request(ch, method, props, body):
    response = 'im the response'
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=response)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='pdfs', on_message_callback=on_request)

print(" [x] Awaiting RPC requests")
channel.start_consuming()