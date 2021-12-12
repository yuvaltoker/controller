from rabbitmq_handler import Rabbitmq_handler

def rabbitmq_send_msg_example():
    print('im the controller')
    rmq = Rabbitmq_handler()
    print(rmq.send_rpc('', 'pdfs', 'im the controller'))


if __name__ == '__main__':
    control_the_world()