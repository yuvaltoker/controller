from rabbitmq_handler import Rabbitmq_handler

def rabbitmq_send_msg_example():
    print('im the rabbitmq example')
    rmq = Rabbitmq_handler()
    print(rmq.send_rpc('', 'pdfs', 'im the controller'))

def mongodb_tests():
    print('im the mongodb example')

if __name__ == '__main__':
    mongodb_tests()